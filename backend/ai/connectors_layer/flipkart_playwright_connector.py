"""
Flipkart Playwright Connector
Live browser automation of Flipkart Seller Hub: session management,
products/orders/inventory/shipments, sales & business metrics.

STATUS / WHAT'S VERIFIED VS ASSUMED
-----------------------------------------------------------------------
The *mechanics* below (session restore/refresh, one shared browser,
retry-on-transient-failure, guaranteed context/page cleanup, structured
logging) are real and testable without a live seller account.

The CSS selectors in FlipkartSelectors and the "#dashboard / #orders /
#inventory" URL fragments are NOT verified against the real Flipkart
Seller Hub — nobody on this project has a live logged-in session to
confirm them against. They're reasonable guesses at a typical seller
panel's shape, structured so that if you or QA discover the real
selectors, FlipkartSelectors is the ONLY place that needs editing —
nothing in the fetch_*/update_* methods themselves.

BROWSER LIFECYCLE — AN HONEST LIMITATION
-----------------------------------------------------------------------
The public facade functions at the bottom of this file (fetch_orders,
fetch_inventory, ...) are synchronous, and each currently wraps its
work in its own `asyncio.run(...)` call — that's the calling
convention the rest of the codebase (marketplace_connector.py, tools,
agents) already expects, and this file does not change that.

`asyncio.run()` opens a brand-new event loop and tears it down when
the call returns. A Playwright Browser object is bound to the loop
that launched it, so a browser CANNOT actually survive from one
`fetch_orders(...)` call to the next `fetch_inventory(...)` call under
this calling convention — there is no event loop left afterward for it
to live in.

An earlier version of this file tried to work around that with a
class-level BrowserManager singleton caching one Browser/Playwright
pair across calls. Under real concurrent FastAPI traffic (dashboard,
inventory, orders, and analytics all firing at once — each on its own
OS thread via `asyncio.to_thread`, each running its own independent
`asyncio.run()` loop) that singleton was a genuine correctness bug,
not just a noisy log line: whichever request's `get_browser()` call
observed the cached handle second would overwrite the class attribute
with its OWN browser, so the FIRST request's `shutdown()` — reading
that same class attribute at the end of ITS OWN call — could end up
closing a completely different, still-in-flight request's browser
(intermittent "Target closed" failures under load), while the first
request's own browser/Playwright process was never closed by anyone
(a leak). Ownership was never actually guaranteed to the code that
launched it.

The fix: no shared state at all. Every top-level facade call launches
its own Playwright + Browser (see `_launch_browser` / `_close_browser`
below), uses it exclusively for the duration of that one call, and
closes it itself in a `finally` block. Nothing is cached at module or
class level, so there is nothing for a concurrent call to clobber or
have clobbered. `_fetch_business_metrics` still reuses ONE browser
across its two sub-fetches (sales + inventory) — but by passing that
browser as an explicit argument through the call, not by caching it
anywhere.
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)

from .exceptions import (
    NavigationError,
    ParsingError,
    RateLimitError,
    SelectorError,
    SessionExpiredError,
)

logger = logging.getLogger(__name__)

print("=" * 80)
print("LOADED FILE:", __file__)
print("=" * 80)

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Task 10 — Debug instrumentation. Evidence-collection only: screenshots,
# full HTML, URL, title, and table-structure counts at key stages, so a
# zero-rows result can be diagnosed (wrong URL? never logged in? table
# absent? table present but TABLE_ROW doesn't match it?) without guessing.
# Does NOT touch FlipkartSelectors, does NOT change scraping behavior.
# ---------------------------------------------------------------------------
DEBUG_DIR = Path(__file__).resolve().parents[3] / "debug"


# ---------------------------------------------------------------------------
# Task 5 (revised) — URL/route configuration, mirroring meesho_connector.py's
# module-level BASE_URL/ROUTES pattern instead of baking URLs into class
# attributes computed once at class-definition time.
#
# This split matters for one concrete reason: FlipkartSelectors used to
# compute DASHBOARD_URL/LOGIN_URL/etc. as class attributes evaluated the
# moment this module was imported (`DASHBOARD_URL = f"{BASE_URL}/..."`
# inside the class body). Once computed, that string never changed again
# -- there was no way for a test harness (or, eventually, real per-
# environment config) to point the connector at anything other than the
# literal production seller.flipkart.com, even by reassigning an
# attribute on the class or module afterward. meesho_connector.py never
# had this problem: its fetch_*/​_login functions look up `ROUTES["..."]`
# fresh, as a plain module-global name, on every call -- so replacing the
# module's `ROUTES` dict wholesale (`mod.ROUTES = {...}`, exactly what
# tests/test_playwright_connectors.py's shared fixture does for both
# connectors) actually takes effect, because every call re-reads the
# current dict instead of a value frozen at import time.
#
# BASE_URL/ROUTES below follow the exact same shape so the same fixture
# now works for Flipkart too. FlipkartSelectors keeps ONLY DOM selectors
# (CSS/text hooks), which have nothing to do with which host they're
# queried against and don't need this treatment.
#
# UNVERIFIED - Requires live Flipkart Seller account
# Every selector and URL fragment below is a best-effort guess at the
# real Seller Hub's DOM/routing and has not been confirmed against a
# live logged-in session -- that remains true and unchanged by this
# refactor, which only makes the values swappable, not more accurate.
# Left unchanged rather than guessed further -- do not fabricate
# validation.
# ---------------------------------------------------------------------------
BASE_URL = "https://seller.flipkart.com"

ROUTES = {
    "login": f"{BASE_URL}/login",
    "dashboard": f"{BASE_URL}/index.html#dashboard",
    "catalog": f"{BASE_URL}/index.html#listings",
    "orders": f"{BASE_URL}/index.html#orders",
    "shipments": f"{BASE_URL}/index.html#shipments",
    "inventory": f"{BASE_URL}/index.html#inventory",
    "analytics_sales": f"{BASE_URL}/index.html#analytics/sales",
}


def _route(key: str, default_suffix: str) -> str:
    """
    Looks up ROUTES[key] fresh on every call -- both ROUTES and BASE_URL
    are read as module globals here, not captured once at import time,
    so reassigning either (`flipkart_playwright_connector.BASE_URL = ...`
    / `...ROUTES = {...}`) takes effect on the very next call. This is
    what tests/test_playwright_connectors.py's shared fixture relies on,
    and what meesho_connector.py already does implicitly by reading
    `ROUTES[...]` as a bare module global inside its functions.

    Falls back to BASE_URL + default_suffix (also read fresh) when `key`
    isn't present -- the shared fixture only overrides
    {"login", "catalog", "orders", "shipments", "inventory"}, not every
    route this connector uses (e.g. "dashboard", "analytics_sales"), so
    a plain `ROUTES[key]` would KeyError for those under test. Falling
    back to BASE_URL keeps such calls following BASE_URL to the mock
    server too, instead of silently reverting to production the moment
    a route key is absent.
    """
    return ROUTES.get(key, f"{BASE_URL}{default_suffix}")


class FlipkartSelectors:
    # UNVERIFIED - current Seller Hub UI (see _login()'s docstring).
    # /login as a directly-navigable URL was confirmed obsolete (bare
    # HTTP 404 -- see debug_capture_navigation's findings) and the real
    # flow now starts at the homepage: click an entry point, a modal
    # appears with a username/phone screen, "Next", then a password
    # screen. Every one of these five selectors is a best-effort guess
    # at that flow's DOM, same unverified status as the rest of this
    # class -- debug_capture()/debug_inspect_login_page() calls at each
    # stage in _login() exist specifically so a wrong guess here is
    # pinpointed by stage, not by re-guessing blindly.
    # UNVERIFIED - current Seller Hub UI. Kept as a tuple of separate
    # candidates rather than one comma-joined string: `text=/.../i` and
    # plain CSS (`a:has-text(...)`) are DIFFERENT Playwright selector
    # engines, and joining different engines with commas inside one
    # selector string is invalid syntax (a comma-joined list of plain-CSS
    # branches, like TABLE_ROW/PAGINATION_NEXT below, IS one valid
    # selector -- it's only mixing engines that breaks).
    # `_click_first_available()` tries each of these candidates in turn.
    LOGIN_ENTRY_BUTTON_CANDIDATES = (
        "button:has-text('Login')",
        "text=/^login$/i",
        "a:has-text('Login')",
    )

    # CONFIRMED by the login discovery run -- read directly off the
    # rendered page, not guessed. The login form (username, password,
    # Next/Login buttons) sits directly on the page after the entry
    # click; no modal, no iframe, no Shadow DOM was present, so there
    # is no LOGIN_MODAL selector here anymore.
    LOGIN_USERNAME_INPUT = 'input[name="username"]'
    LOGIN_PASSWORD_INPUT = 'input[name="password"]'
    LOGIN_NEXT_BUTTON_TEXT = "Next"
    LOGIN_SUBMIT_BUTTON_TEXT = "Login"

    TABLE_ROW = "table tbody tr"
    TABLE_CELL = "td"
    # UNVERIFIED - Requires live Flipkart Seller account. The
    # data-testid variant is appended (not substituted) so production's
    # guessed selectors are untouched -- it's what lets this same
    # selector also match tests/mock_panel_server.py's pagination link
    # (`<a data-testid="pagination-next">`), which the meesho selector
    # for the identical mock already matches.
    PAGINATION_NEXT = "a.next, button.next, [aria-label='Next'], .pagination-next, [data-testid='pagination-next']"

    # -- Row-extraction normalization -----------------------------------
    # These four target tests/mock_panel_server.py's data-testid rows --
    # the same DOM shape meesho_connector.py's SELECTORS already read.
    # Only "order_row" is actually served by the mock today; the other
    # three are here so fetch_products/fetch_inventory/fetch_shipments
    # go through the same table-or-data-testid normalization rather than
    # three of the four fetch_* methods being special-cased. Genuinely
    # unverified against production, same caveat as everything else in
    # this class.
    ORDER_ROW_TESTID = "[data-testid='order-row']"
    PRODUCT_ROW_TESTID = "[data-testid='product-row']"
    INVENTORY_ROW_TESTID = "[data-testid='inventory-row']"
    SHIPMENT_ROW_TESTID = "[data-testid='shipment-row']"

    # Matches tests/mock_panel_server.py's rate-limited response body
    # exactly (case-insensitive text-content selector engine, same
    # pattern meesho_connector.py's SELECTORS["rate_limit_banner"] uses
    # against the same mock).
    RATE_LIMIT_BANNER = "text=/too many requests/i"

    SALES_GROSS_REVENUE = ".gross-revenue-val"
    SALES_TOTAL_ORDERS = ".total-orders-val"
    SALES_UNITS_SOLD = ".units-sold-val"
    SALES_CANCELLED_ORDERS = ".cancelled-orders-val"
    SALES_RETURNED_ORDERS = ".returned-orders-val"
    SALES_GROWTH = ".sales-growth-val"

    INVENTORY_ACTIVE_LISTINGS = ".active-listings-count"
    INVENTORY_LOW_STOCK = ".low-stock-count"

    INVENTORY_QTY_INPUT = "input[type='number']"
    INVENTORY_SAVE_BUTTON = "button[type='submit'], button.save"


# ---------------------------------------------------------------------------
# Task 2 — Browser lifecycle. No class, no singleton, no cache, no lock.
#
# A Playwright + Browser pair is launched fresh for exactly one top-level
# facade call (see `_run_and_cleanup` and the facade functions at the
# bottom of this file) and closed by that same call before it returns.
# The pair is passed down explicitly as a `browser` argument to every
# `_fetch_*`/`_update_*` method that needs it -- it is never stored on
# `self`, on a class attribute, or anywhere else that a concurrent call
# (running on its own OS thread / its own `asyncio.run()` loop -- see the
# module docstring) could read or overwrite. There is nothing shared, so
# there is nothing to lock and nothing to race on.
#
# `_fetch_business_metrics` still reuses ONE browser across its two
# sub-fetches (`_fetch_sales_metrics` + `_fetch_inventory_metrics`) --
# it just does that by passing the same `browser` object into both calls,
# not by caching it anywhere.
# ---------------------------------------------------------------------------
async def _launch_browser() -> "tuple":
    """
    Launches a Playwright driver + headless Chromium instance, both
    owned exclusively by the caller from this point on. No caching:
    the caller is responsible for closing both (see `_close_browser`)
    before its `asyncio.run()` call returns.
    """
    logger.debug("flipkart_connector: launching browser")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    logger.debug("flipkart_connector: browser launched")
    return playwright, browser


async def _close_browser(playwright, browser: Optional[Browser]) -> None:
    """
    Closes exactly the Playwright/Browser pair this same call launched
    via `_launch_browser`. Never touches any other call's browser --
    there is no shared state left for it to reach into. Safe to call
    even if launch never completed (e.g. `playwright` is set but
    `browser` launch raised).
    """
    if browser is not None:
        try:
            await browser.close()
            logger.debug("flipkart_connector: browser closed")
        except Exception:
            logger.warning(
                "flipkart_connector: browser handle failed to close cleanly."
            )
    if playwright is not None:
        try:
            await playwright.stop()
            logger.debug("flipkart_connector: playwright stopped")
        except Exception:
            logger.warning(
                "flipkart_connector: playwright handle failed to stop cleanly."
            )


# ---------------------------------------------------------------------------
# Task 3 — Retry framework. Retries ONLY transient failures (timeouts,
# navigation errors) with exponential backoff + jitter. Auth failures,
# missing selectors, and parsing failures are never retried — running
# the exact same broken assumption again produces the exact same result.
# ---------------------------------------------------------------------------
_RETRYABLE_EXCEPTIONS = (PlaywrightTimeoutError, NavigationError)


async def _with_retries(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    tool: str = "unknown",
) -> T:
    last_exc: Optional[Exception] = None
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except _RETRYABLE_EXCEPTIONS as exc:
            last_exc = exc
            if attempt == attempts:
                break
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
            logger.warning(
                "flipkart.%s transient failure (attempt %d/%d): %s -- retrying in %.2fs",
                tool, attempt, attempts, exc, delay,
            )
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise NavigationError(f"Flipkart '{tool}' failed after {attempts} attempts: {last_exc}") from last_exc


# ---------------------------------------------------------------------------
# Task 9 — Structured logging. Every connector call logs seller_id,
# platform, tool, duration_ms, success/failure, and error type.
# NEVER logs passwords, cookies, or tokens.
# ---------------------------------------------------------------------------
def _log_call(tool: str, seller_id: str, start_time: float, success: bool, error: Optional[Exception] = None) -> None:
    duration_ms = round((time.monotonic() - start_time) * 1000, 1)
    if success:
        logger.info(
            "flipkart_call tool=%s seller_id=%s platform=flipkart duration_ms=%s success=true",
            tool, seller_id, duration_ms,
        )
    else:
        logger.error(
            "flipkart_call tool=%s seller_id=%s platform=flipkart duration_ms=%s success=false error_type=%s",
            tool, seller_id, duration_ms, type(error).__name__ if error else "Unknown",
        )


class FlipkartPlaywrightConnector:
    def __init__(self, credentials: Dict[str, Any]):
        self.seller_id = credentials.get("seller_id", "")
        self.username = credentials.get("username", "")
        self.password = credentials.get("password", "")
        self.base_url = BASE_URL
        # In-memory cookie cache, keyed by seller_id. Deliberately NOT a
        # separate SessionStore class/module -- this codebase's real
        # session_store.py owns MarketplaceSession construction from
        # env vars / a registered-credentials map, and doesn't persist
        # cookies at all today. This cache is this file's own concern:
        # "did we already log in once in this process," nothing more.
        # Lost on process restart, same as everything else in-memory
        # in this codebase until a real backend/DB owns it.
        self._cookie_cache: "dict[str, list]" = _COOKIE_CACHE
        # Debug-instrumentation-only state (see _debug_capture /
        # _debug_table_diagnostics below). A connector instance is
        # created fresh per top-level facade call (see `_connector()`
        # near the bottom of this file), so this id is naturally
        # scoped to one call -- it exists so concurrent calls (now
        # genuinely possible after the browser-ownership fix) don't
        # overwrite each other's debug artifacts on disk.
        self._debug_call_id = uuid.uuid4().hex[:8]
        self._debug_step = 0

    # -- Task 10: debug instrumentation (evidence collection only) -----

    async def debug_capture(self, page: Page, stage_name: str) -> None:
        print("=" * 80)
        print("DEBUG_CAPTURE CALLED")
        print("Stage:", stage_name)
        print("=" * 80)
        """
        Saves a full-page screenshot + complete HTML + logs URL/title
        for `page` at `stage_name`. Evidence only -- never touches
        FlipkartSelectors, never changes control flow.

        Files land in:
            debug/<seller_id>_<call_id>/NN_<stage_name>.png
            debug/<seller_id>_<call_id>/NN_<stage_name>.html

        The `<seller_id>_<call_id>` subfolder (not a flat
        `debug/NN_stage.png`) is deliberate: after the browser-ownership
        fix, multiple top-level calls can genuinely run at the same
        wall-clock moment on different threads. Flat, stage-only
        filenames would let one request's capture silently overwrite
        another's mid-write -- exactly the kind of cross-request
        clobbering that fix eliminated for browsers, so debug output
        shouldn't reintroduce it for evidence files.
        """
        self._debug_step += 1
        call_dir = DEBUG_DIR / f"{self.seller_id or 'unknown_seller'}_{self._debug_call_id}"
        try:
            call_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning("[FLIPKART DEBUG] could not create debug dir %s: %s", call_dir, exc)
            return

        stage_prefix = f"{self._debug_step:02d}_{stage_name}"
        screenshot_path = call_dir / f"{stage_prefix}.png"
        html_path = call_dir / f"{stage_prefix}.html"

        url = page.url
        try:
            title = await page.title()
        except PlaywrightError as exc:
            title = f"<title unavailable: {exc}>"

        try:
            await page.screenshot(path=str(screenshot_path), full_page=True)
        except PlaywrightError as exc:
            logger.warning("[FLIPKART DEBUG] stage=%s screenshot capture failed: %s", stage_name, exc)

        html_len = 0
        try:
            html = await page.content()
            html_path.write_text(html, encoding="utf-8")
            html_len = len(html)
        except (PlaywrightError, OSError) as exc:
            logger.warning("[FLIPKART DEBUG] stage=%s html capture failed: %s", stage_name, exc)

        logger.info("[FLIPKART DEBUG] stage=%s seller_id=%s URL: %s", stage_name, self.seller_id, url)
        logger.info("[FLIPKART DEBUG] stage=%s Title: %s", stage_name, title)
        logger.info("[FLIPKART DEBUG] stage=%s screenshot=%s", stage_name, screenshot_path)
        logger.info("[FLIPKART DEBUG] stage=%s html=%s (length=%d chars)", stage_name, html_path, html_len)

    async def debug_capture_navigation(self, page: Page, response) -> None:
        """
        Task 12 — navigation/response inspection. Runs immediately after
        the `page.goto(BASE_URL)` call in `_login()` (previously this
        ran after `page.goto(ROUTES["login"])`, before that endpoint
        was confirmed obsolete), using the Response object that goto()
        itself returns (no extra navigation, no extra request
        triggered).

        Reconstructs the redirect chain via Playwright's
        `request.redirected_from` linked list (each Request knows the
        Request that redirected to it, walking backwards to the very
        first request Playwright made) and logs, for the FINAL response
        and every intermediate hop: HTTP status, status text, and the
        response headers (content-type, server, location, and the full
        header set). Also logs the final response body so a genuine
        404/error page can be told apart from an anti-bot interstitial
        by size/content rather than by guessing.

        Evidence-collection only -- does not retry, does not change
        `wait_until`, does not touch FlipkartSelectors, does not attempt
        any bypass.
        """
        print("=" * 80)
        print("NAVIGATION / RESPONSE INSPECTION")

        if response is None:
            print("goto() returned no Response object at all (e.g. same-document "
                  "navigation, or navigation aborted before a response was received).")
            logger.warning("[FLIPKART NAV DEBUG] goto() returned None -- no response to inspect.")
            print("=" * 80)
            return

        # -- walk the redirect chain from the final request backwards ------
        chain: "list" = []
        current_request = response.request
        while current_request is not None:
            chain.append(current_request)
            current_request = current_request.redirected_from
        chain.reverse()  # chain[0] is the very first request; chain[-1] is final

        print(f"Redirect chain ({len(chain)} hop(s)):")
        for i, req in enumerate(chain):
            try:
                hop_response = await req.response()
            except PlaywrightError as exc:
                hop_response = None
                logger.warning("[FLIPKART NAV DEBUG] could not resolve response for hop %d: %s", i, exc)

            status = hop_response.status if hop_response else "<no response>"
            headers = await hop_response.all_headers() if hop_response else {}
            location = headers.get("location")

            arrow = "  " if i == 0 else "  -> "
            print(f"{arrow}[{i}] {req.method} {req.url}")
            print(f"      status: {status}")
            if location:
                print(f"      location header: {location}")
            logger.info(
                "[FLIPKART NAV DEBUG] hop=%d method=%s url=%s status=%s location=%s",
                i, req.method, req.url, status, location,
            )

        # -- final response detail ------------------------------------------
        final_headers = await response.all_headers()
        print("-- FINAL RESPONSE --")
        print("URL:", response.url)
        print("Status:", response.status, response.status_text)
        print("Content-Type:", final_headers.get("content-type"))
        print("Server:", final_headers.get("server"))
        print("Location:", final_headers.get("location"))
        print("All headers:", final_headers)
        logger.info(
            "[FLIPKART NAV DEBUG] final url=%s status=%s status_text=%s content_type=%s server=%s location=%s",
            response.url, response.status, response.status_text,
            final_headers.get("content-type"), final_headers.get("server"),
            final_headers.get("location"),
        )
        logger.info("[FLIPKART NAV DEBUG] final all_headers=%s", final_headers)

        try:
            body = await response.text()
        except PlaywrightError as exc:
            body = f"<body unavailable: {exc}>"
        print(f"Body ({len(body)} chars):")
        print(body)
        logger.info("[FLIPKART NAV DEBUG] final body (%d chars): %s", len(body), body)
        print("=" * 80)

    async def debug_inspect_login_page(self, page: Page) -> None:
        """
        Task 11 — one-shot login-page inspection. Now called during
        _login()'s discovery phase, once the post-click route has
        finished loading (networkidle + a fixed render-settle wait) --
        NOT after a login modal, since the entry-point click was
        confirmed to navigate to a full new route rather than reveal an
        in-place modal. BEFORE any `page.fill()`, so it captures
        precisely what Playwright sees before any new, unverified field
        selectors are relied on -- distinct from `debug_capture()`/
        `debug_table_diagnostics()`, which only ever run AFTER a login
        attempt (successful or not).

        Evidence-collection only. Does NOT touch FlipkartSelectors, does
        NOT guess at new selectors, does NOT change control flow.

        Saves:
            debug/<seller_id>_<call_id>/login_page.html
            debug/<seller_id>_<call_id>/login_page.png

        And logs (to both `logger` and stdout, matching this file's
        existing debug-print convention): current URL/title, counts of
        input/form/button/link/iframe elements, every <input>'s
        type/name/id/placeholder/autocomplete/aria-label, every
        <button>'s inner text, every <a>'s inner text and href, every
        frame's name/url, and any Shadow DOM hosts found on the page.
        """
        call_dir = DEBUG_DIR / f"{self.seller_id or 'unknown_seller'}_{self._debug_call_id}"
        try:
            call_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning("[FLIPKART LOGIN DEBUG] could not create debug dir %s: %s", call_dir, exc)
            return

        html_path = call_dir / "login_page.html"
        screenshot_path = call_dir / "login_page.png"

        url = page.url
        try:
            title = await page.title()
        except PlaywrightError as exc:
            title = f"<title unavailable: {exc}>"

        try:
            await page.screenshot(path=str(screenshot_path), full_page=True)
        except PlaywrightError as exc:
            logger.warning("[FLIPKART LOGIN DEBUG] screenshot capture failed: %s", exc)

        html = ""
        try:
            html = await page.content()
            html_path.write_text(html, encoding="utf-8")
        except (PlaywrightError, OSError) as exc:
            logger.warning("[FLIPKART LOGIN DEBUG] html capture failed: %s", exc)

        print("=" * 80)
        print("LOGIN PAGE INSPECTION")
        print("URL:", url)
        print("Title:", title)
        print("HTML saved:", html_path, f"({len(html)} chars)")
        print("Screenshot saved:", screenshot_path)
        logger.info("[FLIPKART LOGIN DEBUG] URL: %s", url)
        logger.info("[FLIPKART LOGIN DEBUG] Title: %s", title)
        logger.info("[FLIPKART LOGIN DEBUG] html=%s (length=%d chars)", html_path, len(html))
        logger.info("[FLIPKART LOGIN DEBUG] screenshot=%s", screenshot_path)

        # -- element counts ------------------------------------------------
        inputs = await page.query_selector_all("input")
        forms = await page.query_selector_all("form")
        buttons = await page.query_selector_all("button")
        links = await page.query_selector_all("a")
        iframe_elements = await page.query_selector_all("iframe")

        print(
            f"Counts -> inputs: {len(inputs)}, forms: {len(forms)}, "
            f"buttons: {len(buttons)}, links: {len(links)}, iframes: {len(iframe_elements)}"
        )
        logger.info(
            "[FLIPKART LOGIN DEBUG] counts inputs=%d forms=%d buttons=%d links=%d iframes=%d",
            len(inputs), len(forms), len(buttons), len(links), len(iframe_elements),
        )

        # -- enumerate every input ------------------------------------------
        print("-- INPUTS --")
        for i, inp in enumerate(inputs):
            try:
                attrs = await inp.evaluate(
                    "el => ({type: el.type, name: el.name, id: el.id, "
                    "placeholder: el.placeholder, autocomplete: el.autocomplete, "
                    "'aria-label': el.getAttribute('aria-label')})"
                )
            except PlaywrightError as exc:
                attrs = {"error": str(exc)}
            print(f"  input[{i}]:", attrs)
            logger.info("[FLIPKART LOGIN DEBUG] input[%d] %s", i, attrs)

        # -- enumerate every button (inner text only) -----------------------
        print("-- BUTTONS --")
        for i, btn in enumerate(buttons):
            try:
                text = (await btn.inner_text()).strip()
            except PlaywrightError as exc:
                text = f"<error: {exc}>"
            print(f"  button[{i}]: text={text!r}")
            logger.info("[FLIPKART LOGIN DEBUG] button[%d] text=%s", i, text)

        # -- enumerate every link (inner text + href) ------------------------
        print("-- LINKS --")
        for i, link in enumerate(links):
            try:
                text = (await link.inner_text()).strip()
            except PlaywrightError as exc:
                text = f"<error: {exc}>"
            try:
                href = await link.get_attribute("href")
            except PlaywrightError as exc:
                href = f"<error: {exc}>"
            print(f"  link[{i}]: text={text!r} href={href!r}")
            logger.info("[FLIPKART LOGIN DEBUG] link[%d] text=%s href=%s", i, text, href)

        # -- enumerate every frame (main frame + iframes) -------------------
        print("-- FRAMES --")
        for i, frame in enumerate(page.frames):
            print(f"  frame[{i}]: name={frame.name!r} url={frame.url!r}")
            logger.info("[FLIPKART LOGIN DEBUG] frame[%d] name=%s url=%s", i, frame.name, frame.url)

        # -- Shadow DOM detection --------------------------------------------
        try:
            shadow_hosts = await page.evaluate(
                """
                () => {
                    const hosts = [];
                    document.querySelectorAll('*').forEach(el => {
                        if (el.shadowRoot) {
                            hosts.push({
                                tag: el.tagName,
                                id: el.id || null,
                                class: el.className || null,
                            });
                        }
                    });
                    return hosts;
                }
                """
            )
        except PlaywrightError as exc:
            shadow_hosts = [{"error": str(exc)}]

        print("-- SHADOW DOM HOSTS --")
        if shadow_hosts:
            for i, host in enumerate(shadow_hosts):
                print(f"  shadow_host[{i}]:", host)
                logger.info("[FLIPKART LOGIN DEBUG] shadow_host[%d] %s", i, host)
        else:
            print("  none detected")
            logger.info("[FLIPKART LOGIN DEBUG] no shadow DOM hosts detected")
        print("=" * 80)

    async def debug_table_diagnostics(self, page: Page, stage_name: str) -> int:
        print("=" * 80)
        print("DEBUG_TABLE_DIAGNOSTICS CALLED")
        print("Stage:", stage_name)
        print("=" * 80)
        """
        Logs table/tbody/tr counts (plus button/link/div counts and
        page.content() length as extra signal) BEFORE any row parsing,
        so a zero-rows result can be told apart from:
          - table absent entirely (page never really loaded the panel)
          - table present, but FlipkartSelectors.TABLE_ROW doesn't
            match this table's markup (selector guess is wrong)
          - table present and matched, genuinely zero data rows

        Returns the count of elements matching
        FlipkartSelectors.TABLE_ROW (i.e. what the real scrape will
        see), so callers can log "No table rows found" without
        querying the DOM a second time.
        """
        url = page.url
        try:
            title = await page.title()
        except PlaywrightError as exc:
            title = f"<title unavailable: {exc}>"

        tables = await page.query_selector_all("table")
        tbodies = await page.query_selector_all("tbody")
        trs = await page.query_selector_all("tr")
        matched_rows = await page.query_selector_all(FlipkartSelectors.TABLE_ROW)

        logger.info("[FLIPKART DEBUG] stage=%s URL: %s", stage_name, url)
        logger.info("[FLIPKART DEBUG] stage=%s Title: %s", stage_name, title)
        logger.info("[FLIPKART DEBUG] stage=%s Tables: %d", stage_name, len(tables))
        logger.info("[FLIPKART DEBUG] stage=%s Tbody: %d", stage_name, len(tbodies))
        logger.info("[FLIPKART DEBUG] stage=%s Tr: %d", stage_name, len(trs))
        logger.info("[FLIPKART DEBUG] stage=%s Rows (table tbody tr): %d", stage_name, len(matched_rows))

        try:
            content_len = len(await page.content())
        except PlaywrightError:
            content_len = -1
        buttons = await page.query_selector_all("button")
        links = await page.query_selector_all("a")
        divs = await page.query_selector_all("div")
        logger.info(
            "[FLIPKART DEBUG] stage=%s content_length=%d buttons=%d links=%d divs=%d",
            stage_name, content_len, len(buttons), len(links), len(divs),
        )

        return len(matched_rows)

    # -- Task 1: session management -----------------------------------

    async def _get_authenticated_page(self, context: BrowserContext) -> Page:
        """
        Restore a cached session if we have one; detect that it's
        expired (redirected to /login); if so (or if we had nothing
        cached), perform a fresh login and cache the result. Callers
        never need to manually re-login -- one call gets a page that's
        either already authenticated or freshly authenticated.
        """
        cached_cookies = self._cookie_cache.get(self.seller_id)
        if cached_cookies:
            await context.add_cookies(cached_cookies)

        page = await context.new_page()

        async def _load_dashboard():
            try:
                await page.goto(_route("dashboard", "/index.html#dashboard"), wait_until="networkidle", timeout=15000)
            except PlaywrightError as exc:
                raise NavigationError(f"Timed out loading Flipkart dashboard: {exc}") from exc

        try:
            await _with_retries(_load_dashboard, tool="load_dashboard")
        except NavigationError:
            # Couldn't even confirm whether the session is valid --
            # fall through to a fresh login rather than giving up.
            pass

        url = page.url.lower()
        title = (await page.title()).lower()

        needs_login = (
             "login" in url
            or "page-not-found" in url
             or "become an online seller" in title
        )

        logger.info(
            "[AUTH CHECK] url=%s title=%s needs_login=%s",
            url,
            title,
            needs_login,
        )

        if needs_login:
            logger.info("Running Flipkart login")
            await self._login(page)

        return page

    async def _click_first_available(
        self, page: Page, selectors: "tuple[str, ...]", *, timeout: int = 10000
    ) -> str:
        """
        Tries each selector in `selectors` in order, clicking the first
        one that actually matches something on the page. Exists because
        different Playwright selector engines (`text=...` vs plain CSS)
        can't be joined with commas into one selector string -- unlike
        a pure-CSS list (e.g. FlipkartSelectors.PAGINATION_NEXT), where
        every branch is the same engine and a comma-joined string IS
        one valid selector. This tries genuinely different candidates
        one at a time instead of concatenating them into an invalid
        string.

        Polls all candidates in a loop (rather than giving each one a
        full independent timeout) so slow-to-render UI still gets
        picked up by whichever candidate ends up matching, without
        summing every candidate's timeout into one long wait.

        Returns the selector that actually matched, so the caller can
        log which candidate worked. Raises PlaywrightTimeoutError if
        none of the candidates match within `timeout` ms.
        """
        deadline = time.monotonic() + (timeout / 1000)
        last_exc: Optional[Exception] = None
        while time.monotonic() < deadline:
            for selector in selectors:
                try:
                    locator = page.locator(selector)
                    if await locator.count() > 0:
                        await locator.first.click(timeout=2000)
                        return selector
                except PlaywrightError as exc:
                    last_exc = exc
                    continue
            await asyncio.sleep(0.25)
        raise PlaywrightTimeoutError(
            f"None of the candidate selectors matched a clickable element: {selectors}"
        ) from last_exc

    async def _login(self, page: Page) -> None:
        print("=" * 80)
        print("LOGIN START")
        print("=" * 80)

        page.on(
            "console",
            lambda msg: print(f"[CONSOLE] {msg.type}: {msg.text}")
        )

        page.on(
            "pageerror",
            lambda exc: print(f"[PAGE ERROR] {exc}")
        )

        page.on(
            "requestfailed",
            lambda req: print(
                f"[REQUEST FAILED] {req.url} -> {req.failure or 'Unknown'}"
            )
        )

        """
        Full login workflow. Retries the request ONCE after a fresh
        login on session-expiry-shaped failures, per Task 1 -- but
        never retries on genuinely invalid credentials (that's not
        transient, it's not going to start working on attempt 2).
        """
        try:
            # /login as a directly-navigable URL is confirmed obsolete
            # (bare HTTP 404 -- see debug_capture_navigation's earlier
            # findings). The real flow starts at the homepage, the same
            # entry point a human seller uses.
            nav_response = await page.goto(BASE_URL, wait_until="domcontentloaded")
            print("After goto homepage:", page.url)
            await self.debug_capture_navigation(page, nav_response)
            await self.debug_capture(page, "homepage_loaded")

            login_button = page.get_by_role("button", name="Login")

            await login_button.wait_for(
                state="visible",
                timeout=10000,
            )

            await login_button.click()

            print("Clicked Login button")

            await self.debug_capture(page, "after_login_entry_click")
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except PlaywrightTimeoutError:
                pass

            await page.wait_for_timeout(1000)

            print("URL after Login click:", page.url)

            if "signup" in page.url.lower() or "accountcreation" in page.url.lower():
                raise SelectorError(
                    f"Clicked Login but landed on signup page: {page.url}"
                )
            await self.debug_inspect_login_page(page)


            # -- Discovered controls (see FlipkartSelectors) -----------------
            # input[name="username"] / input[name="password"], and
            # "Next"/"Login" buttons -- confirmed via the discovery run,
            # not guessed. Supports both possible flows:
            #   Flow A: username -> Next -> password -> Login
            #   Flow B: username + password both visible -> Login
            print("HTML length:", len(await page.content()))
            username_input = page.locator(FlipkartSelectors.LOGIN_USERNAME_INPUT)
            await username_input.wait_for(state="visible", timeout=10000)
            await username_input.fill(self.username)
            print("Username filled")

            next_button = page.get_by_role("button", name=FlipkartSelectors.LOGIN_NEXT_BUTTON_TEXT)
            if await next_button.count() > 0 and await next_button.first.is_visible():
                await next_button.first.click()
                print("Next clicked (Flow A)")
            else:
                print("No visible Next button -- proceeding as Flow B (single-screen form)")

            password_input = page.locator(FlipkartSelectors.LOGIN_PASSWORD_INPUT)
            await password_input.wait_for(state="visible", timeout=10000)
            await password_input.fill(self.password)
            print("Password filled")

            login_button = page.get_by_role("button", name=FlipkartSelectors.LOGIN_SUBMIT_BUTTON_TEXT)
            await login_button.first.click()
            print("Login clicked")

            print("URL immediately after click:", page.url)

            await page.wait_for_timeout(5000)

            print("URL after 5 seconds:", page.url)
            print("Title after 5 seconds:", await page.title())

            body_text = await page.locator("body").inner_text()

            print("=" * 80)
            print("BODY TEXT AFTER LOGIN")
            print("=" * 80)
            print(body_text[:5000])
            print("=" * 80)

            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except PlaywrightTimeoutError:
                pass

            print("Final URL:", page.url)
            print("Final Title:", await page.title())

            await self.debug_capture(page, "after_login_click")

            # -- Success check ------------------------------------------------
            # Same heuristic _get_authenticated_page already uses: if the
            # page still looks like the login page, stop and report the
            # exact state (already captured above) rather than guessing
            # at more selectors.
            url = page.url.lower()
            title = (await page.title()).lower()
            login_still_showing = "login" in url or "become an online seller" in title
            if login_still_showing:
                print("=" * 80)
                print("LOGIN DID NOT SUCCEED AFTER CLICKING LOGIN")
                print("Current URL:", page.url)
                print("Current Title:", await page.title())
                print("See debug_capture('after_login_click') screenshot/HTML for the exact page state.")
                print("=" * 80)
                raise SessionExpiredError(
                    "Flipkart login click completed but the page still looks like the "
                    f"login page (url={page.url!r}, title={title!r}). See "
                    "debug_capture('after_login_click') output for the exact state -- "
                    "no further selectors were guessed."
                )

            cookies = await page.context.cookies()
            self._cookie_cache[self.seller_id] = cookies
            print("LOGIN SUCCESS")
            print(page.url)
        except PlaywrightTimeoutError as exc:
            print("=" * 80)
            print("LOGIN TIMEOUT")
            print("Current URL:", page.url)
            print("Current Title:", await page.title())
            print("=" * 80)
            await self.debug_capture(page, "login_timeout")
            raise SessionExpiredError(
                "Flipkart authentication failed or timed out. Please reconnect your account."
            ) from exc

        except PlaywrightError as exc:
            print("=" * 80)
            print("LOGIN PLAYWRIGHT ERROR")
            print("Current URL:", page.url)
            print("Current Title:", await page.title())
            print(exc)
            print("=" * 80)
            await self.debug_capture(page, "login_playwright_error")
            raise NavigationError(
                f"Flipkart login navigation failed: {exc}"
            ) from exc
    # -- shared helpers -------------------------------------------------

    async def _safe_text(self, page: Page, selector: str, default=None):
        """Returns `default` if the element genuinely isn't present --
        this is a real "selector may not match production" gap, not an
        error worth raising, since several metrics fields are optional
        even in the real Seller Hub (e.g. no returns yet)."""
        try:
            element = await page.query_selector(selector)
            if not element:
                return default
            text = await element.inner_text()
            return text.strip() if text else default
        except PlaywrightError:
            return default

    async def _paginate(self, page: Page, skip_pages: int) -> None:
        """
        Click through to the requested starting page using the same
        Next-button mechanism proven out in meesho_connector.py /
        flipkart's own SELECTORS-based sibling implementation, instead
        of silently ignoring the `page` argument -- every fetch_*
        method here previously accepted `page` and always returned the
        table's own first page regardless of what was requested.
        """
        for _ in range(skip_pages):
            next_button = page.locator(FlipkartSelectors.PAGINATION_NEXT)
            if await next_button.count() == 0:
                break  # asked to skip past the last available page
            await next_button.first.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightError as exc:
                raise NavigationError(f"Timed out paginating Flipkart table: {exc}") from exc

    async def _check_rate_limited(self, page: Page) -> None:
        """
        Mirrors meesho_connector.py's _check_rate_limited exactly (same
        selector, same mock server). Must run BEFORE row extraction --
        a rate-limited response has no rows of either shape, so waiting
        on rows first (as this file used to, implicitly, by just
        finding zero and returning an empty list) previously surfaced a
        real rate limit as a silent empty result instead of a specific,
        actionable RateLimitError.
        """
        if await page.locator(FlipkartSelectors.RATE_LIMIT_BANNER).count() > 0:
            raise RateLimitError("Flipkart Seller Hub reported a rate limit / throttling banner.")

    async def _scrape_rows_normalized(
        self,
        page: Page,
        *,
        min_cells: int,
        field_names: "list[str]",
        testid_selector: str,
        dataset_field_map: "Dict[str, str]",
    ) -> "list[Dict[str, str]]":
        """
        Row-extraction normalization: returns a list of plain dicts,
        each guaranteed to contain every name in `field_names`
        (defaulting to "" if a source didn't supply it), regardless of
        which DOM shape actually supplied the data --

          - Production's assumed <table><tbody><tr><td> layout
            (unverified -- see this class's docstring): cells mapped
            positionally onto `field_names`, same index-to-field
            mapping the old per-index `cells[0]`, `cells[1]`, ...
            call sites used inline.
          - tests/mock_panel_server.py's `data-testid="..."` div rows
            (the same shape meesho_connector.py's `_extract_row_data`
            reads): read via the element's `.dataset` and mapped onto
            `field_names` through `dataset_field_map`.

        Callers (fetch_products/fetch_orders/fetch_inventory/
        fetch_shipments) read the returned dicts by field name either
        way, so which branch actually ran is invisible past this
        point -- "downstream code does not change" whether the page
        turns out to be a real table or the mock's data-testid rows.
        """
        table_rows = await page.query_selector_all(FlipkartSelectors.TABLE_ROW)
        if table_rows:
            normalized = []
            for row in table_rows:
                cells = await row.query_selector_all(FlipkartSelectors.TABLE_CELL)
                if len(cells) < min_cells:
                    continue
                record = {}
                for i, name in enumerate(field_names):
                    record[name] = (await cells[i].inner_text()).strip() if i < len(cells) else ""
                normalized.append(record)
            return normalized

        # No <table> on the page at all -- fall back to data-testid rows
        # (tests/mock_panel_server.py's shape; also a plausible real
        # Seller Hub shape, equally unverified either way).
        testid_rows = await page.query_selector_all(testid_selector)
        normalized = []
        for row in testid_rows:
            dataset = await row.evaluate("el => ({...el.dataset})")
            record = {name: "" for name in field_names}
            for dataset_key, field_name in dataset_field_map.items():
                value = dataset.get(dataset_key)
                if value:
                    record[field_name] = value
            normalized.append(record)
        return normalized

    async def _collect_paginated_rows(
        self,
        page: Page,
        *,
        min_cells: int,
        field_names: "list[str]",
        testid_selector: str,
        dataset_field_map: "Dict[str, str]",
        limit: int,
        row_filter: "Optional[Callable[[Dict[str, str]], bool]]" = None,
    ) -> "list[Dict[str, str]]":
        """
        Repeatedly extracts the current page's rows (via
        `_scrape_rows_normalized`) and clicks "Next" (via the same
        PAGINATION_NEXT locator `_paginate` uses for the initial
        skip-ahead) until `limit` rows have been collected or no
        further page is available -- mirrors meesho_connector.py's
        `_paginate_rows` while-loop, including its dedupe-by-content
        and no-forward-progress stop conditions.

        Previously, every fetch_* method here called the single-page
        scrape exactly once: a `limit` larger than one page's worth of
        rows silently returned fewer rows than requested instead of
        continuing to the next page for more, even though `_paginate`
        already proved out clicking "Next" for the *initial* skip-ahead
        (Task: "page skips ahead"). This reuses that same mechanism for
        the *collection* loop too.

        `row_filter`, if given, is applied before a row counts toward
        `limit` (e.g. status/order_id matching) -- matching how the old
        inline per-method loops filtered before appending, so a filter
        that discards most rows on a page still causes further pages to
        be fetched rather than returning an under-sized result.
        """
        await self._check_rate_limited(page)

        collected: "list[Dict[str, str]]" = []
        seen_rows: set = set()
        while len(collected) < limit:
            await self._check_rate_limited(page)
            rows = await self._scrape_rows_normalized(
                page,
                min_cells=min_cells,
                field_names=field_names,
                testid_selector=testid_selector,
                dataset_field_map=dataset_field_map,
            )
            page_had_new_row = False
            for row in rows:
                signature = tuple(sorted(row.items()))
                if signature in seen_rows:
                    continue
                seen_rows.add(signature)
                page_had_new_row = True
                if row_filter is not None and not row_filter(row):
                    continue
                collected.append(row)
                if len(collected) >= limit:
                    break

            next_button = page.locator(FlipkartSelectors.PAGINATION_NEXT)
            if len(collected) >= limit or await next_button.count() == 0:
                break
            if not page_had_new_row:
                # "Next" is present but produced nothing we haven't
                # already collected -- treat pagination as genuinely
                # terminated rather than clicking forever.
                break
            await next_button.first.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightError as exc:
                raise NavigationError(f"Timed out paginating Flipkart table: {exc}") from exc

        return collected

    @staticmethod
    def _parse_number(text: str, *, tool: str, field: str) -> float:
        try:
            return float(text.replace("\u20b9", "").replace(",", "").strip() or 0.0)
        except ValueError as exc:
            raise ParsingError(f"Flipkart {tool}: couldn't parse '{field}' value '{text}'") from exc

    # -- metrics ----------------------------------------------------------

    async def _fetch_sales_metrics(self, browser: Browser, days: int = 30) -> Dict[str, Any]:
        """Fetches live sales, revenue, and order metrics end-to-end from Flipkart Hub."""
        start_time = time.monotonic()
        context = await browser.new_context()
        try:
            page = await self._get_authenticated_page(context)

            async def _load_analytics():
                try:
                    await page.goto(_route("analytics_sales", "/index.html#analytics/sales"), wait_until="networkidle", timeout=20000)
                except PlaywrightError as exc:
                    raise NavigationError(f"Timed out loading Flipkart analytics: {exc}") from exc

            await _with_retries(_load_analytics, tool="fetch_sales_metrics")
            if "login" in page.url.lower():
                logger.info("Flipkart session expired mid-request for seller_id=%s (fetch_sales_metrics) -- re-authenticating.", self.seller_id)
                await self._login(page)
                await _with_retries(_load_analytics, tool="fetch_sales_metrics")

            await self.debug_capture(page, "sales_metrics_loaded")

            revenue_text = await self._safe_text(page, FlipkartSelectors.SALES_GROSS_REVENUE, "0")
            orders_text = await self._safe_text(page, FlipkartSelectors.SALES_TOTAL_ORDERS, "0")
            units_text = await self._safe_text(page, FlipkartSelectors.SALES_UNITS_SOLD, "0")
            cancelled_text = await self._safe_text(page, FlipkartSelectors.SALES_CANCELLED_ORDERS, None)
            returned_text = await self._safe_text(page, FlipkartSelectors.SALES_RETURNED_ORDERS, None)
            growth_text = await self._safe_text(page, FlipkartSelectors.SALES_GROWTH, None)

            gross_revenue = self._parse_number(revenue_text, tool="fetch_sales_metrics", field="gross_revenue")
            total_orders = int(self._parse_number(orders_text, tool="fetch_sales_metrics", field="total_orders"))
            units_sold = int(self._parse_number(units_text, tool="fetch_sales_metrics", field="units_sold"))
            aov = (gross_revenue / total_orders) if total_orders > 0 else 0.0

            cancelled_orders = int(self._parse_number(cancelled_text, tool="fetch_sales_metrics", field="cancelled_orders")) if cancelled_text else None
            returned_orders = int(self._parse_number(returned_text, tool="fetch_sales_metrics", field="returned_orders")) if returned_text else None
            try:
                growth_percentage = float(growth_text.replace("%", "").strip()) if growth_text else None
            except ValueError:
                growth_percentage = None

            result = {
                "marketplace": "flipkart",
                "period_days": days,
                "gross_revenue": gross_revenue,
                "net_revenue": None,
                "total_orders": total_orders,
                "units_sold": units_sold,
                "average_order_value": round(aov, 2),
                "cancelled_orders": cancelled_orders,
                "returned_orders": returned_orders,
                "growth_percentage": growth_percentage,
                "daily_sales": [],
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
            }
            _log_call("fetch_sales_metrics", self.seller_id, start_time, success=True)
            return result

        except SessionExpiredError as exc:
            _log_call("fetch_sales_metrics", self.seller_id, start_time, success=False, error=exc)
            raise
        except (NavigationError, SelectorError, ParsingError) as exc:
            logger.error("Error fetching Flipkart sales metrics for seller_id=%s: %s", self.seller_id, exc)
            _log_call("fetch_sales_metrics", self.seller_id, start_time, success=False, error=exc)
            return {
                "marketplace": "flipkart",
                "period_days": days,
                "gross_revenue": 0.0,
                "total_orders": 0,
                "status": "error",
                "error_message": "Failed to fetch live sales metrics from Flipkart. Please verify credentials.",
            }
        except PlaywrightError as exc:
            # Previously had no catch-all: a raw Playwright error here
            # (unexpected page state, e.g.) would have escaped the
            # connector boundary unwrapped.
            wrapped = SelectorError(f"Flipkart fetch_sales_metrics: unexpected page state: {exc}")
            logger.error("Error fetching Flipkart sales metrics for seller_id=%s: %s", self.seller_id, wrapped)
            _log_call("fetch_sales_metrics", self.seller_id, start_time, success=False, error=wrapped)
            return {
                "marketplace": "flipkart",
                "period_days": days,
                "gross_revenue": 0.0,
                "total_orders": 0,
                "status": "error",
                "error_message": "Failed to fetch live sales metrics from Flipkart. Please verify credentials.",
            }
        finally:
            await context.close()

    async def _fetch_inventory_metrics(self, browser: Browser) -> Dict[str, Any]:
        """Fetches current stock and active listings info."""
        start_time = time.monotonic()
        context = await browser.new_context()
        try:
            page = await self._get_authenticated_page(context)

            async def _load_inventory():
                try:
                    await page.goto(ROUTES["inventory"], wait_until="networkidle", timeout=15000)
                except PlaywrightError as exc:
                    raise NavigationError(f"Timed out loading Flipkart inventory: {exc}") from exc

            await _with_retries(_load_inventory, tool="fetch_inventory_metrics")
            if "login" in page.url.lower():
                logger.info("Flipkart session expired mid-request for seller_id=%s (fetch_inventory_metrics) -- re-authenticating.", self.seller_id)
                await self._login(page)
                await _with_retries(_load_inventory, tool="fetch_inventory_metrics")

            await self.debug_capture(page, "inventory_metrics_loaded")

            active_text = await self._safe_text(page, FlipkartSelectors.INVENTORY_ACTIVE_LISTINGS, "0")
            low_stock_text = await self._safe_text(page, FlipkartSelectors.INVENTORY_LOW_STOCK, "0")

            result = {
                "marketplace": "flipkart",
                "active_listings": int(self._parse_number(active_text, tool="fetch_inventory_metrics", field="active_listings")),
                "low_stock_alerts": int(self._parse_number(low_stock_text, tool="fetch_inventory_metrics", field="low_stock_alerts")),
                "timestamp": datetime.utcnow().isoformat(),
            }
            _log_call("fetch_inventory_metrics", self.seller_id, start_time, success=True)
            return result
        except (NavigationError, SelectorError, ParsingError, SessionExpiredError):
            raise
        except PlaywrightError as exc:
            wrapped = SelectorError(f"Flipkart fetch_inventory_metrics: unexpected page state: {exc}")
            _log_call("fetch_inventory_metrics", self.seller_id, start_time, success=False, error=wrapped)
            raise wrapped from exc
        except Exception as exc:
            _log_call("fetch_inventory_metrics", self.seller_id, start_time, success=False, error=exc)
            raise
        finally:
            await context.close()

    async def _fetch_business_metrics(self, browser: Browser, days: int = 30) -> Dict[str, Any]:
        """
        Combines sales and inventory metrics into one business summary.
        Shares ONE browser across both sub-fetches, passed down as an
        explicit argument, instead of each one launching/closing its
        own -- previously _fetch_sales_metrics and
        _fetch_inventory_metrics each opened a separate Chromium
        instance for what is logically one operation.
        """
        sales = await self._fetch_sales_metrics(browser, days)
        inventory = await self._fetch_inventory_metrics(browser)
        return {
            "marketplace": "flipkart",
            "status": "success",
            "sales_performance": sales,
            "inventory_health": inventory,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _verify_connection(self, browser: Browser) -> Dict[str, Any]:
        """Verifies that the Flipkart Seller Hub session is valid. Used
        by the Executive Agent before performing operations."""
        start_time = time.monotonic()
        context = await browser.new_context()
        try:
            page = await self._get_authenticated_page(context)
            await page.goto(_route("dashboard", "/index.html#dashboard"), wait_until="networkidle", timeout=15000)
            latency = (time.monotonic() - start_time) * 1000
            _log_call("verify_connection", self.seller_id, start_time, success=True)
            return {
                "platform": "flipkart",
                "seller_id": self.seller_id,
                "is_connected": True,
                "latency_ms": round(latency, 2),
                "message": "Connected successfully",
            }
        except Exception as exc:
            _log_call("verify_connection", self.seller_id, start_time, success=False, error=exc)
            return {
                "platform": "flipkart",
                "seller_id": self.seller_id,
                "is_connected": False,
                "latency_ms": None,
                "message": str(exc),
            }
        finally:
            await context.close()

    # -- products / orders / inventory / shipments -----------------------

    async def _fetch_products(self, browser: Browser, page: int = 1, limit: int = 50, category: Optional[str] = None) -> "list[Dict[str, Any]]":
        start_time = time.monotonic()
        context = await browser.new_context()
        try:
            page_obj = await self._get_authenticated_page(context)

            async def _load():
                try:
                    await page_obj.goto(ROUTES["catalog"], wait_until="networkidle", timeout=20000)
                except PlaywrightError as exc:
                    raise NavigationError(f"Timed out loading Flipkart listings: {exc}") from exc

            await _with_retries(_load, tool="fetch_products")
            if "login" in page_obj.url.lower():
                logger.info("Flipkart session expired mid-request for seller_id=%s (fetch_products) -- re-authenticating.", self.seller_id)
                await self._login(page_obj)
                await _with_retries(_load, tool="fetch_products")
            await self._paginate(page_obj, skip_pages=page - 1)

            await self.debug_capture(page_obj, "products_loaded")
            diag_row_count = await self.debug_table_diagnostics(page_obj, "products_table_check")
            if diag_row_count == 0:
                logger.warning(
                    "[FLIPKART DEBUG] No table rows found for fetch_products (seller_id=%s) -- "
                    "HTML preserved for inspection.", self.seller_id,
                )

            raw_rows = await self._collect_paginated_rows(
                page_obj,
                min_cells=5,
                field_names=["sku", "title", "status", "stock", "price"],
                testid_selector=FlipkartSelectors.PRODUCT_ROW_TESTID,
                dataset_field_map={"sku": "sku", "status": "status"},
                limit=limit,
            )

            products = []
            for row in raw_rows:
                products.append({
                    "skuId": row["sku"], "listingId": row["sku"], "productTitle": row["title"],
                    "sellingPrice": row["price"], "availableUnits": row["stock"], "listingStatus": row["status"],
                    "sku": row["sku"], "title": row["title"], "price": row["price"],
                    "stock": row["stock"], "status": row["status"],
                })

            _log_call("fetch_products", self.seller_id, start_time, success=True)
            return products
        except (NavigationError, SelectorError, ParsingError, SessionExpiredError, RateLimitError):
            raise
        except PlaywrightError as exc:
            # A raw Playwright error here means the DOM shifted mid-scrape
            # (row detached, page navigated away, etc.) -- translate it so
            # no bare Playwright exception ever escapes the connector
            # boundary (Phase 7 requirement).
            wrapped = SelectorError(f"Flipkart fetch_products: unexpected page state while scraping: {exc}")
            _log_call("fetch_products", self.seller_id, start_time, success=False, error=wrapped)
            raise wrapped from exc
        except Exception as exc:
            _log_call("fetch_products", self.seller_id, start_time, success=False, error=exc)
            raise
        finally:
            await context.close()

    async def _fetch_inventory(self, browser: Browser, sku: Optional[str] = None, page: int = 1, limit: int = 50) -> "list[Dict[str, Any]]":
        start_time = time.monotonic()
        context = await browser.new_context()
        try:
            page_obj = await self._get_authenticated_page(context)

            async def _load():
                try:
                    await page_obj.goto(ROUTES["inventory"], wait_until="networkidle", timeout=20000)
                except PlaywrightError as exc:
                    raise NavigationError(f"Timed out loading Flipkart inventory: {exc}") from exc

            await _with_retries(_load, tool="fetch_inventory")
            if "login" in page_obj.url.lower():
                logger.info("Flipkart session expired mid-request for seller_id=%s (fetch_inventory) -- re-authenticating.", self.seller_id)
                await self._login(page_obj)
                await _with_retries(_load, tool="fetch_inventory")
            await self._paginate(page_obj, skip_pages=page - 1)

            await self.debug_capture(page_obj, "inventory_loaded")
            diag_row_count = await self.debug_table_diagnostics(page_obj, "inventory_table_check")

            if diag_row_count == 0:
                logger.warning(
                    "[FLIPKART DEBUG] No table rows found for fetch_inventory (seller_id=%s) -- "
                    "HTML preserved for inspection.", self.seller_id,
                )

            sku_filter = (lambda r: r["sku"] == sku) if sku else None
            raw_rows = await self._collect_paginated_rows(
                page_obj,
                min_cells=4,
                field_names=["sku", "available_quantity", "reserved_quantity", "status"],
                testid_selector=FlipkartSelectors.INVENTORY_ROW_TESTID,
                dataset_field_map={"sku": "sku", "status": "status"},
                limit=limit,
                row_filter=sku_filter,
            )

            inventory = []
            for row in raw_rows:
                inventory.append({
                    "skuId": row["sku"], "availableUnits": row["available_quantity"], "listingStatus": row["status"],
                    "sku": row["sku"], "available_quantity": row["available_quantity"],
                    "reserved_quantity": row["reserved_quantity"], "status": row["status"],
                })

            _log_call("fetch_inventory", self.seller_id, start_time, success=True)
            return inventory
        except (NavigationError, SelectorError, ParsingError, SessionExpiredError, RateLimitError):
            raise
        except PlaywrightError as exc:
            wrapped = SelectorError(f"Flipkart fetch_inventory: unexpected page state while scraping: {exc}")
            _log_call("fetch_inventory", self.seller_id, start_time, success=False, error=wrapped)
            raise wrapped from exc
        except Exception as exc:
            _log_call("fetch_inventory", self.seller_id, start_time, success=False, error=exc)
            raise
        finally:
            await context.close()

    async def _fetch_orders(
        self,
        browser: Browser,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50,
    ) -> "list[Dict[str, Any]]":
        start_time = time.monotonic()
        context = await browser.new_context()
        try:
            page_obj = await self._get_authenticated_page(context)

            # Previously always navigated to the bare orders URL and
            # applied `status` as a client-side-only filter afterward --
            # the server (real or mock) never saw it, so a server-side
            # rate-limit trigger keyed on this param (as
            # tests/mock_panel_server.py's is) could never be reached.
            # Mirrors meesho_connector.py's fetch_orders, which already
            # appends `status` this way.
            orders_url = ROUTES["orders"]
            if status:
                orders_url += f"?status={status}"

            async def _load():
                try:
                    await page_obj.goto(orders_url, wait_until="networkidle", timeout=20000)
                except PlaywrightError as exc:
                    raise NavigationError(f"Timed out loading Flipkart orders: {exc}") from exc

            await _with_retries(_load, tool="fetch_orders")
            if "login" in page_obj.url.lower():
                logger.info("Flipkart session expired mid-request for seller_id=%s (fetch_orders) -- re-authenticating.", self.seller_id)
                await self._login(page_obj)
                await _with_retries(_load, tool="fetch_orders")
            await self._paginate(page_obj, skip_pages=page - 1)

            await self.debug_capture(page_obj, "orders_loaded")
            diag_row_count = await self.debug_table_diagnostics(page_obj, "orders_table_check")
            if diag_row_count == 0:
                logger.warning(
                    "[FLIPKART DEBUG] No table rows found for fetch_orders (seller_id=%s) -- "
                    "HTML preserved for inspection.", self.seller_id,
                )

            status_filter = (
                (lambda r: r["status"].lower() == status.lower()) if status else None
            )
            raw_rows = await self._collect_paginated_rows(
                page_obj,
                min_cells=7,
                field_names=["order_id", "sku", "product_name", "quantity", "order_date", "status", "amount"],
                testid_selector=FlipkartSelectors.ORDER_ROW_TESTID,
                dataset_field_map={"orderId": "order_id", "status": "status"},
                limit=limit,
                row_filter=status_filter,
            )

            orders = []
            for row in raw_rows:
                order = {
                    "orderId": row["order_id"],
                    "orderValue": row["amount"],
                    "orderDate": row["order_date"],
                    "status": row["status"],
                    "order_id": row["order_id"],
                    "sku": row["sku"],
                    "product_name": row["product_name"],
                    "quantity": row["quantity"],
                    "order_date": row["order_date"],
                    "amount": row["amount"],
                }

                if start_date or end_date:
                    try:
                        dt = datetime.fromisoformat(order["order_date"][:10])
                        if start_date and dt < start_date:
                            continue
                        if end_date and dt > end_date:
                            continue
                    except ValueError:
                        pass  # unparsable date on this row -- don't drop the row over a date filter we can't apply

                orders.append(order)

            _log_call("fetch_orders", self.seller_id, start_time, success=True)
            return orders
        except (NavigationError, SelectorError, ParsingError, SessionExpiredError, RateLimitError):
            raise
        except PlaywrightError as exc:
            wrapped = SelectorError(f"Flipkart fetch_orders: unexpected page state while scraping: {exc}")
            _log_call("fetch_orders", self.seller_id, start_time, success=False, error=wrapped)
            raise wrapped from exc
        except Exception as exc:
            _log_call("fetch_orders", self.seller_id, start_time, success=False, error=exc)
            raise
        finally:
            await context.close()

    async def _fetch_shipments(
        self,
        browser: Browser,
        order_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> "list[Dict[str, Any]]":
        start_time = time.monotonic()
        context = await browser.new_context()
        try:
            page_obj = await self._get_authenticated_page(context)

            async def _load():
                try:
                    await page_obj.goto(ROUTES["shipments"], wait_until="networkidle", timeout=20000)
                except PlaywrightError as exc:
                    raise NavigationError(f"Timed out loading Flipkart shipments: {exc}") from exc

            await _with_retries(_load, tool="fetch_shipments")
            if "login" in page_obj.url.lower():
                logger.info("Flipkart session expired mid-request for seller_id=%s (fetch_shipments) -- re-authenticating.", self.seller_id)
                await self._login(page_obj)
                await _with_retries(_load, tool="fetch_shipments")
            await self._paginate(page_obj, skip_pages=page - 1)

            await self.debug_capture(page_obj, "shipments_loaded")
            diag_row_count = await self.debug_table_diagnostics(page_obj, "shipments_table_check")

            if diag_row_count == 0:
                logger.warning(
                    "[FLIPKART DEBUG] No table rows found for fetch_shipments (seller_id=%s) -- "
                    "HTML preserved for inspection.", self.seller_id,
                )

            def _shipment_filter(r):
                if order_id and r["order_id"] != order_id:
                    return False
                if status and r["status"].lower() != status.lower():
                    return False
                return True

            raw_rows = await self._collect_paginated_rows(
                page_obj,
                min_cells=7,
                field_names=[
                    "shipment_id", "order_id", "tracking_number", "carrier",
                    "status", "dispatch_date", "expected_delivery",
                ],
                testid_selector=FlipkartSelectors.SHIPMENT_ROW_TESTID,
                dataset_field_map={"orderId": "order_id", "status": "status"},
                limit=limit,
                row_filter=_shipment_filter if (order_id or status) else None,
            )
            shipments: "list[Dict[str, Any]]" = list(raw_rows)

            _log_call("fetch_shipments", self.seller_id, start_time, success=True)
            return shipments
        except (NavigationError, SelectorError, ParsingError, SessionExpiredError, RateLimitError):
            raise
        except PlaywrightError as exc:
            wrapped = SelectorError(f"Flipkart fetch_shipments: unexpected page state while scraping: {exc}")
            _log_call("fetch_shipments", self.seller_id, start_time, success=False, error=wrapped)
            raise wrapped from exc
        except Exception as exc:
            _log_call("fetch_shipments", self.seller_id, start_time, success=False, error=exc)
            raise
        finally:
            await context.close()

    async def _update_inventory(self, browser: Browser, sku: str, quantity: int) -> Dict[str, Any]:
        start_time = time.monotonic()
        context = await browser.new_context()
        try:
            page_obj = await self._get_authenticated_page(context)

            async def _load():
                try:
                    await page_obj.goto(ROUTES["inventory"], wait_until="networkidle", timeout=20000)
                except PlaywrightError as exc:
                    raise NavigationError(f"Timed out loading Flipkart inventory: {exc}") from exc

            await _with_retries(_load, tool="update_inventory")
            if "login" in page_obj.url.lower():
                logger.info("Flipkart session expired mid-request for seller_id=%s (update_inventory) -- re-authenticating.", self.seller_id)
                await self._login(page_obj)
                await _with_retries(_load, tool="update_inventory")

            rows = await page_obj.query_selector_all(FlipkartSelectors.TABLE_ROW)
            for row in rows:
                cells = await row.query_selector_all(FlipkartSelectors.TABLE_CELL)
                if len(cells) < 5:
                    continue
                current_sku = (await cells[0].inner_text()).strip()
                if current_sku != sku:
                    continue

                qty_input = await row.query_selector(FlipkartSelectors.INVENTORY_QTY_INPUT)
                if qty_input is None:
                    raise SelectorError(f"Inventory quantity input not found for SKU '{sku}'.")
                await qty_input.fill(str(quantity))

                save_button = await row.query_selector(FlipkartSelectors.INVENTORY_SAVE_BUTTON)
                if save_button is None:
                    raise SelectorError(f"Save button not found for SKU '{sku}'.")
                await save_button.click()

                try:
                    await page_obj.wait_for_load_state("networkidle", timeout=10000)
                except PlaywrightError as exc:
                    raise NavigationError(f"Timed out saving inventory update for SKU '{sku}': {exc}") from exc

                result = {
                    "sku": sku, "updated_quantity": quantity, "status": "success",
                    "message": "Inventory updated successfully.", "marketplace": "flipkart",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                _log_call("update_inventory", self.seller_id, start_time, success=True)
                return result

            raise SelectorError(f"SKU '{sku}' not found in inventory.")
        except (NavigationError, SelectorError, ParsingError, SessionExpiredError):
            raise
        except PlaywrightError as exc:
            wrapped = SelectorError(f"Flipkart update_inventory: unexpected page state for SKU '{sku}': {exc}")
            _log_call("update_inventory", self.seller_id, start_time, success=False, error=wrapped)
            raise wrapped from exc
        except Exception as exc:
            _log_call("update_inventory", self.seller_id, start_time, success=False, error=exc)
            raise
        finally:
            await context.close()


# In-memory cookie cache shared by every connector instance in this
# process -- keyed by seller_id so multiple sellers' sessions never mix
# (Task 4 / Phase 4's isolation requirement, at the session-storage
# layer; each fetch_* call still gets its OWN BrowserContext too, so
# cookies/local-storage never leak between concurrent sellers even
# though they may share the one underlying Browser process).
_COOKIE_CACHE: "dict[str, list]" = {}


# ============================================================================
# Module-level facade -- matches flipkart_api_connector.py's public interface
# so flipkart_connector.py's switchboard can route to either with zero
# changes anywhere else.
# ============================================================================

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Only used as a type hint below. Importing this at runtime closes
    # a real circular import: flipkart_connector -> (this module) ->
    # session_store -> marketplace_connector -> flipkart_connector.
    # `from __future__ import annotations` (top of this file) means
    # the annotation on _connector() below is never evaluated at
    # runtime anyway, so this import is safe to skip entirely outside
    # type-checking -- no behavior change, cycle gone.
    from .session_store import MarketplaceSession


def _connector(session: MarketplaceSession) -> FlipkartPlaywrightConnector:
    credentials = {
        "seller_id": session.seller_id,
        **session.credentials,
    }
    return FlipkartPlaywrightConnector(credentials)


async def _run_and_cleanup(coro_factory: Callable[[Browser], Awaitable[T]]) -> T:
    """
    Every facade function below runs its connector call through THIS
    wrapper instead of building the coroutine upfront, so that:

      asyncio.run(_run_and_cleanup(
          lambda browser: _connector(session)._fetch_x(browser, ...)
      ))

    launches a Playwright + Browser pair scoped to exactly this call
    (`_launch_browser`), runs `coro_factory(browser)`, and closes that
    same pair (`_close_browser`) before `asyncio.run()` itself cancels
    tasks and closes the loop. Browser and Playwright live only as
    local variables in this function's stack -- nothing is cached at
    module or class level, so a concurrent call (its own OS thread,
    its own `asyncio.run()` loop) can never observe, reuse, or close
    this call's browser, and this call can never touch a concurrent
    call's browser either. Ownership never leaves this function.

    `finally` guarantees `_close_browser` runs on both the success path
    and every exception path (SessionExpiredError, NavigationError, an
    unexpected PlaywrightError escaping a fetch_* method, a failure
    during launch itself, etc.) -- cleanup must not depend on the call
    having succeeded.
    """
    start_time = time.monotonic()
    playwright, browser = await _launch_browser()
    try:
        return await coro_factory(browser)
    finally:
        await _close_browser(playwright, browser)
        logger.debug(
            "flipkart_connector: connector call finished duration_ms=%s",
            round((time.monotonic() - start_time) * 1000, 1),
        )


def fetch_products(session, page: int = 1, limit: int = 50, category: Optional[str] = None):
    return asyncio.run(_run_and_cleanup(
        lambda browser: _connector(session)._fetch_products(browser, page=page, limit=limit, category=category)
    ))


def fetch_orders(session, status: Optional[str] = None, start_date=None, end_date=None, page: int = 1, limit: int = 50):
    return asyncio.run(_run_and_cleanup(lambda browser: _connector(session)._fetch_orders(
        browser, status=status, start_date=start_date, end_date=end_date, page=page, limit=limit,
    )))


def fetch_shipments(session, order_id: Optional[str] = None, status: Optional[str] = None, page: int = 1, limit: int = 50):
    return asyncio.run(_run_and_cleanup(
        lambda browser: _connector(session)._fetch_shipments(browser, order_id=order_id, status=status, page=page, limit=limit)
    ))


def fetch_inventory(session, sku: Optional[str] = None, page: int = 1, limit: int = 50):
    return asyncio.run(_run_and_cleanup(
        lambda browser: _connector(session)._fetch_inventory(browser, sku=sku, page=page, limit=limit)
    ))


def update_inventory(session, sku: str, quantity: int):
    return asyncio.run(_run_and_cleanup(
        lambda browser: _connector(session)._update_inventory(browser, sku=sku, quantity=quantity)
    ))


def fetch_sales_metrics(session, start_date=None, end_date=None, timeframe="30d"):
    days = 30
    if isinstance(timeframe, str) and timeframe.endswith("d"):
        try:
            days = int(timeframe[:-1])
        except ValueError:
            pass
    return asyncio.run(_run_and_cleanup(
        lambda browser: _connector(session)._fetch_sales_metrics(browser, days)
    ))


def fetch_inventory_metrics(session):
    return asyncio.run(_run_and_cleanup(
        lambda browser: _connector(session)._fetch_inventory_metrics(browser)
    ))


def fetch_business_metrics(session, start_date=None, end_date=None, timeframe="30d"):
    days = 30
    if isinstance(timeframe, str) and timeframe.endswith("d"):
        try:
            days = int(timeframe[:-1])
        except ValueError:
            pass
    return asyncio.run(_run_and_cleanup(
        lambda browser: _connector(session)._fetch_business_metrics(browser, days)
    ))


def verify_connection(session):
    return asyncio.run(_run_and_cleanup(
        lambda browser: _connector(session)._verify_connection(browser)
    ))
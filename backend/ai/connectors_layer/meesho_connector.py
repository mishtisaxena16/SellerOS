"""
meesho_connector.py — Live Mode, Playwright-driven.

Meesho does not expose a public seller API, so per the SellerOS
architecture doc this connector automates the actual Supplier Panel
(supplier.meesho.com) with Playwright instead of reading sample JSON.

IMPORTANT — selectors need a validation pass:
The CSS selectors and page routes below (SELECTORS, ROUTES) are written
against the general shape of Meesho's Supplier Panel as of the last time
it was inspected, but I have no way to load an authenticated session of
the live panel from here to verify them pixel-for-pixel. Treat SELECTORS
as the single place to fix if Meesho ships a UI change — everything else
in this file should keep working.

Design:
- One authenticated BrowserContext is created per MarketplaceSession and
  reused across calls in the same request lifecycle (session.credentials
  can carry a `storage_state_path` so login doesn't have to happen on
  every call).
- Every public function returns list[dict] / dict — same contract the
  mock connectors use — so normalizer.py needs no changes to consume it.
- Playwright-specific failures are translated into the same custom
  exceptions connector.py already expects (AuthenticationError,
  RateLimitError, MarketplaceUnavailableError) so the dispatch layer
  doesn't need to know this connector uses a browser instead of HTTP.
"""
from __future__ import annotations

import re
import time
from contextlib import contextmanager
from typing import Any, Iterator, Optional

from playwright.sync_api import (
    sync_playwright,
    Page,
    BrowserContext,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)

from backend.ai.connectors_layer.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    RateLimitError,
    MarketplaceUnavailableError,
    SelectorError,
)

BASE_URL = "https://supplier.meesho.com"

ROUTES = {
    "login": f"{BASE_URL}/login",
    "catalog": f"{BASE_URL}/panel/catalog",
    "orders": f"{BASE_URL}/panel/orders",
    "shipments": f"{BASE_URL}/panel/orders/shipments",
    "inventory": f"{BASE_URL}/panel/inventory",
}

# Single source of truth for DOM hooks — update here if Meesho changes their UI.
# Now includes "shipment_row" alongside the original set — same
# unverified-selectors caveat in this file's module docstring applies
# to it too.
SELECTORS = {
    "login_username": "input[name='username']",
    "login_password": "input[name='password']",
    "login_submit": "button[type='submit']",
    "login_error": "[data-testid='login-error']",
    "rate_limit_banner": "text=/too many requests/i",
    "product_row": "[data-testid='product-row']",
    "order_row": "[data-testid='order-row']",
    "shipment_row": "[data-testid='shipment-row']",
    "inventory_row": "[data-testid='inventory-row']",
    "pagination_next": "[data-testid='pagination-next']:not([disabled])",
}

DEFAULT_TIMEOUT_MS = 15_000


# ---------------------------------------------------------------------------
# Session / browser lifecycle
# ---------------------------------------------------------------------------

@contextmanager
def _authenticated_page(session) -> Iterator[tuple[Page, BrowserContext]]:
    """
    Yields a (page, context) pair for the given MarketplaceSession —
    context is exposed too (Phase 5) so callers can hand it to
    _goto_with_session_recovery() for an in-flight re-login without a
    second _authenticated_page() call / second browser launch.

    Reuses saved storage_state (cookies/localStorage) when present in
    session.credentials["storage_state_path"] so we don't log in on every
    call — Meesho's panel session cookies are long-lived. Falls back to a
    fresh username/password login otherwise.

    NOTE: a restored storage_state is trusted as-is here and is NOT
    itself proof the session is still valid — Meesho may have expired it
    server-side since it was saved. That check happens per-request, in
    _goto_with_session_recovery(), once we actually navigate somewhere
    (see Phase 5 notes there) rather than here.
    """
    storage_state_path = session.credentials.get("storage_state_path")

    with sync_playwright() as pw:
        try:
            # Was outside this try — a missing/broken Chromium install
            # (e.g. `playwright install chromium` never run on a fresh
            # deployment) raised a raw, unmapped Playwright Error here
            # instead of something diagnosable. Same fix as
            # flipkart_playwright_connector.py's _authenticated_page.
            browser = pw.chromium.launch(headless=True)
        except Exception as exc:
            raise MarketplaceUnavailableError(
                f"Could not launch the browser for Meesho automation "
                f"(is `playwright install chromium` set up on this "
                f"deployment?): {exc}"
            ) from exc

        try:
            if storage_state_path:
                context = browser.new_context(storage_state=storage_state_path)
            else:
                context = browser.new_context()

            # Phase 8 — context.close() previously lived in a `finally`
            # that only wrapped the `yield page` statement, so a failure
            # in new_page()/set_default_timeout()/_login() (i.e. before
            # that inner try was reached) skipped it entirely and relied
            # on the outer `browser.close()` to cascade-close the leaked
            # context. That cascade does work in practice, but it means
            # context.close() itself was never guaranteed to run on
            # every path, which is exactly what Phase 8 asks to verify.
            # Moving the try up to right after context creation closes
            # that gap directly instead of depending on the cascade.
            try:
                page = context.new_page()
                page.set_default_timeout(DEFAULT_TIMEOUT_MS)

                if not storage_state_path:
                    _login(page, session, context)

                yield page, context
            finally:
                context.close()
        except PlaywrightTimeoutError as exc:
            raise MarketplaceUnavailableError(
                f"Meesho supplier panel did not respond in time: {exc}"
            ) from exc
        except PlaywrightError as exc:
            # Phase 7 — every fetch_*/update_inventory call runs entirely
            # inside the `yield page, context` block above, so this is
            # the single choke point for the whole module. Previously
            # only PlaywrightTimeoutError was caught here, so any other
            # raw Playwright failure (detached element, closed page,
            # aborted navigation, ...) escaped this connector unwrapped.
            # Mirrors flipkart_playwright_connector.py's SelectorError
            # wrapping ("unexpected page state"), collapsed to one place
            # since this connector has no per-operation try/except of
            # its own the way the async Flipkart one does.
            raise SelectorError(
                f"Meesho supplier panel: unexpected page state during automation: {exc}"
            ) from exc
        finally:
            browser.close()


def _login(page: Page, session, context: BrowserContext) -> None:
    username = session.credentials.get("username") or session.seller_id
    password = session.credentials.get("password")
    if not username or not password:
        raise InvalidCredentialsError(
            "Meesho live mode requires session.credentials['username'] and ['password'] "
            "(or a pre-saved storage_state_path) — none were provided."
        )

    page.goto(ROUTES["login"])
    page.fill(SELECTORS["login_username"], username)
    page.fill(SELECTORS["login_password"], password)
    page.click(SELECTORS["login_submit"])

    error_locator = page.locator(SELECTORS["login_error"])
    try:
        error_locator.wait_for(state="visible", timeout=3_000)
        message = error_locator.inner_text()
        raise InvalidCredentialsError(f"Meesho login rejected credentials: {message}")
    except PlaywrightTimeoutError:
        pass  # no error banner appeared -> treat as successful login

    page.wait_for_url(re.compile(r".*/panel(/|$)"), timeout=DEFAULT_TIMEOUT_MS)

    # Persist the session so future calls skip the login step entirely.
    save_path = session.credentials.get("storage_state_path")
    if save_path:
        context.storage_state(path=save_path)


def _goto_with_session_recovery(page: Page, session, context: BrowserContext, url: str) -> None:
    """
    Phase 5 — session validation.

    A restored storage_state is only ever validated for real the moment
    we actually navigate somewhere with it. Previously every fetch_*
    function called `page.goto(url)` directly and trusted whatever
    _authenticated_page handed it, so an expired stored session (or one
    that expired mid-lifecycle, between the initial login and this
    particular call) surfaced two steps later as a generic
    wait_for_selector timeout -> MarketplaceUnavailableError, with no
    attempt to re-login and no retry of the original request.

    Mirrors flipkart_playwright_connector.py's
    `if "login" in page_obj.url.lower(): self._login(...); retry` — same
    detection signal (Meesho's login route is under `/login`, matching
    ROUTES["login"]), same "retry the original request exactly once
    after a fresh login" behaviour.
    """
    page.goto(url)
    if "/login" in page.url.lower():
        _login(page, session, context)
        page.goto(url)


def _check_rate_limited(page: Page) -> None:
    if page.locator(SELECTORS["rate_limit_banner"]).count() > 0:
        raise RateLimitError("Meesho supplier panel reported a rate limit / throttling banner.")


def _extract_row_data(row) -> dict[str, Any]:
    """
    Pull structured data out of a panel row via its data-* attributes,
    which Meesho's frontend uses to hydrate the table — far more stable
    across visual redesigns than scraping rendered text.
    """
    raw_dataset = row.evaluate("el => ({...el.dataset})")
    return dict(raw_dataset)


def _paginate_rows(page: Page, row_selector: str, limit: int, skip_pages: int = 0) -> list[dict[str, Any]]:
    # skip_pages clicks through to the requested starting page using the
    # same Next-button mechanism proven out below, rather than guessing
    # at a `?page=N` URL convention Meesho's panel may not support —
    # every fetch_* function previously accepted a `page` argument and
    # silently ignored it (same bug as flipkart_playwright_connector.py,
    # confirmed the same way: running fetch_orders(page=1) vs
    # fetch_orders(page=2) against a mock panel returned identical rows).
    for _ in range(skip_pages):
        _check_rate_limited(page)
        next_button = page.locator(SELECTORS["pagination_next"])
        if next_button.count() == 0:
            break
        next_button.first.click()
        page.wait_for_load_state("networkidle")
        time.sleep(0.3)

    collected: list[dict[str, Any]] = []
    # Phase 6 — duplicate prevention. Rows are tracked by their full
    # data-* payload so that if a "Next" click doesn't actually advance
    # the panel (e.g. the real pagination_next selector's disabled
    # state doesn't match what SELECTORS assumes — genuinely unverified
    # without a live account, see module docstring), the same rows
    # don't get counted twice toward `limit`, and pagination stops
    # instead of looping forever re-collecting one page's rows.
    seen_rows: set[tuple[tuple[str, Any], ...]] = set()
    while len(collected) < limit:
        _check_rate_limited(page)
        rows = page.locator(row_selector)
        count = rows.count()
        page_had_new_row = False
        for i in range(count):
            row_data = _extract_row_data(rows.nth(i))
            signature = tuple(sorted(row_data.items()))
            if signature in seen_rows:
                continue
            seen_rows.add(signature)
            page_had_new_row = True
            collected.append(row_data)
            if len(collected) >= limit:
                break

        next_button = page.locator(SELECTORS["pagination_next"])
        if len(collected) >= limit or next_button.count() == 0:
            break
        if not page_had_new_row:
            # "Next" is present but the page produced nothing we
            # haven't already collected — treat this as pagination
            # having genuinely terminated rather than clicking forever.
            break
        next_button.first.click()
        page.wait_for_load_state("networkidle")
        time.sleep(0.3)  # be polite — avoid hammering panel pagination

    return collected


# ---------------------------------------------------------------------------
# Public fetch functions — same signature shape as the mock connectors
# ---------------------------------------------------------------------------

def fetch_products(session, page: int = 1, limit: int = 50, category: Optional[str] = None) -> list[dict[str, Any]]:
    with _authenticated_page(session) as (pg, ctx):
        url = ROUTES["catalog"]
        if category:
            url += f"?category={category}"
        _goto_with_session_recovery(pg, session, ctx, url)
        _check_rate_limited(pg)
        pg.wait_for_selector(SELECTORS["product_row"])
        return _paginate_rows(pg, SELECTORS["product_row"], limit=limit, skip_pages=page - 1)


def fetch_orders(
    session,
    status: Optional[str] = None,
    start_date=None,
    end_date=None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    with _authenticated_page(session) as (pg, ctx):
        url = ROUTES["orders"]
        params = []
        if status:
            params.append(f"status={status}")
        if start_date:
            params.append(f"from={start_date.date().isoformat()}")
        if end_date:
            params.append(f"to={end_date.date().isoformat()}")
        if params:
            url += "?" + "&".join(params)
        _goto_with_session_recovery(pg, session, ctx, url)
        _check_rate_limited(pg)
        pg.wait_for_selector(SELECTORS["order_row"])
        return _paginate_rows(pg, SELECTORS["order_row"], limit=limit, skip_pages=page - 1)


def fetch_shipments(
    session,
    order_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    with _authenticated_page(session) as (pg, ctx):
        url = ROUTES["shipments"]
        params = []
        if order_id:
            params.append(f"orderId={order_id}")
        if status:
            params.append(f"status={status}")
        if params:
            url += "?" + "&".join(params)
        _goto_with_session_recovery(pg, session, ctx, url)
        _check_rate_limited(pg)
        pg.wait_for_selector(SELECTORS["shipment_row"])
        return _paginate_rows(pg, SELECTORS["shipment_row"], limit=limit, skip_pages=page - 1)


def fetch_inventory(session, sku: Optional[str] = None, page: int = 1, limit: int = 50) -> list[dict[str, Any]]:
    with _authenticated_page(session) as (pg, ctx):
        url = ROUTES["inventory"]
        if sku:
            url += f"?sku={sku}"
        _goto_with_session_recovery(pg, session, ctx, url)
        _check_rate_limited(pg)
        pg.wait_for_selector(SELECTORS["inventory_row"])
        return _paginate_rows(pg, SELECTORS["inventory_row"], limit=limit, skip_pages=page - 1)


def update_inventory(session, sku: str, quantity: int):
    """
    Live inventory edits go through the panel's inline quantity editor.
    Returns a raw dict matching what connector.py expects to wrap into
    an InventoryUpdateResponse.
    """
    with _authenticated_page(session) as (pg, ctx):
        _goto_with_session_recovery(pg, session, ctx, f"{ROUTES['inventory']}?sku={sku}")
        row = pg.locator(SELECTORS["inventory_row"]).first
        row.wait_for(state="visible")

        qty_input = row.locator("input[data-testid='inventory-qty-input']")
        qty_input.fill(str(quantity))
        row.locator("button[data-testid='inventory-qty-save']").click()

        confirmation = row.locator("[data-testid='inventory-qty-saved']")
        try:
            confirmation.wait_for(state="visible", timeout=5_000)
            status = "success"
            message = "Inventory updated via Supplier Panel."
        except PlaywrightTimeoutError:
            status = "unknown"
            message = "Save was submitted but no confirmation banner appeared — verify manually."

        return {
            "sku": sku,
            "updated_quantity": quantity,
            "status": status,
            "message": message,
        }


def verify_connection(session):
    """
    verify_connection's whole contract is "always return a status dict,
    never raise" -- that's what lets the Executive Agent check
    connectivity before acting instead of having to catch exceptions.
    Flipkart's reference _verify_connection enforces this with a broad
    `except Exception`. This previously only caught
    (AuthenticationError, InvalidCredentialsError), so a
    MarketplaceUnavailableError (browser launch failure, panel timeout)
    or RateLimitError would escape as a raised exception instead of a
    graceful is_connected=False response -- a genuine behavioural
    inconsistency with the reference implementation, fixed here by
    widening the except clause to match.
    """
    try:
        with _authenticated_page(session) as (pg, ctx):
            _goto_with_session_recovery(pg, session, ctx, f"{BASE_URL}/panel")
            pg.wait_for_load_state("networkidle")
            return {
                "platform": "meesho",
                "seller_id": session.seller_id,
                "is_connected": True,
                "message": "Logged into Meesho Supplier Panel successfully.",
            }
    except Exception as exc:
        return {
            "platform": "meesho",
            "seller_id": session.seller_id,
            "is_connected": False,
            "message": str(exc),
        }

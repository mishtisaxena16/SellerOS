"""
flipkart_playwright_connector.py — Live Mode, Playwright-driven.

Same rationale as meesho_connector.py: until Flipkart's Seller API
access is approved, this automates the actual Seller Hub
(seller.flipkart.com) with Playwright instead of reading sample JSON.

IMPORTANT — selectors need a validation pass:
The CSS selectors and page routes below (SELECTORS, ROUTES) are written
against the general shape of Flipkart's Seller Hub, but I have no way
to load an authenticated session of the live panel from here to verify
them pixel-for-pixel — I don't have real Seller Hub access to inspect.
Treat SELECTORS as the single place to fix once you log in and check
the actual data-testid/class names Flipkart uses; everything else in
this file should keep working.

Design (identical contract to meesho_connector.py, on purpose — so
flipkart_connector.py's facade can route to either one without either
side needing to know):
- One authenticated BrowserContext is created per MarketplaceSession
  and reused across calls in the same request lifecycle
  (session.credentials can carry a `storage_state_path` so login
  doesn't have to happen on every call).
- Every public function returns list[dict] / dict — same contract
  flipkart_api_connector.py and the old mock connector use — so
  normalizer.py needs no changes to consume whichever one is active.
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
    TimeoutError as PlaywrightTimeoutError,
)

from backend.ai.connectors_layer.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    RateLimitError,
    MarketplaceUnavailableError,
)

BASE_URL = "https://seller.flipkart.com"

ROUTES = {
    "login": f"{BASE_URL}/login",
    "catalog": f"{BASE_URL}/dash/products",
    "orders": f"{BASE_URL}/dash/orders",
    "shipments": f"{BASE_URL}/dash/orders/shipments",
    "inventory": f"{BASE_URL}/dash/listings",
}

# Single source of truth for DOM hooks — update here if Flipkart changes their UI.
# UNVERIFIED against a live logged-in session — validate before relying on this
# in production, same caveat as meesho_connector.py's SELECTORS. This now
# includes "shipment_row" alongside the original set — same caveat applies:
# I have no authenticated Seller Hub session to confirm this against, so
# validate it the same pass you'd already planned for order_row/product_row.
SELECTORS = {
    "login_username": "input[name='loginId']",
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
def _authenticated_page(session) -> Iterator[Page]:
    """
    Yields a logged-in Page for the given MarketplaceSession.

    Reuses saved storage_state (cookies/localStorage) when present in
    session.credentials["storage_state_path"] so we don't log in on
    every call. Falls back to a fresh username/password login otherwise.
    """
    storage_state_path = session.credentials.get("storage_state_path")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            if storage_state_path:
                context = browser.new_context(storage_state=storage_state_path)
            else:
                context = browser.new_context()

            page = context.new_page()
            page.set_default_timeout(DEFAULT_TIMEOUT_MS)

            if not storage_state_path:
                _login(page, session, context)

            try:
                yield page
            finally:
                context.close()
        except PlaywrightTimeoutError as exc:
            raise MarketplaceUnavailableError(
                f"Flipkart Seller Hub did not respond in time: {exc}"
            ) from exc
        finally:
            browser.close()


def _login(page: Page, session, context: BrowserContext) -> None:
    username = session.credentials.get("username") or session.seller_id
    password = session.credentials.get("password")
    if not username or not password:
        raise InvalidCredentialsError(
            "Flipkart live mode requires session.credentials['username'] and "
            "['password'] (or a pre-saved storage_state_path) — none were provided."
        )

    page.goto(ROUTES["login"])
    page.fill(SELECTORS["login_username"], username)
    page.fill(SELECTORS["login_password"], password)
    page.click(SELECTORS["login_submit"])

    error_locator = page.locator(SELECTORS["login_error"])
    try:
        error_locator.wait_for(state="visible", timeout=3_000)
        message = error_locator.inner_text()
        raise InvalidCredentialsError(f"Flipkart login rejected credentials: {message}")
    except PlaywrightTimeoutError:
        pass  # no error banner appeared -> treat as successful login

    page.wait_for_url(re.compile(r".*/dash(/|$)"), timeout=DEFAULT_TIMEOUT_MS)

    # Persist the session so future calls skip the login step entirely.
    save_path = session.credentials.get("storage_state_path")
    if save_path:
        context.storage_state(path=save_path)


def _check_rate_limited(page: Page) -> None:
    if page.locator(SELECTORS["rate_limit_banner"]).count() > 0:
        raise RateLimitError("Flipkart Seller Hub reported a rate limit / throttling banner.")


def _extract_row_data(row) -> dict[str, Any]:
    """
    Pull structured data out of a panel row via its data-* attributes,
    which Flipkart's frontend likely uses to hydrate the table — far
    more stable across visual redesigns than scraping rendered text.
    Same approach as meesho_connector.py; adjust if Flipkart's Seller
    Hub turns out not to hydrate rows this way.
    """
    raw_dataset = row.evaluate("el => ({...el.dataset})")
    return dict(raw_dataset)


def _paginate_rows(page: Page, row_selector: str, limit: int) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    while len(collected) < limit:
        _check_rate_limited(page)
        rows = page.locator(row_selector)
        count = rows.count()
        for i in range(count):
            collected.append(_extract_row_data(rows.nth(i)))
            if len(collected) >= limit:
                break

        next_button = page.locator(SELECTORS["pagination_next"])
        if len(collected) >= limit or next_button.count() == 0:
            break
        next_button.first.click()
        page.wait_for_load_state("networkidle")
        time.sleep(0.3)  # be polite — avoid hammering panel pagination

    return collected


# ---------------------------------------------------------------------------
# Public fetch functions — same signature shape as flipkart_api_connector.py
# and the mock connector it replaces, so flipkart_connector.py's facade can
# swap between them with zero changes anywhere else.
# ---------------------------------------------------------------------------

def fetch_products(session, page: int = 1, limit: int = 50, category: Optional[str] = None) -> list[dict[str, Any]]:
    with _authenticated_page(session) as pg:
        url = ROUTES["catalog"]
        if category:
            url += f"?category={category}"
        pg.goto(url)
        pg.wait_for_selector(SELECTORS["product_row"])
        return _paginate_rows(pg, SELECTORS["product_row"], limit=limit)


def fetch_orders(
    session,
    status: Optional[str] = None,
    start_date=None,
    end_date=None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    with _authenticated_page(session) as pg:
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
        pg.goto(url)
        pg.wait_for_selector(SELECTORS["order_row"])
        return _paginate_rows(pg, SELECTORS["order_row"], limit=limit)


def fetch_shipments(
    session,
    order_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    with _authenticated_page(session) as pg:
        url = ROUTES["shipments"]
        params = []
        if order_id:
            params.append(f"orderId={order_id}")
        if status:
            params.append(f"status={status}")
        if params:
            url += "?" + "&".join(params)
        pg.goto(url)
        pg.wait_for_selector(SELECTORS["shipment_row"])
        return _paginate_rows(pg, SELECTORS["shipment_row"], limit=limit)


def fetch_inventory(session, sku: Optional[str] = None, page: int = 1, limit: int = 50) -> list[dict[str, Any]]:
    with _authenticated_page(session) as pg:
        url = ROUTES["inventory"]
        if sku:
            url += f"?sku={sku}"
        pg.goto(url)
        pg.wait_for_selector(SELECTORS["inventory_row"])
        return _paginate_rows(pg, SELECTORS["inventory_row"], limit=limit)


def update_inventory(session, sku: str, quantity: int):
    """
    Live inventory edits go through the panel's inline quantity editor.
    Returns a raw dict matching what marketplace_connector.py expects to
    wrap into an InventoryUpdateResponse.
    """
    with _authenticated_page(session) as pg:
        pg.goto(f"{ROUTES['inventory']}?sku={sku}")
        row = pg.locator(SELECTORS["inventory_row"]).first
        row.wait_for(state="visible")

        qty_input = row.locator("input[data-testid='inventory-qty-input']")
        qty_input.fill(str(quantity))
        row.locator("button[data-testid='inventory-qty-save']").click()

        confirmation = row.locator("[data-testid='inventory-qty-saved']")
        try:
            confirmation.wait_for(state="visible", timeout=5_000)
            status = "success"
            message = "Inventory updated via Flipkart Seller Hub."
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
    try:
        with _authenticated_page(session) as pg:
            pg.goto(f"{BASE_URL}/dash")
            pg.wait_for_load_state("networkidle")
            return {
                "platform": "flipkart",
                "seller_id": session.seller_id,
                "is_connected": True,
                "message": "Logged into Flipkart Seller Hub successfully (Playwright mode).",
            }
    except (AuthenticationError, InvalidCredentialsError) as exc:
        return {
            "platform": "flipkart",
            "seller_id": session.seller_id,
            "is_connected": False,
            "message": str(exc),
        }

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
    TimeoutError as PlaywrightTimeoutError,
)

from ai.connectors_layer.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    RateLimitError,
    MarketplaceUnavailableError,
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
def _authenticated_page(session) -> Iterator[Page]:
    """
    Yields a logged-in Page for the given MarketplaceSession.

    Reuses saved storage_state (cookies/localStorage) when present in
    session.credentials["storage_state_path"] so we don't log in on every
    call — Meesho's panel session cookies are long-lived. Falls back to a
    fresh username/password login otherwise.
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
                f"Meesho supplier panel did not respond in time: {exc}"
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
# Public fetch functions — same signature shape as the mock connectors
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
    Returns a raw dict matching what connector.py expects to wrap into
    an InventoryUpdateResponse.
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
    try:
        with _authenticated_page(session) as pg:
            pg.goto(f"{BASE_URL}/panel")
            pg.wait_for_load_state("networkidle")
            return {
                "platform": "meesho",
                "seller_id": session.seller_id,
                "is_connected": True,
                "message": "Logged into Meesho Supplier Panel successfully.",
            }
    except (AuthenticationError, InvalidCredentialsError) as exc:
        return {
            "platform": "meesho",
            "seller_id": session.seller_id,
            "is_connected": False,
            "message": str(exc),
        }

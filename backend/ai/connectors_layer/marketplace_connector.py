"""
marketplace_connector.py — the ONLY place that talks to Amazon /
Flipkart / Meesho over the network (SP-API, REST, or Playwright).

Design split:
- Fetching/Writing IS legitimately different per platform (different auth,
  different transport — Amazon SP-API vs Flipkart REST vs Meesho
  Playwright automation of the Supplier Panel). These actions are
  registered in fetcher/creator/updater maps.
- Normalizing is NOT platform-specific logic — that stays in
  normalizer.py's FIELD_MAPS tables, called from here.

So this file's job is: receive session/request -> hand off to platform
registry -> normalize raw payload -> return clean Pydantic response
models. Agents never see raw payloads, HTTP errors, or Playwright
exceptions directly.

Fixes applied vs. the previous draft:
1. Registry lookups no longer raise a bare KeyError when a platform
   isn't wired up for a given operation — `_dispatch` raises a clear
   NotImplementedError naming the platform + operation, which is what
   an agent's guardrail/error layer actually wants to catch.
2. Every dispatch is wrapped so unexpected exceptions from a connector
   (Playwright errors, requests errors, etc.) get translated into
   ConnectorError instead of leaking connector-specific exception types
   up to the agent layer. Our own custom exceptions
   (AuthenticationError/RateLimitError/...) pass through unchanged so
   callers can still distinguish them.
3. Meesho's fetchers/updaters/verifier are now wired to the real
   Playwright-backed connectors.meesho_connector module instead of
   being missing from the registries entirely (previously: KeyError
   at runtime for every Meesho call except get_products, which itself
   only raised NotImplementedError).
4. Amazon/Flipkart keep using their Mock Mode connectors for products
   for now — swap in real API-backed modules later with zero changes
   to this file.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field

from backend.ai.models.models import Product, Order, Inventory, Campaign, Shipment, Account
from backend.ai.connectors_layer.normalizer import (
    normalize_product,
    normalize_order,
    normalize_inventory,
    normalize_campaign,
    normalize_shipment,
    normalize_account,
)
from backend.ai.connectors_layer.exceptions import (
    ConnectorError,
    AuthenticationError,
    InvalidCredentialsError,
    RateLimitError,
    MarketplaceUnavailableError,
)

# ---------------------------------------------------------------------------
# 1. Custom Exceptions
#    (defined in exceptions.py — imported above, re-exported here so any
#    existing code doing `from marketplace_connector import ConnectorError`
#    keeps working unchanged)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 2. Domain & Response Models
# ---------------------------------------------------------------------------

class MarketplaceSession(BaseModel):
    """Encapsulates authentication state, region, and metadata for a marketplace connection."""
    platform: str
    seller_id: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    marketplace_id: Optional[str] = None
    region: Optional[str] = None
    credentials: dict[str, Any] = Field(default_factory=dict)


class ListingResponse(BaseModel):
    listing_id: str
    status: str
    message: str
    raw_response: Optional[dict[str, Any]] = None


class CampaignResponse(BaseModel):
    campaign_id: str
    status: str
    message: str
    raw_response: Optional[dict[str, Any]] = None


class InventoryUpdateResponse(BaseModel):
    sku: str
    updated_quantity: int
    status: str
    message: str


class ConnectionStatus(BaseModel):
    platform: str
    seller_id: str
    is_connected: bool
    latency_ms: Optional[float] = None
    message: str


# ---------------------------------------------------------------------------
# 3. Validation & Platform Registry Setup
# ---------------------------------------------------------------------------

SUPPORTED_PLATFORMS: set[str] = {"amazon", "flipkart", "meesho"}


def _validate_platform(platform: str) -> None:
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(
            f"Unsupported platform: '{platform}'. "
            f"Must be one of: {', '.join(sorted(SUPPORTED_PLATFORMS))}"
        )


def _dispatch(
    registry: dict[str, Callable[..., Any]],
    platform: str,
    operation: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Single choke point for every registry call.

    Validates the platform, verifies the requested operation is registered,
    and translates unexpected connector exceptions into ConnectorError.
    """

    _validate_platform(platform)

    fn = registry.get(platform)

    if fn is None:
        raise NotImplementedError(
            f"'{operation}' is not implemented for platform '{platform}' yet."
        )

    try:
        return fn(*args, **kwargs)

    except ConnectorError:
        raise

    except Exception as exc:
        raise ConnectorError(
            f"'{operation}' failed for platform '{platform}': {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# 4. Raw Fetchers, Creators, Updaters, Deleters
#    Branching by platform happens cleanly through dict maps.
# ---------------------------------------------------------------------------

from backend.ai.connectors_layer import amazon_connector, flipkart_connector, meesho_connector

PRODUCT_FETCHERS: dict[str, Callable[..., list[dict[str, Any]]]] = {
    "amazon": amazon_connector.fetch_products,
    "flipkart": flipkart_connector.fetch_products,
    "meesho": meesho_connector.fetch_products,
}

LISTING_CREATORS: dict[str, Callable[..., ListingResponse]] = {}
LISTING_PUBLISHERS: dict[str, Callable[..., ListingResponse]] = {}
LISTING_UPDATERS: dict[str, Callable[..., ListingResponse]] = {}
LISTING_DELETERS: dict[str, Callable[..., ListingResponse]] = {}

INVENTORY_FETCHERS: dict[str, Callable[..., list[dict[str, Any]]]] = {
    "meesho": meesho_connector.fetch_inventory,
    "flipkart": flipkart_connector.fetch_inventory,
    "amazon": amazon_connector.fetch_inventory,
}
INVENTORY_UPDATERS: dict[str, Callable[..., dict[str, Any]]] = {
    "meesho": meesho_connector.update_inventory,
    "flipkart": flipkart_connector.update_inventory,
    "amazon": amazon_connector.update_inventory,
}

ORDER_FETCHERS: dict[str, Callable[..., list[dict[str, Any]]]] = {
    "meesho": meesho_connector.fetch_orders,
    "flipkart": flipkart_connector.fetch_orders,
    "amazon": amazon_connector.fetch_orders,
}
SINGLE_ORDER_FETCHERS: dict[str, Callable[..., dict[str, Any]]] = {
    "amazon": amazon_connector.fetch_order,
}
SHIPMENT_FETCHERS: dict[str, Callable[..., list[dict[str, Any]]]] = {
    "amazon": amazon_connector.fetch_shipments,
    "flipkart": flipkart_connector.fetch_shipments,
    "meesho": meesho_connector.fetch_shipments,
}

CAMPAIGN_FETCHERS: dict[str, Callable[..., list[dict[str, Any]]]] = {}
CAMPAIGN_CREATORS: dict[str, Callable[..., CampaignResponse]] = {}
CAMPAIGN_DELETERS: dict[str, Callable[..., CampaignResponse]] = {}

def _meesho_sales_metrics_from_orders(session: MarketplaceSession, start_date=None, end_date=None, timeframe: str = "30d") -> dict[str, Any]:
    """
    BLOCKER FIX (not a Flipkart change): meesho_connector.py defines no
    fetch_sales_metrics at all, which crashed marketplace_connector.py
    at import time for every platform, Flipkart included, since this
    module's registries are built at import time. Derives revenue from
    Meesho's own already-working get_orders() instead of adding a new,
    unverified Playwright scrape -- same approach already used for
    Flipkart/Meesho in the prior checkpoint's marketplace_connector.py.
    """
    orders = get_orders(session, start_date=start_date, end_date=end_date, limit=1000)
    total_revenue = sum(o.total_amount or 0 for o in orders)
    return {
        "platform": session.platform,
        "timeframe": timeframe,
        "total_orders": len(orders),
        "total_revenue": total_revenue,
        "average_order_value": round(total_revenue / len(orders), 2) if orders else 0.0,
        "currency": orders[0].currency if orders else "INR",
        "note": "Computed from live meesho orders data -- no analytics/reports panel connector exists for this platform yet.",
    }


def _meesho_business_metrics_from_orders(session: MarketplaceSession, start_date=None, end_date=None, timeframe: str = "30d") -> dict[str, Any]:
    orders = get_orders(session, start_date=start_date, end_date=end_date, limit=1000)
    shipped = sum(1 for o in orders if o.status.lower() == "shipped")
    pending = sum(1 for o in orders if o.status.lower() in ("pending", "unshipped"))
    return {
        "platform": session.platform,
        "timeframe": timeframe,
        "shipped_orders": shipped,
        "pending_orders": pending,
        "currency": "INR",
        "note": "Computed from live meesho orders data -- no analytics/reports panel connector exists for this platform yet.",
    }


def _meesho_inventory_metrics_from_inventory(session: MarketplaceSession) -> dict[str, Any]:
    """
    BLOCKER FIX (Phase 2): meesho_connector.py defines no
    fetch_inventory_metrics, and neither does amazon_connector.py --
    only Flipkart's Playwright/API connectors implement it, and even
    marketplace_connector.py itself had no registry or public facade
    function for it at all (get_inventory_metrics() didn't exist for
    ANY platform). Rather than guess at Meesho panel selectors for an
    inventory-summary widget (which would violate the "never invent
    selectors" rule), this derives the numbers from Meesho's own
    already-working get_inventory() -- same approach already used above
    for _meesho_sales_metrics_from_orders / _meesho_business_metrics_from_orders.
    """
    inventory = get_inventory(session, limit=1000)
    return {
        "platform": session.platform,
        "total_skus": len(inventory),
        "total_available_quantity": sum(i.available_quantity or 0 for i in inventory),
        "out_of_stock_skus": sum(1 for i in inventory if not i.available_quantity),
        "note": "Computed from live meesho inventory data -- no inventory-summary panel connector exists for this platform yet.",
    }


INVENTORY_METRICS_FETCHERS: dict[str, Callable[..., dict[str, Any]]] = {
    "flipkart": flipkart_connector.fetch_inventory_metrics,
    "meesho": _meesho_inventory_metrics_from_inventory,
    # amazon intentionally omitted: amazon_connector.py has no
    # fetch_inventory_metrics implementation. _dispatch() already
    # reports this as NotImplementedError naming the platform + op,
    # same as every other genuinely-unimplemented registry gap in this
    # file -- no new behaviour invented for Amazon.
}

SALES_METRICS_FETCHERS: dict[str, Callable[..., dict[str, Any]]] = {
    "amazon": amazon_connector.fetch_sales_metrics,
    "flipkart": flipkart_connector.fetch_sales_metrics,
    "meesho": _meesho_sales_metrics_from_orders,
}

BUSINESS_METRICS_FETCHERS: dict[str, Callable[..., dict[str, Any]]] = {
    "amazon": amazon_connector.fetch_business_metrics,
    "flipkart": flipkart_connector.fetch_business_metrics,
    "meesho": _meesho_business_metrics_from_orders,
}

CONNECTION_VERIFIERS: dict[str, Callable[..., dict[str, Any]]] = {
    "amazon": amazon_connector.verify_connection,
    "flipkart": flipkart_connector.verify_connection,
    "meesho": meesho_connector.verify_connection,
}
ACCOUNT_FETCHERS: dict[str, Callable[..., dict[str, Any]]] = {}


# ---------------------------------------------------------------------------
# 5. Public Business API — Clean interface exposed to SellerOS Agents
# ---------------------------------------------------------------------------

# ===========================================================================
# Module: Product Studio
# ===========================================================================

def get_products(
    session: MarketplaceSession,
    page: int = 1,
    limit: int = 50,
    category: Optional[str] = None
) -> list[Product]:
    raw_products = _dispatch(PRODUCT_FETCHERS, session.platform, "get_products", session, page=page, limit=limit, category=category)
    return [normalize_product(session.platform, raw) for raw in raw_products]


def create_listing(session: MarketplaceSession, product_data: dict[str, Any]) -> ListingResponse:
    return _dispatch(LISTING_CREATORS, session.platform, "create_listing", session, product_data)


def publish_listing(session: MarketplaceSession, listing_id: str) -> ListingResponse:
    return _dispatch(LISTING_PUBLISHERS, session.platform, "publish_listing", session, listing_id)


def update_listing(session: MarketplaceSession, listing_id: str, update_data: dict[str, Any]) -> ListingResponse:
    return _dispatch(LISTING_UPDATERS, session.platform, "update_listing", session, listing_id, update_data)


def delete_listing(session: MarketplaceSession, listing_id: str) -> ListingResponse:
    return _dispatch(LISTING_DELETERS, session.platform, "delete_listing", session, listing_id)


# ===========================================================================
# Module: Inventory Agent
# ===========================================================================

def get_inventory(
    session: MarketplaceSession,
    sku: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> list[Inventory]:
    raw_inventory = _dispatch(INVENTORY_FETCHERS, session.platform, "get_inventory", session, sku=sku, page=page, limit=limit)
    return [normalize_inventory(session.platform, raw) for raw in raw_inventory]


def update_inventory(session: MarketplaceSession, sku: str, quantity: int) -> InventoryUpdateResponse:
    result = _dispatch(INVENTORY_UPDATERS, session.platform, "update_inventory", session, sku, quantity)
    return InventoryUpdateResponse(**result)


# ===========================================================================
# Module: Order Agent (Includes Order & Shipment Domain Operations)
# ===========================================================================

def get_orders(
    session: MarketplaceSession,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    limit: int = 50
) -> list[Order]:
    raw_orders = _dispatch(
        ORDER_FETCHERS, session.platform, "get_orders", session,
        status=status, start_date=start_date, end_date=end_date, page=page, limit=limit,
    )
    return [normalize_order(session.platform, raw) for raw in raw_orders]


def get_order(session: MarketplaceSession, order_id: str) -> Order:
    raw_order = _dispatch(SINGLE_ORDER_FETCHERS, session.platform, "get_order", session, order_id)
    return normalize_order(session.platform, raw_order)


def get_shipments(
    session: MarketplaceSession,
    order_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> list[Shipment]:
    raw_shipments = _dispatch(
        SHIPMENT_FETCHERS, session.platform, "get_shipments", session,
        order_id=order_id, status=status, page=page, limit=limit,
    )
    return [normalize_shipment(session.platform, raw) for raw in raw_shipments]


# ===========================================================================
# Module: Ads Agent
# ===========================================================================

def get_campaigns(
    session: MarketplaceSession,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> list[Campaign]:
    raw_campaigns = _dispatch(CAMPAIGN_FETCHERS, session.platform, "get_campaigns", session, status=status, page=page, limit=limit)
    return [normalize_campaign(session.platform, raw) for raw in raw_campaigns]


def create_campaign(session: MarketplaceSession, campaign_data: dict[str, Any]) -> CampaignResponse:
    return _dispatch(CAMPAIGN_CREATORS, session.platform, "create_campaign", session, campaign_data)


def delete_campaign(session: MarketplaceSession, campaign_id: str) -> CampaignResponse:
    return _dispatch(CAMPAIGN_DELETERS, session.platform, "delete_campaign", session, campaign_id)


# ===========================================================================
# Module: Analytics Agent
# ===========================================================================

def get_sales_metrics(
    session: MarketplaceSession,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    timeframe: str = "30d"
) -> dict[str, Any]:
    return _dispatch(SALES_METRICS_FETCHERS, session.platform, "get_sales_metrics", session, start_date=start_date, end_date=end_date, timeframe=timeframe)


def get_business_metrics(
    session: MarketplaceSession,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    timeframe: str = "30d"
) -> dict[str, Any]:
    return _dispatch(BUSINESS_METRICS_FETCHERS, session.platform, "get_business_metrics", session, start_date=start_date, end_date=end_date, timeframe=timeframe)


def get_inventory_metrics(session: MarketplaceSession) -> dict[str, Any]:
    return _dispatch(INVENTORY_METRICS_FETCHERS, session.platform, "get_inventory_metrics", session)


# ===========================================================================
# Module: Executive Agent
# ===========================================================================

def verify_connection(session: MarketplaceSession) -> ConnectionStatus:
    result = _dispatch(CONNECTION_VERIFIERS, session.platform, "verify_connection", session)
    return ConnectionStatus(**result)


def get_account(session: MarketplaceSession) -> Account:
    raw_account = _dispatch(ACCOUNT_FETCHERS, session.platform, "get_account", session)
    return normalize_account(session.platform, raw_account)

"""
amazon_connector.py — Mock Mode.

Per the SellerOS Connector Development Strategy: this reads sample JSON
so the rest of the team can build against a stable interface while the
real SP-API integration (OAuth + LWA token exchange + SP-API calls) is
wired up. Swapping to Live Mode later means rewriting the bodies of
these functions only — connector.py and everything above it never
changes.
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample_data" / "amazon"


def _load_sample(filename: str) -> list[dict[str, Any]]:
    path = SAMPLE_DATA_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_products(session, page: int = 1, limit: int = 50, category: Optional[str] = None) -> list[dict[str, Any]]:
    products = _load_sample("products.json")
    if category:
        products = [p for p in products if p.get("category") == category]
    start = (page - 1) * limit
    return products[start:start + limit]


def fetch_inventory(session, sku: Optional[str] = None, page: int = 1, limit: int = 50) -> list[dict[str, Any]]:
    inventory = _load_sample("inventory.json")
    if sku:
        inventory = [i for i in inventory if i.get("sellerSku") == sku]
    start = (page - 1) * limit
    return inventory[start:start + limit]


def update_inventory(session, sku: str, quantity: int) -> dict[str, Any]:
    # Mock Mode: no real SP-API "Update Inventory" feed call, and
    # inventory.json isn't rewritten to disk (same "don't fake
    # persistence" stance as meesho/flipkart's mock predecessors) —
    # this just confirms the shape InventoryUpdateResponse expects,
    # matching what a real SP-API feed submission would report back
    # (accepted, not yet necessarily reflected — SP-API inventory
    # feeds are asynchronous).
    return {
        "sku": sku,
        "updated_quantity": quantity,
        "status": "success",
        "message": f"Inventory update for SKU {sku} accepted (Mock Mode — not persisted).",
    }


def _has_live_credentials(session) -> bool:
    return bool((session.credentials or {}).get("refresh_token") or getattr(session, "refresh_token", None))


def _mock_fetch_orders(
    status: Optional[str] = None,
    start_date=None,
    end_date=None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    orders = _load_sample("orders.json")
    if status:
        orders = [
            o for o in orders
            if str(o.get("fulfillment", {}).get("fulfillmentStatus", "")).lower() == status.lower()
        ]
    start = (page - 1) * limit
    return orders[start:start + limit]


def _live_fetch_orders(
    session,
    status: Optional[str] = None,
    start_date=None,
    end_date=None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Live Mode: backed by SP-API's Orders v2026-01-01 searchOrders,
    transparently paginated via amazon_sdk.orders.iterate_orders.

    Performance note: SP-API's pagination is token-based, not
    page-number-based -- there is no way to "skip to page 3" without
    having already walked pages 1-2. `page` here is therefore honoured
    by sequentially iterating and discarding the first
    (page - 1) * limit orders, same as the Mock Mode slicing above does
    logically, just at real API-call cost. Callers doing bulk sync
    should prefer walking pages 1, 2, 3, ... in order (or migrate to a
    cursor-based caller) rather than jumping to a high page number.
    """
    from backend.ai.connectors_layer.amazon_sdk import orders as amazon_orders

    # SP-API requires exactly one of createdAfter/lastUpdatedAfter.
    # start_date (if given) drives a createdAfter sync; with no
    # start_date at all we still need *something* in that slot, so we
    # fall back to lastUpdatedAfter="the beginning of what SP-API will
    # return" (epoch) rather than guessing a created-date window --
    # this returns "every order this seller has that Amazon's Orders
    # API will serve" (bounded by Amazon's own 2-year order-history
    # limit, per the Orders API overview docs) instead of silently
    # narrowing results the caller didn't ask to narrow.
    kwargs: dict[str, Any] = {}
    if start_date is not None:
        kwargs["created_after"] = start_date
        if end_date is not None:
            kwargs["created_before"] = end_date
    else:
        kwargs["last_updated_after"] = datetime(1970, 1, 1)

    if status:
        kwargs["fulfillment_statuses"] = [status.upper()]

    collected: list[dict[str, Any]] = []
    skip = (page - 1) * limit
    for raw_order in amazon_orders.iterate_orders(session, **kwargs):
        if skip > 0:
            skip -= 1
            continue
        collected.append(raw_order)
        if len(collected) >= limit:
            break
    return collected


def fetch_orders(
    session,
    status: Optional[str] = None,
    start_date=None,
    end_date=None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if _has_live_credentials(session):
        return _live_fetch_orders(session, status=status, start_date=start_date, end_date=end_date, page=page, limit=limit)
    return _mock_fetch_orders(status=status, start_date=start_date, end_date=end_date, page=page, limit=limit)


def fetch_order(session, order_id: str) -> dict[str, Any]:
    """
    Single-order fetch, wired to marketplace_connector.SINGLE_ORDER_FETCHERS
    this phase (previously empty for every platform).
    """
    if _has_live_credentials(session):
        from backend.ai.connectors_layer.amazon_sdk import orders as amazon_orders

        return amazon_orders.get_order(session, order_id)

    for order in _load_sample("orders.json"):
        if order.get("orderId") == order_id:
            return order
    from backend.ai.connectors_layer.exceptions import ConnectorError

    raise ConnectorError(f"No such order '{order_id}' in Mock Mode sample data (sample_data/amazon/orders.json).")


def fetch_shipments(
    session,
    order_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    # Mock Mode: sample_data/amazon/shipments.json deliberately only
    # covers the "Shipped" order from orders.json, not the "Unshipped"
    # one — a real seller's shipment feed wouldn't have a shipment
    # record for an order that hasn't shipped yet either. That gap is
    # what lets OrdersAgent's "flag anything that looks stuck" logic
    # (agent_layer/operations/orders_agent.py) actually have something
    # to flag against real (if sample) data, instead of every order
    # trivially having a matching shipment.
    shipments = _load_sample("shipments.json")
    if order_id:
        shipments = [s for s in shipments if s.get("order_id") == order_id]
    if status:
        shipments = [s for s in shipments if s.get("status", "").lower() == status.lower()]
    start = (page - 1) * limit
    return shipments[start:start + limit]


# TODO (Live Mode): replace with real SP-API calls using session.access_token,
# session.marketplace_id, session.region. Keep the return shape identical
# (list[dict]) so normalizer.py's PRODUCT_FIELD_MAPS["amazon"] keeps working
# unchanged. fetch_shipments should call SP-API's Shipping/Tracking API
# (or the Orders API's getOrderItems shipment fields, depending on which
# scope you're granted) instead of reading shipments.json.


def fetch_sales_metrics(session, start_date=None, end_date=None, timeframe: str = "30d") -> dict[str, Any]:
    # Derived from orders.json rather than a second, disconnected set of
    # numbers, so this stays internally consistent with fetch_orders.
    # Field paths updated this phase to match orders.json's move to the
    # Orders API v2026-01-01 shape (proceeds.grandTotal.amount, was
    # OrderTotal.Amount in v0).
    orders = _load_sample("orders.json")
    total_revenue = sum(float(o.get("proceeds", {}).get("grandTotal", {}).get("amount") or 0) for o in orders)
    return {
        "platform": "amazon",
        "timeframe": timeframe,
        "total_orders": len(orders),
        "total_revenue": total_revenue,
        "average_order_value": round(total_revenue / len(orders), 2) if orders else 0.0,
        "currency": "INR",
        "note": "Mock Mode -- computed from sample_data/amazon/orders.json, not a live SP-API report.",
    }


def fetch_business_metrics(session, start_date=None, end_date=None, timeframe: str = "30d") -> dict[str, Any]:
    orders = _load_sample("orders.json")
    statuses = [str(o.get("fulfillment", {}).get("fulfillmentStatus", "")).lower() for o in orders]
    shipped = statuses.count("shipped")
    pending = sum(1 for s in statuses if s in ("pending", "unshipped"))
    return {
        "platform": "amazon",
        "timeframe": timeframe,
        "shipped_orders": shipped,
        "pending_orders": pending,
        "currency": "INR",
        "note": "Mock Mode -- computed from sample_data/amazon/orders.json, not a live SP-API report.",
    }


def verify_connection(session) -> dict[str, Any]:
    """
    Mock Mode (no OAuth completed yet -- session has no refresh_token):
    reports "connected" unconditionally, same as before, since fetch_*
    here always succeeds off local sample data.

    Live Mode (seller completed the Connect Amazon OAuth flow --
    backend/service/amazon_auth_service.py): calls the real SP-API
    Marketplace Participation API (getMarketplaceParticipations) via
    amazon_sdk/client.py. Response shape is unchanged either way --
    marketplace_connector.py's verify_connection() constructs the same
    ConnectionStatus(**result) from this dict regardless of which path
    ran, so nothing above this function needs to know or care which
    mode it's in.
    """
    refresh_token = (session.credentials or {}).get("refresh_token") or getattr(session, "refresh_token", None)
    if not refresh_token:
        return {
            "platform": "amazon",
            "seller_id": session.seller_id,
            "is_connected": True,
            "latency_ms": 0.0,
            "message": "Mock Mode -- reading local sample_data/amazon/*.json, no live SP-API connection to verify.",
        }

    # Imported here rather than at module top: keeps amazon_connector.py
    # (Mock Mode, zero external deps) importable with no `requests`
    # dependency at all for every caller that never actually reaches
    # this branch -- only sellers who completed OAuth pull in amazon_sdk.
    from backend.ai.connectors_layer.amazon_sdk import client as amazon_client

    started = time.monotonic()
    data = amazon_client.call(session, "GET", "/sellers/v1/marketplaceParticipations")
    latency_ms = (time.monotonic() - started) * 1000

    participations = data.get("payload", []) if isinstance(data, dict) else []
    return {
        "platform": "amazon",
        "seller_id": session.seller_id,
        "is_connected": True,
        "latency_ms": round(latency_ms, 1),
        "message": f"Connected -- {len(participations)} marketplace participation(s) found.",
    }

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


def fetch_orders(
    session,
    status: Optional[str] = None,
    start_date=None,
    end_date=None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    orders = _load_sample("orders.json")
    if status:
        orders = [o for o in orders if o.get("OrderStatus", "").lower() == status.lower()]
    start = (page - 1) * limit
    return orders[start:start + limit]


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

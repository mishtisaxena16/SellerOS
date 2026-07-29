"""
normalizer.py — turns raw, platform-shaped payloads into the shared
Product / Order / Inventory / Campaign / Shipment / Account models.

This is where platform differences in field NAMING get absorbed.
Transport differences (how you fetched the data) stay in the connectors;
shape differences (what the fields are called) stay here.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.ai.models.models import Product, Order, OrderItem, Inventory, Campaign, Shipment, Account

# ---------------------------------------------------------------------------
# Field maps: platform -> our_field -> source_field (dot-path supported)
# ---------------------------------------------------------------------------

PRODUCT_FIELD_MAPS: dict[str, dict[str, str]] = {
    "amazon": {
        "sku": "sellerSku",
        "listing_id": "asin",
        "title": "itemName",
        "price": "listingPrice.amount",
        "stock_quantity": "quantity",
        "status": "status",
    },
    "flipkart": {
        "sku": "skuId",
        "listing_id": "listingId",
        "title": "productTitle",
        "price": "sellingPrice",
        "stock_quantity": "availableUnits",
        "status": "listingStatus",
    },
    "meesho": {
        "sku": "sku",
        "listing_id": "product_id",
        "title": "name",
        "price": "selling_price",
        "mrp": "mrp",
        "stock_quantity": "quantity",
        "status": "status",
        "category": "category",
    },
}

ORDER_FIELD_MAPS: dict[str, dict[str, str]] = {
    "meesho": {
        "order_id": "order_id",
        "status": "order_status",
        "total_amount": "total_amount",
        "order_date": "order_date",
        "customer_state": "customer_state",
    },
    "amazon": {
        # v2026-01-01 field paths (verified against the official Orders
        # API Migration Guide's "Order attribute mapping" table -- v0's
        # flat AmazonOrderId/OrderStatus/OrderTotal.Amount/PurchaseDate
        # became nested objects in the new API). orderId/createdTime/
        # fulfillment/salesChannel are always present in a searchOrders
        # or getOrder response; proceeds.grandTotal requires
        # includedData=PROCEEDS, which config.DEFAULT_ORDERS_INCLUDED_DATA
        # always requests.
        "order_id": "orderId",
        "status": "fulfillment.fulfillmentStatus",
        "total_amount": "proceeds.grandTotal.amount",
        "order_date": "createdTime",
        "last_updated_date": "lastUpdatedTime",
        "fulfillment_channel": "fulfillment.fulfilledBy",
        "marketplace": "salesChannel.marketplaceName",
        "shipping_service_level": "fulfillment.fulfillmentServiceLevel",
    },
    "flipkart": {
        "order_id": "orderId",
        "status": "status",
        "total_amount": "orderValue",
        "order_date": "orderDate",
    },
}

INVENTORY_FIELD_MAPS: dict[str, dict[str, str]] = {
    "meesho": {
        "sku": "sku",
        "available_quantity": "available_quantity",
        "warehouse": "warehouse_name",
    },
    "amazon": {
        "sku": "sellerSku",
        "available_quantity": "fulfillableQuantity",
    },
    "flipkart": {
        "sku": "skuId",
        "available_quantity": "availableUnits",
    },
}


def _dig(payload: dict[str, Any], dot_path: str) -> Any:
    """Resolve a dotted path like 'listingPrice.amount' against a nested dict."""
    value: Any = payload
    for part in dot_path.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def _map_fields(platform: str, field_map_table: dict[str, dict[str, str]], raw: dict[str, Any]) -> dict[str, Any]:
    field_map = field_map_table.get(platform, {})
    mapped: dict[str, Any] = {}
    for our_field, source_path in field_map.items():
        mapped[our_field] = _dig(raw, source_path)
    return mapped


def _parse_date(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Public normalize_* functions used by connector.py
# ---------------------------------------------------------------------------

def normalize_product(platform: str, raw: dict[str, Any]) -> Product:
    mapped = _map_fields(platform, PRODUCT_FIELD_MAPS, raw)
    return Product(
        platform=platform,
        sku=str(mapped.get("sku") or ""),
        listing_id=mapped.get("listing_id"),
        title=mapped.get("title") or "",
        price=mapped.get("price"),
        mrp=mapped.get("mrp"),
        category=mapped.get("category"),
        stock_quantity=mapped.get("stock_quantity"),
        status=mapped.get("status"),
        raw=raw,
    )


def _extract_amazon_order_items(raw: dict[str, Any]) -> list[OrderItem]:
    """
    Amazon (v2026-01-01) nests items under orderItems[].product.* rather
    than the flat {sku, quantity, unit_price} shape meesho/flipkart use
    -- see the Migration Guide's OrderItem attribute table: ASIN ->
    orderItems[].product.asin, SellerSKU -> orderItems[].product.sellerSku,
    Title -> orderItems[].product.title, QuantityOrdered ->
    orderItems[].quantityOrdered. ItemPrice moved into a
    proceeds.breakdowns[] structure (requires includedData=PROCEEDS,
    type == "ITEM") rather than a single flat field -- extracted here
    defensively (None if PROCEEDS wasn't requested/present) rather than
    raising, since unit_price is optional on OrderItem.
    """
    items: list[OrderItem] = []
    for item in raw.get("orderItems") or []:
        if not isinstance(item, dict):
            continue
        product = item.get("product") or {}
        unit_price = None
        proceeds = item.get("proceeds") or {}
        for breakdown in proceeds.get("breakdowns") or []:
            if isinstance(breakdown, dict) and breakdown.get("type") == "ITEM":
                unit_price = _dig(breakdown, "subtotal.amount")
                break
        items.append(
            OrderItem(
                sku=str(product.get("sellerSku") or ""),
                quantity=int(item.get("quantityOrdered") or 0),
                unit_price=float(unit_price) if unit_price is not None else None,
                order_item_id=item.get("orderItemId"),
                asin=product.get("asin"),
                title=product.get("title"),
            )
        )
    return items


def normalize_order(platform: str, raw: dict[str, Any]) -> Order:
    mapped = _map_fields(platform, ORDER_FIELD_MAPS, raw)

    if platform == "amazon":
        items = _extract_amazon_order_items(raw)
    else:
        items_raw = raw.get("items") or raw.get("order_items") or []
        items = [
            OrderItem(
                sku=str(item.get("sku", "")),
                quantity=int(item.get("quantity", 0)),
                unit_price=item.get("unit_price") or item.get("price"),
            )
            for item in items_raw
            if isinstance(item, dict)
        ]

    order_kwargs: dict[str, Any] = dict(
        platform=platform,
        order_id=str(mapped.get("order_id") or ""),
        status=str(mapped.get("status") or "unknown"),
        items=items,
        total_amount=mapped.get("total_amount"),
        order_date=_parse_date(mapped.get("order_date")),
        customer_state=mapped.get("customer_state"),
        raw=raw,
    )

    if platform == "amazon":
        currency = _dig(raw, "proceeds.grandTotal.currencyCode")
        order_kwargs.update(
            last_updated_date=_parse_date(mapped.get("last_updated_date")),
            fulfillment_channel=mapped.get("fulfillment_channel"),
            marketplace=mapped.get("marketplace"),
            item_count=len(items),
            shipping_service_level=mapped.get("shipping_service_level"),
        )
        if currency:
            order_kwargs["currency"] = currency

    return Order(**order_kwargs)


def normalize_inventory(platform: str, raw: dict[str, Any]) -> Inventory:
    mapped = _map_fields(platform, INVENTORY_FIELD_MAPS, raw)
    return Inventory(
        platform=platform,
        sku=str(mapped.get("sku") or ""),
        available_quantity=int(mapped.get("available_quantity") or 0),
        warehouse=mapped.get("warehouse"),
        raw=raw,
    )


def normalize_campaign(platform: str, raw: dict[str, Any]) -> Campaign:
    return Campaign(
        platform=platform,
        campaign_id=str(raw.get("campaign_id") or raw.get("campaignId") or ""),
        name=str(raw.get("name") or raw.get("campaign_name") or ""),
        status=str(raw.get("status") or "unknown"),
        budget=raw.get("budget"),
        spend=raw.get("spend"),
        raw=raw,
    )


def normalize_shipment(platform: str, raw: dict[str, Any]) -> Shipment:
    return Shipment(
        platform=platform,
        shipment_id=str(raw.get("shipment_id") or raw.get("shipmentId") or ""),
        order_id=str(raw.get("order_id") or raw.get("orderId") or ""),
        status=str(raw.get("status") or "unknown"),
        carrier=raw.get("carrier"),
        tracking_number=raw.get("tracking_number"),
        raw=raw,
    )


def normalize_account(platform: str, raw: dict[str, Any]) -> Account:
    return Account(
        platform=platform,
        seller_id=str(raw.get("seller_id") or raw.get("sellerId") or ""),
        seller_name=raw.get("seller_name") or raw.get("name"),
        is_active=bool(raw.get("is_active", True)),
        raw=raw,
    )

"""
business_context.py — Business Context Builder (Phase 7.6A).

A single shared read path so every AI agent can get the seller's
business context in one call, instead of each agent independently
re-reading orders/inventory/listings/analytics from the mock dataset.

This module does NOT touch RAG, Chroma, retrieval, connectors,
Playwright, APIs, router architecture, or agent architecture. It is a
new, additive aggregation layer built entirely on top of the service
functions that already exist and are already the single source of
truth for this data:

    backend/service/marketplace_data_service.py
        get_orders()     -> OrdersTool     (registry key "orders")
        get_inventory()  -> InventoryTool  (registry key "inventory")
        get_listings()   -> ListingTool    (registry key "listing")
        get_analytics()  -> AnalyticsTool  (registry key "analytics")

Those four functions already resolve the seller's marketplace platform
and route through ToolManager -> ToolRegistry -> Tool -> connector —
the exact same path the dashboard/orders/inventory/analytics routers
and agent_layer/base/context_builder.py already use. This module does
not re-implement any of that; it calls each of those functions exactly
once and assembles the results into one structured object.

No business math happens here (no revenue totals, no low-stock
threshold, no cancellation-rate calculation). Those calculations
already live in ContextBuilder._build_business_section, which builds
the human-readable snapshot string used in agent prompts today.
Recomputing the same figures here — from the same underlying data,
with different code — would risk the two disagreeing, which is exactly
what that file's own docstring warns against. This builder exists for
callers that want the underlying summaries directly (structured data),
not the prompt-ready text block.

Usage:

    from backend.ai.context.business_context import get_business_context

    context = await get_business_context(db, seller_id)
    payload = context.to_dict()
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.model.marketplace_account import MarketplaceAccount
from backend.model.seller import Seller
from backend.service.marketplace_data_service import (
    NoMarketplaceConnectedError,
    get_analytics,
    get_inventory,
    get_listings,
    get_orders,
)


@dataclass
class BusinessContext:
    """
    One structured snapshot of a seller's business, derived only from
    orders/inventory/listings/analytics — the same mock dataset every
    other part of SellerOS already reads.

        seller       -> {seller_id, business_name}
        orders       -> get_orders() result
        inventory    -> get_inventory() result
        listings     -> get_listings() result
        analytics    -> get_analytics() result (sales + business metrics)
        marketplace  -> {platform, connected_marketplaces}
        generated_at -> ISO-8601 UTC timestamp for when this was built
    """

    seller: dict[str, Any]
    orders: dict[str, Any]
    inventory: dict[str, Any]
    listings: dict[str, Any]
    analytics: dict[str, Any]
    marketplace: dict[str, Any]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        """Renders the dataclass as the structured object shape agents
        will consume, matching the BusinessContext shape from the
        Phase 7.6A spec (generatedAt in camelCase for that field only,
        to match the example verbatim; every other key stays snake_case
        to match the rest of this codebase's JSON responses)."""
        return {
            "seller": self.seller,
            "orders": self.orders,
            "inventory": self.inventory,
            "listings": self.listings,
            "analytics": self.analytics,
            "marketplace": self.marketplace,
            "generatedAt": self.generated_at,
        }


def _seller_section(db: Session, seller_id: int) -> dict[str, Any]:
    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    return {
        "seller_id": seller_id,
        "business_name": seller.business_name if seller else None,
    }


def _marketplace_section(
    db: Session, seller_id: int, platform: Optional[str]
) -> dict[str, Any]:
    connected_marketplaces = (
        db.query(MarketplaceAccount)
        .filter(MarketplaceAccount.seller_id == seller_id)
        .count()
    )
    return {
        "platform": platform,
        "connected_marketplaces": connected_marketplaces,
    }


def _unavailable_section(list_key: str, message: str) -> dict[str, Any]:
    """Same 'be honest, don't fabricate' shape marketplace_data_service.py
    already returns for its own no-data cases — reused here rather than
    inventing a new empty/error shape."""
    return {
        "success": False,
        "message": message,
        list_key: [],
    }


async def get_business_context(
    db: Session,
    seller_id: int,
    platform: Optional[str] = None,
) -> BusinessContext:
    """
    The one function every AI agent should call for shared business
    context, instead of separately fetching orders/inventory/listings/
    analytics itself.

    Best-effort, matching get_dashboard_summary's own handling: if the
    seller has no connected marketplace, each data section reports that
    honestly instead of raising past this function or fabricating
    numbers. The seller and marketplace sections are always populated
    since neither requires a connected marketplace account.
    """
    try:
        orders = await get_orders(db, seller_id, platform)
        inventory = await get_inventory(db, seller_id, platform)
        listings = await get_listings(db, seller_id, platform)
        analytics = await get_analytics(db, seller_id, platform)
        resolved_platform = orders.get("platform", platform)
    except NoMarketplaceConnectedError as exc:
        message = str(exc)
        resolved_platform = platform
        orders = _unavailable_section("orders", message)
        inventory = _unavailable_section("items", message)
        listings = _unavailable_section("listings", message)
        analytics = {
            "platform": platform,
            "sales_metrics": None,
            "sales_metrics_message": message,
            "business_metrics": None,
            "business_metrics_message": message,
        }

    return BusinessContext(
        seller=_seller_section(db, seller_id),
        orders=orders,
        inventory=inventory,
        listings=listings,
        analytics=analytics,
        marketplace=_marketplace_section(db, seller_id, resolved_platform),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

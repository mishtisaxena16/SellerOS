"""
marketplace_data_service.py

Replaces the hardcoded placeholder data that GET /inventory, /orders,
/analytics, and /dashboard/summary previously returned. Calls the real
Tool Layer directly, per the handoff doc's own rule: dashboard-style
reads are structured data pulls, not conversational queries, and
should NOT go through Supervisor.handle()/the chat path — that's
slower and semantically the wrong tool for "give me a number".

Marketplace selection
----------------------
A seller may have zero, one, or several connected marketplace
accounts. These endpoints accept an optional `platform` query param;
if omitted, the seller's first connected account is used. If none are
connected, callers get a clear, honest response — not a fabricated
number and not a raw exception.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.model.marketplace_account import MarketplaceAccount
from backend.ai.tools_layer.registry.tool_registry import build_default_registry
from backend.ai.agent_layer.base.tool_manager import ToolManager
from backend.ai.connectors_layer.session_store import get_marketplace_session

_tool_registry = build_default_registry()


class NoMarketplaceConnectedError(Exception):
    """Raised when a seller has no connected marketplace account to read from."""


def _resolve_platform(db: Session, seller_id: int, platform: Optional[str]) -> str:
    if platform:
        return platform.lower()

    account = (
        db.query(MarketplaceAccount)
        .filter(MarketplaceAccount.seller_id == seller_id)
        .order_by(MarketplaceAccount.created_at.asc())
        .first()
    )
    if account is None:
        raise NoMarketplaceConnectedError(
            "No marketplace account is connected yet. Connect one via "
            "POST /marketplaces/connect before requesting this data."
        )
    return account.platform


def _tool_manager_for(seller_id: int, platform: str) -> ToolManager:
    session = get_marketplace_session(str(seller_id), platform)
    return ToolManager(_tool_registry, seller_id=str(seller_id), marketplace_session=session)

def _resolve_tool_manager(
    db: Session,
    seller_id: int,
    platform: Optional[str],
) -> tuple[str, ToolManager]:
    """
    Resolve the marketplace platform and construct the corresponding
    ToolManager for the current request.
    """
    resolved_platform = _resolve_platform(db, seller_id, platform)
    return resolved_platform, _tool_manager_for(seller_id, resolved_platform)


async def get_inventory(
    db: Session,
    seller_id: int,
    platform: Optional[str] = None,
) -> dict[str, Any]:
    platform, tm = _resolve_tool_manager(db, seller_id, platform)

    result = await tm.call("inventory", action="get_inventory")

    if not result.success:
        return {
            "platform": platform,
            "success": False,
            "message": result.message,
            "items": [],
        }

    return {
        "platform": platform,
        "success": True,
        "items": result.data,
    }


async def get_orders(
    db: Session,
    seller_id: int,
    platform: Optional[str] = None,
) -> dict[str, Any]:
    platform, tm = _resolve_tool_manager(db, seller_id, platform)

    result = await tm.call("orders", action="get_orders")

    if not result.success:
        return {
            "platform": platform,
            "success": False,
            "message": result.message,
            "orders": [],
        }

    return {
        "platform": platform,
        "success": True,
        "orders": result.data,
    }


async def get_listings(
    db: Session,
    seller_id: int,
    platform: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Mirrors get_inventory/get_orders above: bulk-fetch listings for the
    seller's resolved marketplace via ListingTool (registry key
    "listing"), through the same ToolManager path — no direct
    connector access, no separate resolution logic.
    """
    platform, tm = _resolve_tool_manager(db, seller_id, platform)

    result = await tm.call("listing", action="get_listings", page=page, limit=limit)

    if not result.success:
        return {
            "platform": platform,
            "success": False,
            "message": result.message,
            "listings": [],
        }

    return {
        "platform": platform,
        "success": True,
        "listings": result.data,
    }


async def get_analytics(
    db: Session,
    seller_id: int,
    platform: Optional[str] = None,
) -> dict[str, Any]:
    platform, tm = _resolve_tool_manager(db, seller_id, platform)

    sales_result = await tm.call(
        "analytics",
        action="get_sales_metrics",
    )

    business_result = await tm.call(
        "analytics",
        action="get_business_metrics",
    )

    return {
        "platform": platform,
        "sales_metrics": sales_result.data if sales_result.success else None,
        "sales_metrics_message": None if sales_result.success else sales_result.message,
        "business_metrics": business_result.data if business_result.success else None,
        "business_metrics_message": None if business_result.success else business_result.message,
    }


async def get_dashboard_summary(db: Session, seller_id: int) -> dict[str, Any]:
    marketplace_count = (
        db.query(MarketplaceAccount)
        .filter(MarketplaceAccount.seller_id == seller_id)
        .count()
    )

    if marketplace_count == 0:
        return {
            "connected_marketplaces": 0,
            "inventory_items": None,
            "pending_orders": None,
            "message": "No marketplace connected yet — connect one to see real numbers.",
        }

    platform, tm = _resolve_tool_manager(db, seller_id, None)
    inventory_result = await tm.call("inventory", action="get_inventory")
    orders_result = await tm.call("orders", action="get_orders")

    inventory_items = len(inventory_result.data) if inventory_result.success and inventory_result.data else 0
    pending_orders = (
        len([o for o in orders_result.data if getattr(o, "status", "").lower() in ("pending", "unshipped")])
        if orders_result.success and orders_result.data else 0
    )

    return {
        "connected_marketplaces": marketplace_count,
        "platform": platform,
        "inventory_items": inventory_items,
        "pending_orders": pending_orders,
    }

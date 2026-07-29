"""
ContextBuilder — assembles the context blob every agent hands to
PromptBuilder before an LLM call:

    User + Marketplace + Seller + Inventory + Knowledge + Conversation
    + Business Rules
    -> Prompt Context

(section 18). "Agents should never manually construct prompts" means
concretely: an agent's job is to say *what it needs* (which sections,
for which seller/platform), not to know *how* to fetch or format any
of it — that's this class's job.

Honest status, matching the project's own "don't fake it" pattern
(see e.g. listing_tool.py's docstring on get_listing): two of the
seven sections this is supposed to assemble aren't backed by anything
real yet, because the layers that would supply them don't exist:

- Knowledge:      Knowledge Layer / retriever isn't wired (KnowledgeTool
                   itself raises NotImplementedError today).
- Conversation:    Memory Layer (section 28) is being built by another
                   team member and doesn't exist yet.

Rather than silently return an empty string for those sections (which
would let an agent's prompt look complete when it's actually missing
context), `build()` marks each section's provenance explicitly, so a
PromptBuilder/Reasoner can tell "no knowledge because none was
relevant" apart from "no knowledge because the Knowledge Layer isn't
plugged in yet".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.ai.connectors_layer.marketplace_connector import MarketplaceSession


@dataclass
class ContextSection:
    content: Any
    available: bool
    note: str = ""


@dataclass
class PromptContext:
    sections: dict[str, ContextSection] = field(default_factory=dict)

    def get(self, key: str) -> Any:
        section = self.sections.get(key)
        return section.content if section else None

    def as_prompt_blocks(self) -> dict[str, str]:
        """Renders each *available* section to a plain-text block a
        PromptBuilder can splice into a template. Unavailable sections
        are omitted, not rendered as empty headers — an LLM prompt with
        an empty '## Knowledge' section invites the model to comment on
        the absence rather than just proceed without it."""
        blocks: dict[str, str] = {}
        for key, section in self.sections.items():
            if section.available:
                blocks[key] = str(section.content)
        return blocks


# Matches the frontend's LOW_STOCK_THRESHOLD and CANCELLED_STATUSES
# (Dashboard.tsx / BusinessIntelligence.tsx) so Seller Coach's notion
# of "low stock" and "cancelled" agrees with what the seller sees on
# screen — one seller asking the coach a question shouldn't get a
# different definition of "low stock" than the dashboard just showed them.
_LOW_STOCK_THRESHOLD = 20
_CANCELLED_STATUSES = {"cancelled", "canceled", "returned", "rejected"}


def _field(obj: Any, key: str, default: Any = None) -> Any:
    """
    Sales/business metrics come back from marketplace_connector.py as
    plain dicts (no Pydantic normalization step exists for them,
    unlike Order/Inventory) — while orders/inventory rows are real
    Pydantic objects. `getattr(a_dict, key, default)` silently returns
    `default` every time instead of raising, which is exactly the kind
    of quiet wrong-answer bug this file's own docstring warns against.
    This checks dicts with `.get()` and falls back to `getattr()` for
    everything else, so the same call site works for both shapes.
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class ContextBuilder:
    def __init__(self, tool_manager: Any) -> None:
        # Typed as Any to avoid a hard import cycle with ToolManager for
        # now; in practice this is always an agent_layer.base.tool_manager.ToolManager.
        self._tool_manager = tool_manager

    async def build(
        self,
        seller_id: str,
        user_query: str,
        session: Optional[MarketplaceSession] = None,
        include: Optional[list[str]] = None,
        conversation_history: Optional[list[dict[str, str]]] = None,
        business_rules: Optional[dict[str, Any]] = None,
    ) -> PromptContext:
        """
        `include` lets a specific agent ask for only the sections it
        actually needs (e.g. InventoryAgent has no business asking for
        "ads" context) instead of every agent always paying for every
        section on every call.
        """
        wanted = set(include) if include is not None else {
            "user", "marketplace", "seller", "inventory", "knowledge",
            "conversation", "business_rules", "business",
        }
        ctx = PromptContext()

        if "user" in wanted:
            ctx.sections["user"] = ContextSection(
                content=user_query, available=True,
            )

        if "marketplace" in wanted:
            ctx.sections["marketplace"] = ContextSection(
                content={"platform": session.platform} if session else None,
                available=session is not None,
                note="" if session else "No MarketplaceSession attached for this run.",
            )

        if "seller" in wanted:
            ctx.sections["seller"] = ContextSection(
                content={"seller_id": seller_id}, available=True,
            )

        if "inventory" in wanted and session is not None:
            result = await self._tool_manager.call("inventory", session=session, action="get_inventory")
            ctx.sections["inventory"] = ContextSection(
                content=result.data, available=result.success,
                note=result.message if not result.success else "",
            )

        if "business" in wanted:
            ctx.sections["business"] = await self._build_business_section(session, ctx)

        if "knowledge" in wanted:
            result = await self._tool_manager.call("knowledge", query=user_query)
            ctx.sections["knowledge"] = ContextSection(
                content=result.data, available=result.success,
                note=result.message if not result.success
                else "",
            )

        if "conversation" in wanted:
            ctx.sections["conversation"] = ContextSection(
                content=conversation_history, available=bool(conversation_history),
                note="" if conversation_history else "Memory Layer not wired yet — no conversation history available.",
            )

        if "business_rules" in wanted:
            ctx.sections["business_rules"] = ContextSection(
                content=business_rules, available=bool(business_rules),
            )

        return ctx

    async def _build_business_section(
        self, session: Optional[MarketplaceSession], ctx: PromptContext,
    ) -> ContextSection:
        """
        A short, computed snapshot of the seller's business — revenue,
        pending orders, low-stock/out-of-stock counts, cancellation
        rate — for agents (Seller Coach today) that need situational
        awareness without paying for the full raw inventory/orders
        payload in every prompt. Mirrors exactly the numbers already
        shown on Dashboard/Business Intelligence, computed the same
        way, so the coach's advice can't disagree with what the seller
        is looking at on screen.

        Best-effort by design: any one of orders/analytics/inventory
        failing (e.g. a fetcher not yet wired for this marketplace)
        just drops that line from the snapshot rather than failing the
        whole section — matching this file's existing pattern of
        marking gaps instead of guessing or crashing.
        """
        if session is None:
            return ContextSection(
                content=None, available=False,
                note="No MarketplaceSession attached for this run.",
            )

        lines: list[str] = [f"Platform: {session.platform}"]

        sales_result = await self._tool_manager.call("analytics", session=session, action="get_sales_metrics")
        if sales_result.success and sales_result.data:
            sm = sales_result.data
            revenue = _field(sm, "total_revenue")
            timeframe = _field(sm, "timeframe", "recent period")
            if revenue is not None:
                lines.append(f"Revenue ({timeframe}): ₹{revenue:,.0f}")

        business_result = await self._tool_manager.call("analytics", session=session, action="get_business_metrics")
        pending_from_metrics: Optional[int] = None
        if business_result.success and business_result.data:
            bm = business_result.data
            pending_from_metrics = _field(bm, "pending_orders")
            shipped = _field(bm, "shipped_orders")
            if pending_from_metrics is not None:
                lines.append(f"Pending orders: {pending_from_metrics}")
            if shipped is not None:
                lines.append(f"Shipped orders: {shipped}")

        orders_result = await self._tool_manager.call("orders", session=session, action="get_orders")
        if orders_result.success and orders_result.data:
            orders = orders_result.data
            if pending_from_metrics is None:
                pending = sum(1 for o in orders if getattr(o, "status", "").lower() in ("pending", "unshipped"))
                lines.append(f"Pending orders: {pending}")
            cancelled = sum(1 for o in orders if getattr(o, "status", "").lower() in _CANCELLED_STATUSES)
            if orders:
                lines.append(f"Cancellation/return rate: {cancelled / len(orders) * 100:.1f}% (of {len(orders)} synced orders)")

        # Reuse the "inventory" section's fetch if that section was
        # also requested this call, instead of hitting the tool twice.
        inventory_section = ctx.sections.get("inventory")
        if inventory_section is not None and inventory_section.available:
            inventory_items = inventory_section.content
        else:
            inv_result = await self._tool_manager.call("inventory", session=session, action="get_inventory")
            inventory_items = inv_result.data if inv_result.success else None

        if inventory_items:
            low_stock = sum(1 for i in inventory_items if 0 < getattr(i, "available_quantity", 0) < _LOW_STOCK_THRESHOLD)
            out_of_stock = sum(1 for i in inventory_items if getattr(i, "available_quantity", None) == 0)
            if low_stock:
                lines.append(f"Low stock SKUs (<{_LOW_STOCK_THRESHOLD} units): {low_stock}")
            if out_of_stock:
                lines.append(f"Out of stock SKUs: {out_of_stock}")

        if len(lines) <= 1:
            return ContextSection(
                content=None, available=False,
                note="Business metrics not available for this marketplace yet.",
            )

        return ContextSection(content="\n".join(lines), available=True)

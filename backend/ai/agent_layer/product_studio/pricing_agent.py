"""
PricingAgent — Tier 1 (Core Seller Operations) completion. Recommends
price changes for existing listings using current listing data and
sales performance.

Same "reading vs writing must be a distinct, explicit call" rule as
InventoryAgent.update_stock(): recommending a price is this agent's
`run()`; actually changing a live price is a separate
`apply_price_change()` method that must be called explicitly. A price
change is exactly the kind of mutating action guardrails.py's
`ConnectorPermissionRule` / `HumanApprovalRule` (MUTATING_ACTIONS
includes "price_change") exist to catch — requiring an explicit call
here is this agent's own stand-in for that gate, not a replacement.
"""
from __future__ import annotations

from typing import Any

from backend.ai.agent_layer.base.agent import BaseAgent
from backend.ai.agent_layer.base.agent_result import AgentResult
from backend.ai.agent_layer.base.context_builder import ContextSection
from backend.ai.agent_layer.base.state import AgentState
from backend.ai.agent_layer.base.tool_manager import ToolManager
from backend.ai.connectors_layer.marketplace_connector import MarketplaceSession


class PricingAgent(BaseAgent):
    name = "pricing_agent"
    description = (
        "Recommends price changes for existing listings using current "
        "listing data and sales performance. Can apply a price change "
        "only when explicitly asked."
    )

    permissions: dict[str, bool] = {
        "can_read_listings": True,
        "can_read_analytics": True,
        "can_recommend_price": True,
        "can_update_price": True,
    }
    allowed_tools: list[str] = ["listing", "analytics"]

    prompt_name = "pricing"
    context_sections = ["user", "seller", "marketplace", "business_rules"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "listing", "action": "get_listings"},
        {"tool": "analytics", "action": "get_sales_metrics"},
        {"step": "recommend_price"},
    ]

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "recommend_price":
            state.add_error(f"PricingAgent has no handler for step {step!r}.")
            return None

        listings_result = state.tool_results[0] if len(state.tool_results) > 0 else None
        sales_result = state.tool_results[1] if len(state.tool_results) > 1 else None

        context.sections["listings"] = ContextSection(
            content=listings_result.data if listings_result and listings_result.success else None,
            available=bool(listings_result and listings_result.success),
            note="" if (listings_result and listings_result.success)
            else (listings_result.message if listings_result else "No listings fetched."),
        )
        context.sections["sales_metrics"] = ContextSection(
            content=sales_result.data if sales_result and sales_result.success else None,
            available=bool(sales_result and sales_result.success),
            note="" if (sales_result and sales_result.success)
            else (sales_result.message if sales_result else "No sales metrics fetched."),
        )

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        return result.text

    # -- explicit write path, deliberately separate from run() --------------

    async def apply_price_change(
        self,
        tool_manager: ToolManager,
        session: MarketplaceSession,
        listing_id: str,
        new_price: float,
    ) -> AgentResult:
        """Applies a new price to an existing listing_id via
        ListingTool.update_listing. Deliberately not part of the
        recommend-price plan above — see module docstring."""
        result = await tool_manager.call(
            "listing", session=session, action="update_listing",
            listing_id=listing_id, update_data={"price": new_price},
        )
        if not result.success:
            return AgentResult.fail(message=result.message, tool_calls=[result])
        return AgentResult.ok(
            message=f"Listing {listing_id} price updated to {new_price}.",
            data=result.data, tool_calls=[result],
        )

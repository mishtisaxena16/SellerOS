"""
OrdersAgent — Tier 1 (Core Seller Operations) completion. Reports on
recent orders and shipments using OrdersTool, and flags anything that
looks stuck (e.g. an order with no shipment yet).

Read-only by design: OrdersTool only wraps get_orders / get_order /
get_shipments — there is no create/update/cancel-order action on the
connector layer, which matches reality (sellers don't create orders,
buyers do). So unlike InventoryAgent/PricingAgent there is no explicit
write method here — there's nothing for a future guardrail to gate,
because there's no mutation at all.

ContextBuilder has no dedicated "orders" section (only the fixed
User/Marketplace/Seller/Inventory/Knowledge/Conversation/BusinessRules
set), since order data is only needed here. `handle_step` pulls the
two tool results straight out of `state.tool_results` by position
(default_plan runs both tool steps strictly before this step) and
injects them into the shared PromptContext before rendering, the same
pattern InventoryAgent would use if it needed a second data source.
"""
from __future__ import annotations

from typing import Any

from ai.agent_layer.base.agent import BaseAgent
from ai.agent_layer.base.context_builder import ContextSection
from ai.agent_layer.base.state import AgentState


class OrdersAgent(BaseAgent):
    name = "order_agent"
    description = (
        "Reports on recent orders and shipments across marketplaces, "
        "and flags orders that look stuck (e.g. no shipment yet)."
    )

    permissions: dict[str, bool] = {
        "can_read_orders": True,
        "can_read_shipments": True,
        "can_cancel_order": False,
    }
    allowed_tools: list[str] = ["orders"]

    prompt_name = "orders"
    context_sections = ["user", "seller", "marketplace", "business_rules"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "orders", "action": "get_orders"},
        {"tool": "orders", "action": "get_shipments"},
        {"step": "summarize_orders"},
    ]

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "summarize_orders":
            state.add_error(f"OrdersAgent has no handler for step {step!r}.")
            return None

        orders_result = state.tool_results[0] if len(state.tool_results) > 0 else None
        shipments_result = state.tool_results[1] if len(state.tool_results) > 1 else None

        context.sections["orders"] = ContextSection(
            content=orders_result.data if orders_result and orders_result.success else None,
            available=bool(orders_result and orders_result.success),
            note="" if (orders_result and orders_result.success)
            else (orders_result.message if orders_result else "No orders fetched."),
        )
        context.sections["shipments"] = ContextSection(
            content=shipments_result.data if shipments_result and shipments_result.success else None,
            available=bool(shipments_result and shipments_result.success),
            note="" if (shipments_result and shipments_result.success)
            else (shipments_result.message if shipments_result else "No shipments fetched."),
        )

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        return result.text

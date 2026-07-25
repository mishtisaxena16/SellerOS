"""
ProfitabilityAgent — Tier 2 (Business Intelligence), third of four.
Flags margin health against a seller's configured margin floors using
revenue data. Deliberately NOT "computes actual profit."

Honest status: real profitability needs cost data (COGS, packaging,
shipping cost, marketplace commission, ad spend) and none of it is
modeled anywhere in SellerOS today — no field on Product, Order, or
Listing carries a cost. `models/models.py` has price and revenue,
never cost. So this agent can't produce a rupee profit figure without
inventing the cost side, which prompts/profitability.md explicitly
forbids the Reasoner from doing.

What it does instead, honestly: compares revenue/sales trends against
whatever margin floor the seller has configured in business_rules
(the same business_rules PricingAgent reads for margin floors) and
flags whether pricing looks consistent with that floor — a real,
useful check that doesn't require data the system doesn't have. If
SellerOS later adds a cost field to Product/Order, this agent should
be revisited to compute real margin — that's a data-modeling change,
not a prompt fix.
"""
from __future__ import annotations

from typing import Any

from agent_layer.base.agent import BaseAgent
from agent_layer.base.context_builder import ContextSection
from agent_layer.base.state import AgentState


class ProfitabilityAgent(BaseAgent):
    name = "profitability_agent"
    description = (
        "Checks whether current pricing and revenue trends look "
        "consistent with the seller's configured margin floors. Does "
        "NOT compute actual profit — SellerOS has no cost/COGS data "
        "modeled yet, so no rupee profit figure would be real."
    )

    permissions: dict[str, bool] = {
        "can_read_analytics": True,
        "can_modify_listings": False,
        "can_modify_inventory": False,
    }
    allowed_tools: list[str] = ["analytics"]

    prompt_name = "profitability"
    context_sections = ["user", "seller", "marketplace", "business_rules"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "analytics", "action": "get_sales_metrics"},
        {"step": "assess_margin_health"},
    ]

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "assess_margin_health":
            state.add_error(f"ProfitabilityAgent has no handler for step {step!r}.")
            return None

        sales_result = state.tool_results[0] if len(state.tool_results) > 0 else None

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

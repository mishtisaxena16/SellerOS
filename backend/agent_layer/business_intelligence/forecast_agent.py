"""
ForecastAgent — Tier 2 (Business Intelligence), second of four.
Projects near-term demand/revenue direction from recent sales history.

Honest status, matching this project's "don't fake it" pattern (see
listing_tool.py's docstring on get_listing, or AnalyticsTool's own
docstring on why forecast_sales() doesn't belong at the tool layer):
there is no statistical forecasting model anywhere in SellerOS —  no
time-series library, no trained model, nothing. What this agent
actually does is hand the Reasoner the same sales_metrics history
AnalyticsAgent uses and ask for a *qualitative directional read*
("trending up/down/flat, watch out for X"), not a number a seller
could reasonably budget against. prompts/forecast.md says this to the
LLM explicitly, and the agent's own docstring says it here for anyone
reading the code: if SellerOS ever needs an actual forecast (a number
with a confidence interval), that's a real modeling task — pandas/
statsmodels/prophet over exported order history — layered in as a new
Tool this agent would call, not a prompt-engineering fix to this file.
"""
from __future__ import annotations

from typing import Any

from agent_layer.base.agent import BaseAgent
from agent_layer.base.context_builder import ContextSection
from agent_layer.base.state import AgentState


class ForecastAgent(BaseAgent):
    name = "forecasting_agent"
    description = (
        "Gives a qualitative read on near-term sales direction (trending "
        "up, down, or flat, and why) from recent sales history. Not a "
        "statistical forecast — no model or confidence interval behind it."
    )

    permissions: dict[str, bool] = {
        "can_read_analytics": True,
        "can_modify_listings": False,
        "can_modify_inventory": False,
    }
    allowed_tools: list[str] = ["analytics"]

    prompt_name = "forecast"
    context_sections = ["user", "seller", "marketplace", "business_rules"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "analytics", "action": "get_sales_metrics"},
        {"step": "project_trend"},
    ]

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "project_trend":
            state.add_error(f"ForecastAgent has no handler for step {step!r}.")
            return None

        sales_result = state.tool_results[0] if len(state.tool_results) > 0 else None

        context.sections["sales_metrics"] = ContextSection(
            content=sales_result.data if sales_result and sales_result.success else None,
            available=bool(sales_result and sales_result.success),
            note="" if (sales_result and sales_result.success)
            else (sales_result.message if sales_result else "No sales history fetched."),
        )

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        return result.text

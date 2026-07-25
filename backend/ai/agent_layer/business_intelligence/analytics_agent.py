"""
AnalyticsAgent — Tier 2 (Business Intelligence), first of four. Reports
on sales and business KPIs using AnalyticsTool.

Read-only, same reasoning as OrdersAgent: AnalyticsTool only wraps
get_sales_metrics / get_business_metrics, there's no connector-layer
action that "changes" analytics data, so there's nothing here for a
future guardrail to gate and no explicit write method.

Two tool calls, same manual-injection-into-context pattern
PricingAgent/OrdersAgent use for a second data source, since
ContextBuilder's fixed section set (context_builder.py) has no
built-in "sales_metrics" or "business_metrics" section.
"""
from __future__ import annotations

from typing import Any

from ai.agent_layer.base.agent import BaseAgent
from ai.agent_layer.base.context_builder import ContextSection
from ai.agent_layer.base.state import AgentState


class AnalyticsAgent(BaseAgent):
    name = "analytics_agent"
    description = (
        "Reports on sales performance and business KPIs across "
        "marketplaces using live connector data, and flags notable "
        "trends (revenue up/down, order volume shifts)."
    )

    permissions: dict[str, bool] = {
        "can_read_analytics": True,
        "can_modify_listings": False,
        "can_modify_inventory": False,
    }
    allowed_tools: list[str] = ["analytics"]

    prompt_name = "analytics"
    context_sections = ["user", "seller", "marketplace", "business_rules"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "analytics", "action": "get_sales_metrics"},
        {"tool": "analytics", "action": "get_business_metrics"},
        {"step": "summarize_performance"},
    ]

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "summarize_performance":
            state.add_error(f"AnalyticsAgent has no handler for step {step!r}.")
            return None

        sales_result = state.tool_results[0] if len(state.tool_results) > 0 else None
        business_result = state.tool_results[1] if len(state.tool_results) > 1 else None

        context.sections["sales_metrics"] = ContextSection(
            content=sales_result.data if sales_result and sales_result.success else None,
            available=bool(sales_result and sales_result.success),
            note="" if (sales_result and sales_result.success)
            else (sales_result.message if sales_result else "No sales metrics fetched."),
        )
        context.sections["business_metrics"] = ContextSection(
            content=business_result.data if business_result and business_result.success else None,
            available=bool(business_result and business_result.success),
            note="" if (business_result and business_result.success)
            else (business_result.message if business_result else "No business metrics fetched."),
        )

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        return result.text

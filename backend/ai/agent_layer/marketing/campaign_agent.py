"""
CampaignAgent — Tier 3 (Marketing), second of four. Recommends a
marketing campaign plan (what to promote, roughly when, and why) by
combining sales performance with the seller's current advertising
state.

Deliberate design choice, worth being explicit about: CampaignAgent
has NO write method, unlike every other mutating-capable agent in this
codebase. Planning and execution are kept as two different agents on
purpose here — CampaignAgent decides *what a campaign should look
like*, AdsAgent.create_campaign() is what actually spends budget. A
seller (or a future Supervisor plan) that wants to act on a
CampaignAgent recommendation calls AdsAgent next, explicitly, with a
campaign_data payload informed by this agent's output. This keeps the
"reading/planning vs writing" line in the same place it is everywhere
else in the codebase — CampaignAgent just never had a writing side to
begin with, rather than needing a stand-in guardrail to withhold it.
"""
from __future__ import annotations

from typing import Any

from backend.ai.agent_layer.base.agent import BaseAgent
from backend.ai.agent_layer.base.context_builder import ContextSection
from backend.ai.agent_layer.base.state import AgentState


class CampaignAgent(BaseAgent):
    name = "campaign_agent"
    description = (
        "Recommends a marketing campaign plan (what to promote, timing, "
        "and rationale) using sales performance and current ad campaigns. "
        "Read-only — hand a resulting plan to AdsAgent to actually create it."
    )

    permissions: dict[str, bool] = {
        "can_read_analytics": True,
        "can_read_ads": True,
        "can_create_ads": False,
    }
    allowed_tools: list[str] = ["analytics", "ads"]

    prompt_name = "campaign"
    context_sections = ["user", "seller", "marketplace", "business_rules"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "analytics", "action": "get_sales_metrics"},
        {"tool": "ads", "action": "get_campaigns"},
        {"step": "plan_campaign"},
    ]

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "plan_campaign":
            state.add_error(f"CampaignAgent has no handler for step {step!r}.")
            return None

        sales_result = state.tool_results[0] if len(state.tool_results) > 0 else None
        ads_result = state.tool_results[1] if len(state.tool_results) > 1 else None

        context.sections["sales_metrics"] = ContextSection(
            content=sales_result.data if sales_result and sales_result.success else None,
            available=bool(sales_result and sales_result.success),
            note="" if (sales_result and sales_result.success)
            else (sales_result.message if sales_result else "No sales metrics fetched."),
        )
        context.sections["campaigns"] = ContextSection(
            content=ads_result.data if ads_result and ads_result.success else None,
            available=bool(ads_result and ads_result.success),
            note="" if (ads_result and ads_result.success)
            else (ads_result.message if ads_result else "No existing campaigns fetched."),
        )

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        return result.text

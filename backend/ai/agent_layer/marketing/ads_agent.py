"""
AdsAgent — Tier 3 (Marketing), first of four. Reports on current
advertising campaigns and can create a new one when explicitly asked,
using AdsTool.

Same "reading vs writing must be a distinct, explicit call" rule as
InventoryAgent.update_stock() / ListingAgent.publish() /
PricingAgent.apply_price_change(): creating an ad campaign spends real
budget, so `create_campaign()` below is a separate method that must be
called explicitly — never a side effect of `run()`.

Scope note, matching AdsTool's own docstring: AdsTool only wraps
get_campaigns / create_campaign / delete_campaign — there's no
pause_campaign or campaign_metrics on the connector layer. This agent
doesn't expose a pause action because there's nothing real underneath
it to call; it does expose delete, since the tool supports it.
"""
from __future__ import annotations

from typing import Any

from ai.agent_layer.base.agent import BaseAgent
from ai.agent_layer.base.agent_result import AgentResult
from ai.agent_layer.base.state import AgentState
from ai.agent_layer.base.tool_manager import ToolManager
from ai.connectors_layer.marketplace_connector import MarketplaceSession


class AdsAgent(BaseAgent):
    name = "ads_agent"
    description = (
        "Reports on current advertising campaigns across marketplaces. "
        "Can create or delete a campaign only when explicitly asked."
    )

    permissions: dict[str, bool] = {
        "can_read_ads": True,
        "can_create_ads": True,
        "can_delete_ads": True,
    }
    allowed_tools: list[str] = ["ads"]

    prompt_name = "ads"
    context_sections = ["user", "seller", "marketplace", "business_rules"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "ads", "action": "get_campaigns"},
        {"step": "summarize_campaigns"},
    ]

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "summarize_campaigns":
            state.add_error(f"AdsAgent has no handler for step {step!r}.")
            return None

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        return result.text

    # -- explicit write paths, deliberately separate from run() -------------

    async def create_campaign(
        self,
        tool_manager: ToolManager,
        session: MarketplaceSession,
        campaign_data: dict[str, Any],
    ) -> AgentResult:
        """Creates a new ad campaign. Deliberately not part of the
        summarize plan above — spending budget should only ever happen
        because the caller explicitly asked for it."""
        result = await tool_manager.call(
            "ads", session=session, action="create_campaign", campaign_data=campaign_data,
        )
        if not result.success:
            return AgentResult.fail(message=result.message, tool_calls=[result])
        return AgentResult.ok(
            message="Campaign created.", data=result.data, tool_calls=[result],
        )

    async def delete_campaign(
        self,
        tool_manager: ToolManager,
        session: MarketplaceSession,
        campaign_id: str,
    ) -> AgentResult:
        result = await tool_manager.call(
            "ads", session=session, action="delete_campaign", campaign_id=campaign_id,
        )
        if not result.success:
            return AgentResult.fail(message=result.message, tool_calls=[result])
        return AgentResult.ok(
            message=f"Campaign {campaign_id} deleted.", data=result.data, tool_calls=[result],
        )

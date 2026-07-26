"""
SEOAgent — Tier 3 (Marketing), third of four. Recommends title/
description/keyword improvements for existing listings to improve
search ranking within a marketplace, using ListingTool + KnowledgeTool.

Same "reading vs writing must be a distinct, explicit call" rule as
PricingAgent.apply_price_change(): recommending SEO changes is `run()`;
actually rewriting a live listing's title/description is a separate
`apply_seo_update()` method that must be called explicitly.

Honest status: there is no keyword-research or search-ranking API
anywhere in SellerOS (no SEO tool, no ranking data connector) — this
agent's recommendations come from the Reasoner reading the current
listing plus whatever marketplace-policy/best-practice knowledge
KnowledgeTool returns (itself NOT_IMPLEMENTED today, same as every
other agent that touches it). prompts/seo.md is explicit that
suggestions should be reasoned from the listing content shown, not
presented as backed by real keyword-volume or ranking data that
doesn't exist.
"""
from __future__ import annotations

from typing import Any

from backend.ai.agent_layer.base.agent import BaseAgent
from backend.ai.agent_layer.base.agent_result import AgentResult
from backend.ai.agent_layer.base.state import AgentState
from backend.ai.agent_layer.base.tool_manager import ToolManager
from backend.ai.connectors_layer.marketplace_connector import MarketplaceSession


class SEOAgent(BaseAgent):
    name = "seo_agent"
    description = (
        "Recommends title/description/keyword improvements for existing "
        "listings to improve marketplace search ranking. Can apply a "
        "recommended change only when explicitly asked."
    )

    permissions: dict[str, bool] = {
        "can_read_listings": True,
        "can_update_listing": True,
        "can_publish_listing": False,
    }
    allowed_tools: list[str] = ["listing", "knowledge"]

    prompt_name = "seo"
    context_sections = ["user", "seller", "marketplace", "knowledge"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "listing", "action": "get_listings"},
        {"tool": "knowledge", "action": "search", "query": None, "top_k": 5},
        {"step": "recommend_seo"},
    ]

    def override_plan(self, plan: list[dict[str, Any]], user_query: str) -> list[dict[str, Any]]:
        for step in plan:
            if step.get("tool") == "knowledge" and step.get("query") is None:
                step["query"] = user_query
        return plan

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "recommend_seo":
            state.add_error(f"SEOAgent has no handler for step {step!r}.")
            return None

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        state.scratch["seo_recommendation"] = result.text
        return result.text

    def format_output(self, state: AgentState) -> AgentResult:
        result = super().format_output(state)
        if state.scratch.get("seo_recommendation"):
            result.artifacts.append({"type": "seo_recommendation", "content": state.scratch["seo_recommendation"]})
        return result

    # -- explicit write path, deliberately separate from run() --------------

    async def apply_seo_update(
        self,
        tool_manager: ToolManager,
        session: MarketplaceSession,
        listing_id: str,
        update_data: dict[str, Any],
    ) -> AgentResult:
        """Applies an SEO change (e.g. revised title/description) to an
        existing listing_id via ListingTool.update_listing. Deliberately
        not part of the recommend plan above — see module docstring."""
        result = await tool_manager.call(
            "listing", session=session, action="update_listing",
            listing_id=listing_id, update_data=update_data,
        )
        if not result.success:
            return AgentResult.fail(message=result.message, tool_calls=[result])
        return AgentResult.ok(
            message=f"Listing {listing_id} updated with SEO changes.",
            data=result.data, tool_calls=[result],
        )

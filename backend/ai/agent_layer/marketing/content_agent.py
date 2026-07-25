"""
ContentAgent — Tier 3 (Marketing), fourth of four. Drafts marketing
copy (product descriptions, social captions, promotional text) for a
listing using ListingTool + KnowledgeTool.

Mirrors ListingAgent's draft/publish split, not SEOAgent's — the
distinction from SEOAgent is genuinely one of purpose, not just
naming: SEOAgent optimizes existing copy for search ranking (keywords,
title structure); ContentAgent writes new promotional copy for a
listing or a marketing channel (a caption, a launch description). Both
end up writing to the same place (ListingTool.update_listing for the
listing case), and that's fine — two agents legitimately producing
input to the same write action is exactly what CampaignAgent's "plan
here, execute there" split already establishes as a normal pattern in
this codebase, not a duplication to collapse.

Same "reading vs writing must be a distinct, explicit call" rule as
every other mutating-capable agent here.
"""
from __future__ import annotations

from typing import Any

from ai.agent_layer.base.agent import BaseAgent
from ai.agent_layer.base.agent_result import AgentResult
from ai.agent_layer.base.state import AgentState
from ai.agent_layer.base.tool_manager import ToolManager
from ai.connectors_layer.marketplace_connector import MarketplaceSession


class ContentAgent(BaseAgent):
    name = "content_agent"
    description = (
        "Drafts marketing copy (product descriptions, captions, "
        "promotional text) for a listing. Can push a draft into the "
        "live listing description only when explicitly asked."
    )

    permissions: dict[str, bool] = {
        "can_read_listings": True,
        "can_update_listing": True,
        "can_publish_listing": False,
    }
    allowed_tools: list[str] = ["listing", "knowledge"]

    prompt_name = "content"
    context_sections = ["user", "seller", "marketplace", "knowledge"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "listing", "action": "get_listings"},
        {"tool": "knowledge", "action": "search", "query": None, "top_k": 5},
        {"step": "draft_content"},
    ]

    def override_plan(self, plan: list[dict[str, Any]], user_query: str) -> list[dict[str, Any]]:
        for step in plan:
            if step.get("tool") == "knowledge" and step.get("query") is None:
                step["query"] = user_query
        return plan

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "draft_content":
            state.add_error(f"ContentAgent has no handler for step {step!r}.")
            return None

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        state.scratch["content_draft"] = result.text
        return result.text

    def format_output(self, state: AgentState) -> AgentResult:
        result = super().format_output(state)
        if state.scratch.get("content_draft"):
            result.artifacts.append({"type": "content_draft", "content": state.scratch["content_draft"]})
        return result

    # -- explicit write path, deliberately separate from run() --------------

    async def apply_content_update(
        self,
        tool_manager: ToolManager,
        session: MarketplaceSession,
        listing_id: str,
        description: str,
    ) -> AgentResult:
        """Pushes drafted copy into a listing's live description via
        ListingTool.update_listing. Deliberately not part of the draft
        plan above — see module docstring."""
        result = await tool_manager.call(
            "listing", session=session, action="update_listing",
            listing_id=listing_id, update_data={"description": description},
        )
        if not result.success:
            return AgentResult.fail(message=result.message, tool_calls=[result])
        return AgentResult.ok(
            message=f"Listing {listing_id} description updated.",
            data=result.data, tool_calls=[result],
        )

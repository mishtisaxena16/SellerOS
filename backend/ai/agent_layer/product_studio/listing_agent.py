"""
ListingAgent — third agent in the build order (section 25: "3. Listing
Agent"). Drafts/revises product listing copy using ListingTool +
KnowledgeTool for context, and can publish a draft as an explicit,
separate write action — same "reading vs writing must be a distinct
call" reasoning as InventoryAgent.update_stock().

Scope note: this is the agent_layer's ListingAgent, not the folder tree
in section 13's `product_studio/` listing all of listing_agent.py +
seo_agent.py + image_agent.py as siblings. Only listing_agent.py exists
so far — seo_agent.py and image_agent.py aren't part of section 31's
immediate task list (Seller Coach, Inventory, Listing) and are left
unbuilt rather than stubbed with fake behavior.
"""
from __future__ import annotations

from typing import Any

from backend.ai.agent_layer.base.agent import BaseAgent
from backend.ai.agent_layer.base.agent_result import AgentResult
from backend.ai.agent_layer.base.state import AgentState
from backend.ai.agent_layer.base.tool_manager import ToolManager
from backend.ai.connectors_layer.marketplace_connector import MarketplaceSession


class ListingAgent(BaseAgent):
    name = "listing_agent"
    description = (
        "Drafts and revises marketplace product listings (title, "
        "description, price, category) using existing listing data and "
        "the SellerOS knowledge base. Can publish a listing when "
        "explicitly asked."
    )

    permissions: dict[str, bool] = {
        "can_read_listings": True,
        "can_create_listing": True,
        "can_publish_listing": True,
        "can_delete_listing": False,
    }
    allowed_tools: list[str] = ["listing", "knowledge"]

    prompt_name = "listing"
    context_sections = ["user", "seller", "marketplace", "inventory", "knowledge"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "listing", "action": "get_listings"},
        {"tool": "knowledge", "action": "search", "query": None, "top_k": 5},
        {"step": "draft_listing"},
    ]

    def override_plan(self, plan: list[dict[str, Any]], user_query: str) -> list[dict[str, Any]]:
        for step in plan:
            if step.get("tool") == "knowledge" and step.get("query") is None:
                step["query"] = user_query
        return plan

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "draft_listing":
            state.add_error(f"ListingAgent has no handler for step {step!r}.")
            return None

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        state.scratch["draft"] = result.text
        return result.text

    def format_output(self, state: AgentState) -> AgentResult:
        # Overridden (not just the shared default) so the drafted copy
        # is also surfaced as an artifact, not only inline in `message`
        # — a listing draft is something a frontend would want to show
        # in an editable field, not just render as chat text.
        result = super().format_output(state)
        if state.scratch.get("draft"):
            result.artifacts.append({"type": "listing_draft", "content": state.scratch["draft"]})
        return result

    # -- explicit write path, deliberately separate from run() --------------

    async def publish(
        self,
        tool_manager: ToolManager,
        session: MarketplaceSession,
        listing_id: str,
    ) -> AgentResult:
        """Publishes an already-created listing_id. Deliberately not
        part of the draft plan above — publishing is a real, visible
        marketplace mutation and should only ever happen because the
        caller explicitly asked for it, not as an automatic next step
        after drafting."""
        result = await tool_manager.call(
            "listing", session=session, action="publish_listing", listing_id=listing_id,
        )
        if not result.success:
            return AgentResult.fail(message=result.message, tool_calls=[result])
        return AgentResult.ok(
            message=f"Listing {listing_id} published.", data=result.data, tool_calls=[result],
        )

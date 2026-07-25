"""
ContextBuilder — assembles the context blob every agent hands to
PromptBuilder before an LLM call:

    User + Marketplace + Seller + Inventory + Knowledge + Conversation
    + Business Rules
    -> Prompt Context

(section 18). "Agents should never manually construct prompts" means
concretely: an agent's job is to say *what it needs* (which sections,
for which seller/platform), not to know *how* to fetch or format any
of it — that's this class's job.

Honest status, matching the project's own "don't fake it" pattern
(see e.g. listing_tool.py's docstring on get_listing): two of the
seven sections this is supposed to assemble aren't backed by anything
real yet, because the layers that would supply them don't exist:

- Knowledge:      Knowledge Layer / retriever isn't wired (KnowledgeTool
                   itself raises NotImplementedError today).
- Conversation:    Memory Layer (section 28) is being built by another
                   team member and doesn't exist yet.

Rather than silently return an empty string for those sections (which
would let an agent's prompt look complete when it's actually missing
context), `build()` marks each section's provenance explicitly, so a
PromptBuilder/Reasoner can tell "no knowledge because none was
relevant" apart from "no knowledge because the Knowledge Layer isn't
plugged in yet".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ai.connectors_layer.marketplace_connector import MarketplaceSession


@dataclass
class ContextSection:
    content: Any
    available: bool
    note: str = ""


@dataclass
class PromptContext:
    sections: dict[str, ContextSection] = field(default_factory=dict)

    def get(self, key: str) -> Any:
        section = self.sections.get(key)
        return section.content if section else None

    def as_prompt_blocks(self) -> dict[str, str]:
        """Renders each *available* section to a plain-text block a
        PromptBuilder can splice into a template. Unavailable sections
        are omitted, not rendered as empty headers — an LLM prompt with
        an empty '## Knowledge' section invites the model to comment on
        the absence rather than just proceed without it."""
        blocks: dict[str, str] = {}
        for key, section in self.sections.items():
            if section.available:
                blocks[key] = str(section.content)
        return blocks


class ContextBuilder:
    def __init__(self, tool_manager: Any) -> None:
        # Typed as Any to avoid a hard import cycle with ToolManager for
        # now; in practice this is always an agent_layer.base.tool_manager.ToolManager.
        self._tool_manager = tool_manager

    async def build(
        self,
        seller_id: str,
        user_query: str,
        session: Optional[MarketplaceSession] = None,
        include: Optional[list[str]] = None,
        conversation_history: Optional[list[dict[str, str]]] = None,
        business_rules: Optional[dict[str, Any]] = None,
    ) -> PromptContext:
        """
        `include` lets a specific agent ask for only the sections it
        actually needs (e.g. InventoryAgent has no business asking for
        "ads" context) instead of every agent always paying for every
        section on every call.
        """
        wanted = set(include) if include is not None else {
            "user", "marketplace", "seller", "inventory", "knowledge",
            "conversation", "business_rules",
        }
        ctx = PromptContext()

        if "user" in wanted:
            ctx.sections["user"] = ContextSection(
                content=user_query, available=True,
            )

        if "marketplace" in wanted:
            ctx.sections["marketplace"] = ContextSection(
                content={"platform": session.platform} if session else None,
                available=session is not None,
                note="" if session else "No MarketplaceSession attached for this run.",
            )

        if "seller" in wanted:
            ctx.sections["seller"] = ContextSection(
                content={"seller_id": seller_id}, available=True,
            )

        if "inventory" in wanted and session is not None:
            result = await self._tool_manager.call("inventory", session=session, action="get_inventory")
            ctx.sections["inventory"] = ContextSection(
                content=result.data, available=result.success,
                note=result.message if not result.success else "",
            )

        if "knowledge" in wanted:
            result = await self._tool_manager.call("knowledge", query=user_query)
            ctx.sections["knowledge"] = ContextSection(
                content=result.data, available=result.success,
                note=result.message if not result.success
                else "",
            )

        if "conversation" in wanted:
            ctx.sections["conversation"] = ContextSection(
                content=conversation_history, available=bool(conversation_history),
                note="" if conversation_history else "Memory Layer not wired yet — no conversation history available.",
            )

        if "business_rules" in wanted:
            ctx.sections["business_rules"] = ContextSection(
                content=business_rules, available=bool(business_rules),
            )

        return ctx

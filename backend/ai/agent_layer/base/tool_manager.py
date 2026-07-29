"""
ToolManager — the only way an agent is allowed to touch a tool.

    Bad:  Listing Agent -> Amazon API
    Good: Listing Agent -> ToolManager -> Tool -> Connector -> Amazon

(section 19 of the handover doc). Concretely, ToolManager is a thin
wrapper around the existing ToolRegistry (tools/registry/tool_registry.py)
that also owns building the ToolContext for a given seller/session, so
agent code never constructs one by hand and never imports
tools.marketplace.* directly.

Why this isn't just "agents call tool_registry.get(...) themselves":
every tool call needs the *same* ToolContext (seller_id, platform,
marketplace_session, memory, request_id, ...) attached, call after
call, for the life of one agent run. Building that inline in every
agent method would (a) duplicate the same six lines everywhere and
(b) make it easy for one agent to forget a field (e.g. request_id for
tracing) that another agent remembers. One ToolManager instance per
agent run, built once, closes that gap.

Session-per-platform note: an agent working across marketplaces (e.g.
Analytics Agent comparing Amazon vs Meesho) needs a *different*
MarketplaceSession per call. `call()` accepts an optional session
override for exactly that case; the ToolManager's own default session
covers the common case of "this whole agent run is scoped to one
platform".
"""
from __future__ import annotations

from typing import Any, Optional

from backend.ai.tools_layer.base.tool_context import ToolContext
from backend.ai.tools_layer.base.tool_result import ToolResult
from backend.ai.tools_layer.registry.tool_registry import ToolRegistry
from backend.ai.connectors_layer.marketplace_connector import MarketplaceSession


class ToolManager:
    def __init__(
        self,
        registry: ToolRegistry,
        seller_id: str,
        marketplace_session: Optional[MarketplaceSession] = None,
        memory: Any = None,
        user: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        self._registry = registry
        self._seller_id = seller_id
        self._default_session = marketplace_session
        self._memory = memory
        self._user = user
        self._trace_id = trace_id

    def _build_context(
        self,
        session_override: Optional[MarketplaceSession],
    ) -> ToolContext:
        session = session_override or self._default_session

        # Deliberately NOT raising here when session is None. Whether a
        # MarketplaceSession is actually required is a per-tool decision,
        # not a per-call one: marketplace tools (inventory/listing/orders/
        # ads/account) already call context.require_session() themselves
        # (tools_layer/marketplace/_helpers.get_session ->
        # ToolContext.require_session()) and raise their own clear
        # ValueError, which BaseTool.run() turns into a normal
        # ToolResult.fail(...) instead of an unhandled exception.
        # Non-marketplace tools (e.g. KnowledgeTool) never touch
        # marketplace_session at all and must be able to run with none
        # attached — which is the common case for LLM-only requests
        # (seller coaching, SEO tips, campaign ideas, product copy) that
        # never named a marketplace. Raising unconditionally here failed
        # every one of those before the tool itself ever got a chance to
        # decide it didn't need a session.
        return ToolContext(
            seller_id=self._seller_id,
            platform=session.platform if session else None,
            marketplace_session=session,
            memory=self._memory,
            user=self._user,
            trace_id=self._trace_id,
        )

    async def call(
        self,
        tool_name: str,
        session: Optional[MarketplaceSession] = None,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Runs `tool_name` from the registry with a freshly built
        ToolContext. `kwargs` are passed straight through to
        BaseTool.run() (typically `action=...` plus that action's
        arguments) — ToolManager doesn't know or care about any given
        tool's specific signature, matching the same "agents don't
        need to know tool internals" separation ToolRegistry already
        enforces one layer down.
        """
        tool = self._registry.get(tool_name)
        context = self._build_context(session)
        return await tool.run(context, **kwargs)

    def describe_tools(self) -> dict[str, str]:
        """Name -> description for every registered tool. Useful for
        building an LLM tool-selection prompt (PromptBuilder / Planner)."""
        return self._registry.describe()

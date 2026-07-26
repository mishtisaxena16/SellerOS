"""
BaseAgent — every specialized agent inherits from this and defines
only Goal / Tools / Permissions / Prompt (section 14):

    BaseAgent
        Planner
        ToolManager
        ContextBuilder
        PromptBuilder
        Reasoner
        Guardrail Hooks
        Output Formatter

    Specialized agents should only define:
        Goal
        Tools
        Permissions
        Prompt

    Everything else should be inherited.

What a subclass actually overrides, concretely:

    name / description      -- identity, for the Agent Registry
    permissions             -- dict[str, bool], e.g. {"can_create_listing": True}
    allowed_tools           -- which ToolManager.call(name, ...) calls this agent may make
    prompt_name             -- which agent_layer/prompts/*.md template it renders
    default_plan            -- its static plan template (see planner.py)
    context_sections        -- which ContextBuilder sections it needs
    handle_step()           -- how it executes its own non-tool plan steps
                                (typically: render prompt, call Reasoner, store result)

Guardrail Hooks: `check_permissions()` below is a hook, not an
enforcement point — it always returns True today. The actual
Permission/Guardrail Layer (section 29) is explicitly "being built by
another team member." Wiring real enforcement in here now would mean
building Guardrail logic inside the Agent Layer, which the
architecture explicitly separates out — same reasoning BaseTool.py
already gives for why `permissions` is stored but not enforced at the
Tool Layer. Storing/declaring `permissions` now avoids a retrofit
later; enforcing it here would build the wrong layer's job into this one.

Output Formatter: `format_output()` is what normalizes whatever an
agent produced into the shared AgentResult shape (section 23/24: "the
frontend should never care which agent generated the result"). It's a
plain method here, not a separate injected component, because unlike
Planner/ToolManager/etc. it has no state or config of its own to swap
out — it's pure state -> AgentResult mapping.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from backend.ai.agent_layer.base.agent_result import AgentResult
from backend.ai.agent_layer.base.context_builder import ContextBuilder
from backend.ai.agent_layer.base.executor import Executor
from backend.ai.agent_layer.base.planner import Planner
from backend.ai.agent_layer.base.prompt_builder import PromptBuilder
from backend.ai.agent_layer.base.reasoning import LLMReasoner
from backend.ai.agent_layer.base.state import AgentState
from backend.ai.agent_layer.base.tool_manager import ToolManager
from backend.ai.connectors_layer.marketplace_connector import MarketplaceSession


class BaseAgent(ABC):
    name: str = "base_agent"
    description: str = "Base agent. Override name/description/goal in subclasses."

    # Declared, not enforced yet — see module docstring re: Guardrail Layer.
    permissions: dict[str, bool] = {}

    # Which tool_registry keys this agent is allowed to call. Purely a
    # declared contract for now (nothing currently checks it before
    # ToolManager.call() runs) — same "declare now, enforce once the
    # Guardrail Layer exists" reasoning as `permissions` above. Kept as
    # a *separate* field from `permissions` rather than folding into
    # it, because "may call the inventory tool at all" and "may call
    # update_inventory specifically" are different-grained checks a
    # future Guardrail will want to make independently.
    allowed_tools: list[str] = []

    prompt_name: str = ""
    default_plan: list[dict[str, Any]] = []
    context_sections: Optional[list[str]] = None  # None = ContextBuilder default (all sections)

    def __init__(
        self,
        reasoner: LLMReasoner,
        planner: Optional[Planner] = None,
        prompt_builder: Optional[PromptBuilder] = None,
    ) -> None:
        # Deliberately no ToolManager here. A ToolManager is scoped to
        # one seller_id/MarketplaceSession (see tool_manager.py), but a
        # single agent *instance* is meant to be built once at startup
        # and shared across every seller's requests (same as
        # ToolRegistry/AgentRegistry — "one instance, created once").
        # Baking a specific seller's ToolManager into __init__ would
        # make agent instances request-scoped, which breaks the
        # registry pattern this whole layer is built around. Instead,
        # `run()` below takes tool_manager as a parameter — the caller
        # (Executive Agent, or a test) builds a fresh ToolManager per
        # request and hands it in for that one call only.
        self.reasoner = reasoner
        self.planner = planner or Planner()
        self.prompt_builder = prompt_builder or PromptBuilder()

    # -- Guardrail Hooks (stub — see module docstring) ----------------------

    async def check_permissions(self, action: str) -> bool:
        """Always True today. This is the seam the Guardrail Layer
        (section 29) will call into once it exists — don't remove it
        just because it's a no-op right now."""
        return True

    # -- the run loop every subclass shares ---------------------------------

    async def run(
        self,
        tool_manager: ToolManager,
        seller_id: str,
        user_query: str,
        session: Optional[MarketplaceSession] = None,
        conversation_history: Optional[list[dict[str, str]]] = None,
        business_rules: Optional[dict[str, Any]] = None,
    ) -> AgentResult:
        context_builder = ContextBuilder(tool_manager)
        executor = Executor(tool_manager)

        state = AgentState(user_query=user_query)

        context = await context_builder.build(
            seller_id=seller_id,
            user_query=user_query,
            session=session,
            include=self.context_sections,
            conversation_history=conversation_history,
            business_rules=business_rules,
        )
        state.retrieved_context = {k: v.content for k, v in context.sections.items() if v.available}

        state.plan = self.planner.create_plan(self.default_plan, user_query, overrides=self.override_plan)

        async def _step_handler(step: dict[str, Any], s: AgentState) -> Any:
            return await self.handle_step(step, s, context)

        state = await executor.run_plan(state, session=session, step_handler=_step_handler)

        return self.format_output(state)

    # -- subclass hooks ------------------------------------------------------

    def override_plan(self, plan: list[dict[str, Any]], user_query: str) -> list[dict[str, Any]]:
        """Optional per-query plan adjustment. Default: no-op (return
        the static default_plan unchanged). Override in a subclass for
        query-dependent adjustments (see planner.py)."""
        return plan

    @abstractmethod
    async def handle_step(
        self, step: dict[str, Any], state: AgentState, context: Any
    ) -> Any:
        """Runs this agent's own non-tool plan steps (the {"step": ...}
        entries Executor hands back — see executor.py). Every
        specialized agent must implement this; there's no sensible
        shared default because what a "generate_listing" step actually
        does is entirely agent-specific."""
        raise NotImplementedError

    def format_output(self, state: AgentState) -> AgentResult:
        """Default Output Formatter: maps AgentState -> AgentResult.
        Subclasses may override for agent-specific data/artifacts, but
        most won't need to — this covers the common case of "final
        answer is text, tool_calls/errors carry the rest"."""
        if state.has_errors() and state.final_response is None:
            return AgentResult.fail(
                message="; ".join(state.errors),
                tool_calls=state.tool_results,
            )
        return AgentResult.ok(
            message=state.final_response or "",
            confidence=state.confidence,
            tool_calls=state.tool_results,
            metadata={"errors": state.errors} if state.errors else {},
        )

"""
supervisor.py — the Supervisor Layer, sitting ABOVE orchestrator.py.

    User / Backend API
          |
          v
      Supervisor            <- this file
          |
   Execution Plan
          |
          v
  LangGraph Orchestrator    (orchestrator.py)
          |
          v
  Specialized Agents -> Tools -> Connectors -> Marketplace

Why this exists as a separate file, not a graph node
-----------------------------------------------------------------------
Putting a "Supervisor" node inside the LangGraph orchestrator means it
can only ever do one pass of routing before LangGraph's own machinery
takes over — awkward for anything that needs to decide *before*
execution starts whether to run the graph at all, run it more than
once, or answer straight from memory with no workflow. Keeping it
outside means it can:

  - recall memory and decide up front whether a workflow is even
    needed (a pure Q&A the recalled context already answers doesn't
    need to enter the graph),
  - decompose a query that touches multiple intents into an ordered
    plan (see TaskDecomposer below) before a single node executes,
  - own the conversation's memory lifecycle (start/record/summarize)
    end-to-end, across possibly several orchestrator runs,
  - manage the human-approval pause/resume cycle as its own concern,
    not something the caller has to know LangGraph-specific details
    (thread_id, interrupt_before) to drive.

The Orchestrator still owns everything execution-shaped: state
transitions, retries, parallel branches, guardrail enforcement,
publishing. The Supervisor never touches a Tool or Connector directly
and never imports LangGraph — it only ever calls
`orchestrator.run_workflow()` / `orchestrator.resume_workflow()`.

Internal components (deliberately small, single-purpose classes/
functions rather than one large Supervisor god-class):

    IntentAnalyzer     - what does the user want, which marketplace
    TaskDecomposer      - one query -> one or more ordered plan steps
    MemoryCoordinator   - recall before deciding, record after responding
    ApprovalManager     - interpret a paused orchestrator run, drive resume
    ResponseSynthesizer - shape the final dict handed back to the caller

None of these are meant to be over-engineered ahead of need — they're
real, working code today, but intentionally the smallest version of
each responsibility that's still genuinely useful, so growing any one
of them later (e.g. an LLM-driven IntentAnalyzer instead of keyword
matching) doesn't require touching the others.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import backend.ai.orchestrator_layer.orchestrator as orchestrator
from backend.ai.orchestrator_layer.orchestrator import router as intent_router  # the existing IntentRouter, reused rather than duplicated


# =============================================================================
# Execution Plan — what the Supervisor produces, what the Orchestrator consumes
# =============================================================================

@dataclass
class ExecutionStep:
    action: str  # matches an AGENT_FOR_INTENT-style intent, e.g. "inventory", "listing"
    status: str = "pending"

    def as_dict(self) -> Dict[str, Any]:
        return {"action": self.action, "status": self.status}


@dataclass
class ExecutionPlan:
    intents: List[str]
    steps: List[ExecutionStep]
    marketplace: Optional[str]
    approval_likely: bool

    def as_state_plan(self) -> List[Dict[str, Any]]:
        """Shape orchestrator.new_state(plan=...) expects: list[dict]."""
        return [step.as_dict() for step in self.steps]


# =============================================================================
# IntentAnalyzer + TaskDecomposer
# =============================================================================

# Intents whose corresponding agent isn't registered yet (kept in sync
# with orchestrator.AGENT_NODE_TO_REGISTRY_KEY) — surfaced here so the
# Supervisor can tell the user plainly up front, rather than only after
# a graph run comes back with "not implemented yet".
_UNIMPLEMENTED_INTENTS = {
    intent
    for intent, agent_node in orchestrator.AGENT_FOR_INTENT.items()
    if orchestrator.AGENT_NODE_TO_REGISTRY_KEY.get(agent_node) is None
}

# Mutating intents very likely to trip HumanApprovalRule/MarketplacePolicyRule
# in guardrails.py — used only to set expectations in the response, the
# guardrail engine itself remains the actual source of truth.
_LIKELY_APPROVAL_INTENTS = {"create_listing", "update_listing", "pricing", "inventory"}


class IntentAnalyzer:
    """Thin wrapper over orchestrator.IntentRouter — kept as its own
    class so swapping in an LLM-driven analyzer later only means
    changing this one class, not TaskDecomposer or the Supervisor."""

    def detect_intents(self, query: str) -> List[str]:
        """
        Returns every matching intent, not just the first — this is
        what lets TaskDecomposer build a multi-step plan for a query
        that touches more than one concern (e.g. "...and tell me why
        sales dropped" alongside a listing request).
        """
        q = query.lower()
        matched = [
            intent
            for intent, keywords in orchestrator.INTENT_KEYWORDS.items()
            if any(keyword in q for keyword in keywords)
        ]
        return matched or ["unknown"]

    def detect_marketplace(self, query: str) -> Optional[str]:
        return intent_router.detect_marketplace(query)


class TaskDecomposer:
    def __init__(self, analyzer: IntentAnalyzer) -> None:
        self._analyzer = analyzer

    def build_plan(self, query: str) -> ExecutionPlan:
        intents = self._analyzer.detect_intents(query)
        marketplace = self._analyzer.detect_marketplace(query)

        steps = [ExecutionStep(action=intent) for intent in intents if intent != "unknown"]
        if not steps:
            # "unknown" still needs *something* to run — fall back to
            # Seller Coach, same default orchestrator.IntentRouter.select_agent uses.
            steps = [ExecutionStep(action="seller_coach")]

        approval_likely = any(intent in _LIKELY_APPROVAL_INTENTS for intent in intents)
        return ExecutionPlan(intents=intents, steps=steps, marketplace=marketplace, approval_likely=approval_likely)

    def unimplemented_intents(self, plan: ExecutionPlan) -> List[str]:
        return [i for i in plan.intents if i in _UNIMPLEMENTED_INTENTS]


# =============================================================================
# MemoryCoordinator
# =============================================================================

class MemoryCoordinator:
    """
    Owns the conversation's memory lifecycle. Safe to use with
    session_id=None (a stateless one-off query) — every method is a
    no-op in that case rather than requiring the caller to branch.
    """

    def __init__(self) -> None:
        self._service = orchestrator.memory_service

    def ensure_session(self, session_id: Optional[str], seller_id: str) -> None:
        if not session_id or self._service is None:
            return
        existing = self._service.retriever.get_conversation(session_id)
        if existing is None:
            self._service.start_conversation(session_id, seller_id)

    def record_user_message(self, session_id: Optional[str], query: str) -> None:
        if not session_id or self._service is None:
            return
        self._service.record_message(session_id, "user", query)

    def record_assistant_message(self, session_id: Optional[str], response: Optional[str]) -> None:
        if not session_id or self._service is None or not response:
            return
        self._service.record_message(session_id, "assistant", response)


# =============================================================================
# ApprovalManager
# =============================================================================

@dataclass
class SupervisorResult:
    response: str
    intent: List[str]
    marketplace: Optional[str]
    awaiting_approval: bool
    thread_id: Optional[str]
    guardrail_findings: List[str] = field(default_factory=list)
    unimplemented_intents: List[str] = field(default_factory=list)
    raw_state: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "intent": self.intent,
            "marketplace": self.marketplace,
            "awaiting_approval": self.awaiting_approval,
            "thread_id": self.thread_id,
            "guardrail_findings": self.guardrail_findings,
            "unimplemented_intents": self.unimplemented_intents,
        }


class ApprovalManager:
    """
    Interprets whatever state orchestrator.run_workflow()/resume_workflow()
    hands back. LangGraph's `interrupt_before=["approval"]` means a
    paused run simply returns the state as of the last completed node
    — there's no exception or special "paused" object to catch, so
    "are we waiting on a human" is a plain field check, done in one
    place here instead of in every caller.
    """

    @staticmethod
    def is_awaiting_approval(state: Dict[str, Any]) -> bool:
        return bool(state.get("approval_required")) and state.get("published_status") is None and state.get(
            "error"
        ) != "blocked_by_guardrail"


# =============================================================================
# ResponseSynthesizer
# =============================================================================

class ResponseSynthesizer:
    @staticmethod
    def from_state(state: Dict[str, Any], plan: ExecutionPlan, thread_id: Optional[str], unimplemented: List[str]) -> SupervisorResult:
        return SupervisorResult(
            response=state.get("final_response") or "",
            intent=plan.intents,
            marketplace=state.get("marketplace") or plan.marketplace,
            awaiting_approval=ApprovalManager.is_awaiting_approval(state),
            thread_id=thread_id,
            guardrail_findings=state.get("guardrail_findings", []),
            unimplemented_intents=unimplemented,
            raw_state=state,
        )


# =============================================================================
# Supervisor — the entry point everything above composes into
# =============================================================================

class Supervisor:
    def __init__(self) -> None:
        self._analyzer = IntentAnalyzer()
        self._decomposer = TaskDecomposer(self._analyzer)
        self._memory = MemoryCoordinator()

    async def handle(
        self,
        query: str,
        seller_id: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        The one method a Backend API layer should call for a fresh
        user turn. Returns a plain dict (see SupervisorResult.as_dict) —
        no LangGraph types, no orchestrator internals leak through.

        seller_id is required, on purpose, with no fallback default.
        This used to default to "default_seller" — convenient for
        early testing, but a real liability once a backend with real
        auth calls this: if an auth-middleware bug ever fails to
        attach a real seller_id, a silent default would route that
        request into a shared bucket instead of failing — mixing one
        seller's conversation history and marketplace data with
        another's, discovered only much later. Failing loudly here,
        at the one entry point every backend request passes through,
        is a lot cheaper than finding that bug in production.
        """
        if not seller_id or not seller_id.strip():
            raise ValueError(
                "Supervisor.handle() requires a real seller_id — the caller "
                "(the backend's Chat API) must resolve this from the "
                "authenticated request before calling handle(), not leave "
                "it blank or rely on a default."
            )

        self._memory.ensure_session(session_id, seller_id)
        self._memory.record_user_message(session_id, query)

        plan = self._decomposer.build_plan(query)
        unimplemented = self._decomposer.unimplemented_intents(plan)

        thread_id = session_id or seller_id
        state = await orchestrator.run_workflow(
            query=query,
            seller_id=seller_id,
            marketplace=plan.marketplace,
            session_id=session_id,
            plan=plan.as_state_plan(),
            thread_id=thread_id,
        )

        result = ResponseSynthesizer.from_state(state, plan, thread_id, unimplemented)
        self._memory.record_assistant_message(session_id, result.response)
        return result.as_dict()

    async def resume(
        self,
        thread_id: str,
        approval_granted: bool,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Continue a run that paused at the human-approval checkpoint."""
        state = await orchestrator.resume_workflow(thread_id=thread_id, approval_granted=approval_granted)

        # No original ExecutionPlan is available post-resume (LangGraph's
        # checkpoint doesn't round-trip our dataclass) — reconstruct just
        # enough of one from the resumed state for ResponseSynthesizer.
        plan = ExecutionPlan(
            intents=[state.get("intent")] if state.get("intent") else [],
            steps=[],
            marketplace=state.get("marketplace"),
            approval_likely=False,
        )
        result = ResponseSynthesizer.from_state(state, plan, thread_id, unimplemented=[])
        self._memory.record_assistant_message(session_id, result.response)
        return result.as_dict()


# Module-level singleton — same pattern as orchestrator.sellerOS_graph /
# guardrails.guardrail_engine / agent_registry: one shared instance, not
# rebuilt per request.
supervisor = Supervisor()

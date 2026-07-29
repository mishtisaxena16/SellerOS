"""
models.py — the reusable ExecutionPlan/ExecutionStep shape (Phase 6.1, Task 1).

Deliberately plain dataclasses, no LangGraph/pydantic dependency, so this
module can be imported from anywhere (Supervisor layer today, the future
multi-agent Executor in a later phase) without dragging in unrelated
machinery. `backend/schema/chat.py` has the pydantic mirror of this shape
for the actual HTTP response contract — this module is the internal,
framework-free source of truth that gets converted to that schema at the
API boundary.

NOTE ON NAMING: `backend/ai/supervisor_layer/supervisor.py` already
defines its own small `ExecutionPlan`/`ExecutionStep` classes, used
internally to seed `SellerOSState["plan"]` for the LangGraph orchestrator.
That is a different concern (one flat list of intent-steps fed into an
already-running graph) from what Phase 6.1 asks for (a rich, displayable,
pre-execution plan naming *which agents* would run and *why*, before
anything executes). Both are legitimately named `ExecutionPlan` /
`ExecutionStep` per their own module's spec; they are not the same class
and are never imported into the same namespace under the same name. See
supervisor.py's integration comment for how the two are kept apart.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class ExecutionStatus(str, Enum):
    """Every status an ExecutionStep can be in.

    Phase 6.1 only ever produces PENDING steps (no agent has executed
    yet). RUNNING/COMPLETED/FAILED/SKIPPED exist now so the *shape* is
    already correct for the future multi-agent Executor (a later phase)
    to update in place, without a breaking schema change.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    """One planned agent invocation.

    agent_id        - stable key, e.g. "analytics" (matches, where one
                       exists, the key an agent is registered under in
                       backend/ai/agent_layer/registry/agent_registry.py —
                       see AgentPlanner's AGENT_CATALOG for the mapping).
    display_name     - human-readable label for UI/logging, e.g. "Analytics Agent".
    reason            - short, human-readable explanation of *why* this
                       agent was included in the plan for this query.
    status            - one of ExecutionStatus; always "pending" out of
                       AgentPlanner today.
    execution_order   - 1-based position this step would run in. Seller
                       Coach always receives the highest execution_order
                       in its plan (see AgentPlanner._assign_execution_order).
    """

    agent_id: str
    display_name: str
    reason: str
    execution_order: int
    status: str = ExecutionStatus.PENDING.value

    def as_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "display_name": self.display_name,
            "reason": self.reason,
            "status": self.status,
            "execution_order": self.execution_order,
        }


@dataclass
class ExecutionPlan:
    """An ordered collection of ExecutionSteps for a single user query."""

    steps: List[ExecutionStep] = field(default_factory=list)

    def as_list(self) -> List[Dict[str, Any]]:
        """Steps sorted by execution_order, each as a plain dict — this
        is the exact shape `ChatResponse.execution_plan` expects."""
        return [step.as_dict() for step in sorted(self.steps, key=lambda s: s.execution_order)]

    @property
    def agent_ids(self) -> List[str]:
        return [step.agent_id for step in sorted(self.steps, key=lambda s: s.execution_order)]

    def is_empty(self) -> bool:
        return not self.steps

from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    session_id: str | None = None


class ExecutionStepSchema(BaseModel):
    """
    Phase 6.1 — Agent Execution Planner. Pydantic mirror of
    `backend.ai.planner_layer.models.ExecutionStep`, for the HTTP
    response contract specifically. No agent has actually executed when
    this is returned — `status` is always "pending" today.
    """

    agent_id: str
    display_name: str
    reason: str
    status: str
    execution_order: int


class ChatResponse(BaseModel):
    response: str
    intent: list[str] = []
    marketplace: Optional[str] = None
    awaiting_approval: bool = False
    thread_id: str | None = None
    guardrail_findings: list[str] = []
    unimplemented_intents: list[str] = []
    # Phase 6.1 — additive only. Existing clients that don't read this
    # field are unaffected; every field above is unchanged.
    execution_plan: list[ExecutionStepSchema] = []
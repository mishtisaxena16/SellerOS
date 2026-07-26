from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    intent: list[str] = []
    marketplace: Optional[str] = None
    awaiting_approval: bool = False
    thread_id: str | None = None
    guardrail_findings: list[str] = []
    unimplemented_intents: list[str] = []
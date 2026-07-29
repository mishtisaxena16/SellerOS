from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from backend.api.dependencies import get_current_seller
from backend.model.seller import Seller
from backend.schema.chat import (
    ChatRequest,
    ChatResponse,
    ApprovalRequest,
)

from backend.ai.supervisor_layer.supervisor import (
    supervisor,
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    seller: Seller = Depends(
        get_current_seller
    ),
):
    try:
        # supervisor.handle() returns SupervisorResult.as_dict() — a
        # plain dict, not an object. Attribute access here (result.response)
        # would raise AttributeError on every single call.
        result = await supervisor.handle(
            query=request.message,
            seller_id=str(seller.id),
            session_id=request.session_id,
        )

        return ChatResponse(
            response=result["response"],
            intent=result["intent"],
            marketplace=result["marketplace"],
            awaiting_approval=result["awaiting_approval"],
            thread_id=result["thread_id"],
            guardrail_findings=result["guardrail_findings"],
            unimplemented_intents=result["unimplemented_intents"],
            # Phase 6.1 — result["agent_execution_plan"] is always present
            # (defaults to [] in SupervisorResult), so this is safe for
            # both this endpoint and /approve below.
            execution_plan=result.get("agent_execution_plan", []),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post(
    "/approve",
    response_model=ChatResponse,
)
async def approve(
    request: ApprovalRequest,
    seller: Seller = Depends(
        get_current_seller
    ),
):
    """
    Resumes a run that paused at the human-approval checkpoint
    (result.awaiting_approval == True from a prior /chat call).
    Without this endpoint, Supervisor.resume() — the other half of the
    approval flow the AI runtime already supports — was never callable
    from outside a test script.
    """
    try:
        result = await supervisor.resume(
            thread_id=request.thread_id,
            approval_granted=request.approved,
            session_id=request.session_id,
        )

        return ChatResponse(
            response=result["response"],
            intent=result["intent"],
            marketplace=result["marketplace"],
            awaiting_approval=result["awaiting_approval"],
            thread_id=result["thread_id"],
            guardrail_findings=result["guardrail_findings"],
            unimplemented_intents=result["unimplemented_intents"],
            # Phase 6.1 — no original query is available on resume, so
            # there's nothing to re-plan from; empty is the correct,
            # honest answer rather than guessing.
            execution_plan=result.get("agent_execution_plan", []),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
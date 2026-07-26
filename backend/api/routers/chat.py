from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from backend.api.dependencies import get_current_seller
from backend.model.seller import Seller
from backend.schema.chat import (
    ChatRequest,
    ChatResponse,
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

        result = await supervisor.handle(
            query=request.message,
            seller_id=str(seller.id),
            session_id=request.session_id,
        )
        

        return ChatResponse(
            response=result.response,
            awaiting_approval=result.awaiting_approval,
            thread_id=result.thread_id,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
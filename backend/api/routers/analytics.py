from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    get_current_seller,
)
from backend.database.session import get_db
from backend.model.seller import Seller
from backend.service.marketplace_data_service import (
    get_analytics,
    NoMarketplaceConnectedError,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("")
async def read_analytics(
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
    seller: Seller = Depends(
        get_current_seller
    ),
):
    try:
        return await get_analytics(db, seller.id, platform)
    except NoMarketplaceConnectedError as e:
        raise HTTPException(status_code=409, detail=str(e))

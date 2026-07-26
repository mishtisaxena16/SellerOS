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
    get_inventory,
    NoMarketplaceConnectedError,
)

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)


@router.get("")
async def read_inventory(
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
    seller: Seller = Depends(
        get_current_seller
    ),
):
    try:
        return await get_inventory(db, seller.id, platform)
    except NoMarketplaceConnectedError as e:
        raise HTTPException(status_code=409, detail=str(e))

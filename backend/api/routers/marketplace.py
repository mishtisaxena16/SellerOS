from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    get_current_seller,
)
from backend.database.session import get_db
from backend.model.seller import Seller
from backend.schema.marketplace import (
    ConnectMarketplaceRequest,
    MarketplaceResponse,
)
from backend.service.marketplace_service import (
    MarketplaceService,
)

router = APIRouter(
    prefix="/marketplaces",
    tags=["Marketplaces"],
)

@router.post("/connect", response_model=MarketplaceResponse)
def connect_marketplace(
    request: ConnectMarketplaceRequest,
    db: Session = Depends(get_db),
    seller: Seller = Depends(
        get_current_seller
    ),
):

    return MarketplaceService.connect_marketplace(
        db=db,
        seller_id=seller.id,
        platform=request.platform,
        credentials=request.credentials,
    )
    
@router.get("", response_model=List[MarketplaceResponse])
def get_marketplaces(
    db: Session = Depends(get_db),
    seller: Seller = Depends(
        get_current_seller
    ),
):

    return MarketplaceService.get_marketplaces(
        db=db,
        seller_id=seller.id,
    )

@router.delete("/{marketplace_id}")
def delete_marketplace(
    marketplace_id: int,
    db: Session = Depends(get_db),
    seller: Seller = Depends(
        get_current_seller
    ),
):
    # delete_marketplace raises ValueError when the account doesn't
    # exist or belongs to another seller. Without this catch, that
    # ValueError propagated straight out of the route handler as a bare
    # 500 with a Python traceback instead of a clean, expected 404.
    try:
        MarketplaceService.delete_marketplace(
            db=db,
            seller_id=seller.id,
            marketplace_id=marketplace_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    return {
        "message": "Marketplace deleted successfully"
    }
    

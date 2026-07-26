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
)
from backend.service.marketplace_service import (
    MarketplaceService,
)

router = APIRouter(
    prefix="/marketplaces",
    tags=["Marketplaces"],
)

@router.post("/connect")
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
    
@router.get("")
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

    MarketplaceService.delete_marketplace(
        db=db,
        seller_id=seller.id,
        marketplace_id=marketplace_id,
    )

    return {
        "message": "Marketplace deleted successfully"
    }
    

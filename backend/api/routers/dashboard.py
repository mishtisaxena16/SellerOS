from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    get_current_seller,
)
from backend.database.session import get_db
from backend.model.seller import Seller
from backend.service.dashboard_service import (
    DashboardService,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)

@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    seller: Seller = Depends(
        get_current_seller
    ),
):

    return DashboardService.get_summary(
        db=db,
        seller_id=seller.id,
    )
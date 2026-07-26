from fastapi import APIRouter
from fastapi import Depends

from backend.api.dependencies import (
    get_current_seller,
)
from backend.model.seller import Seller

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("")
def get_analytics(
    seller: Seller = Depends(
        get_current_seller
    ),
):
    return {
        "sales": 100000,
        "orders": 200,
        "conversion_rate": 4.2,
    }
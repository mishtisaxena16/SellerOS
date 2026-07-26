from fastapi import APIRouter
from fastapi import Depends

from backend.api.dependencies import (
    get_current_seller,
)
from backend.model.seller import Seller

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.get("")
def get_orders(
    seller: Seller = Depends(
        get_current_seller
    ),
):
    return [
        {
            "order_id": "ORD001",
            "status": "Pending",
        },
        {
            "order_id": "ORD002",
            "status": "Shipped",
        },
    ]
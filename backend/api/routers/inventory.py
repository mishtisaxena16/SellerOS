from fastapi import APIRouter
from fastapi import Depends

from backend.api.dependencies import (
    get_current_seller,
)
from backend.model.seller import Seller

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)


@router.get("")
def get_inventory(
    seller: Seller = Depends(
        get_current_seller
    ),
):
    return [
        {
            "sku": "SKU001",
            "title": "Bluetooth Speaker",
            "stock": 12,
        },
        {
            "sku": "SKU002",
            "title": "Wireless Mouse",
            "stock": 8,
        },
    ]
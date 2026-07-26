from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schema.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
)
from backend.service.auth_service import AuthService
from backend.api.dependencies import (
    get_current_seller,
)

from backend.model.seller import Seller

from backend.schema.auth import (
    CurrentUserResponse,
)
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=TokenResponse,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        return AuthService.register_user(
            db=db,
            email=request.email,
            password=request.password,
            business_name=request.business_name,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        return AuthService.login_user(
            db=db,
            email=request.email,
            password=request.password,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )

@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
def get_me(
    seller: Seller = Depends(
        get_current_seller
    ),
):

    return {
        "user_id": seller.user.id,
        "seller_id": seller.id,
        "email": seller.user.email,
        "business_name": seller.business_name,
    }
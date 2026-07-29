from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schema.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UpdateProfileRequest,
    ChangePasswordRequest,
)
from backend.service.auth_service import AuthService
from backend.api.dependencies import (
    get_current_seller,
    get_current_user,
)

from backend.model.seller import Seller
from backend.model.user import User

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


@router.patch(
    "/me",
    response_model=CurrentUserResponse,
)
def update_me(
    request: UpdateProfileRequest,
    db: Session = Depends(get_db),
    seller: Seller = Depends(
        get_current_seller
    ),
):
    updated = AuthService.update_profile(
        db=db,
        seller=seller,
        business_name=request.business_name,
    )

    return {
        "user_id": updated.user.id,
        "seller_id": updated.id,
        "email": updated.user.email,
        "business_name": updated.business_name,
    }


@router.post(
    "/change-password",
    status_code=204,
)
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(
        get_current_user
    ),
):
    try:
        AuthService.change_password(
            db=db,
            user=user,
            current_password=request.current_password,
            new_password=request.new_password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
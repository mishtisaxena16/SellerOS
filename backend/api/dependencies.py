from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from backend.auth.jwt import decode_access_token
from backend.database.session import get_db
from backend.model.user import User
from backend.model.seller import Seller


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:

    payload = decode_access_token(
        credentials.credentials
    )

    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user


def get_current_seller(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Seller:

    seller = (
        db.query(Seller)
        .filter(
            Seller.user_id == current_user.id
        )
        .first()
    )

    if not seller:
        raise HTTPException(
            status_code=404,
            detail="Seller not found",
        )

    return seller
from sqlalchemy.orm import Session

from backend.auth.jwt import create_access_token
from backend.auth.password import hash_password
from backend.auth.password import verify_password
from backend.model.user import User
from backend.model.seller import Seller


class AuthService:
    """
    Authentication business logic.
    """

    @staticmethod
    def register_user(
        db: Session,
        email: str,
        password: str,
        business_name: str,
    ) -> dict:
        """
        Register a new user and seller account.
        """

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            raise ValueError(
                "User with this email already exists."
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
        )

        db.add(user)
        db.flush()

        seller = Seller(
            user_id=user.id,
            business_name=business_name,
        )

        db.add(seller)

        db.commit()

        db.refresh(user)
        db.refresh(seller)

        token = create_access_token(
            {
                "user_id": user.id,
                "seller_id": seller.id,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    @staticmethod
    def login_user(
        db: Session,
        email: str,
        password: str,
    ) -> dict:
        """
        Authenticate existing user.
        """

        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if not user:
            raise ValueError(
                "Invalid email or password."
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise ValueError(
                "Invalid email or password."
            )

        seller = (
            db.query(Seller)
            .filter(Seller.user_id == user.id)
            .first()
        )

        token = create_access_token(
            {
                "user_id": user.id,
                "seller_id": seller.id,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }
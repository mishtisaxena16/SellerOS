from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict

from jose import JWTError
from jose import jwt

from backend.config.settings import settings


def create_access_token(
    data: Dict[str, Any]
) -> str:
    """
    Create a JWT access token.
    """

    payload = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload["exp"] = expire

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token


def decode_access_token(
    token: str
) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        return payload

    except JWTError:
        return {}
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field


class RegisterRequest(BaseModel):
    """
    Request schema for user registration.
    """

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )

    business_name: str = Field(
        min_length=1,
        max_length=255
    )


class LoginRequest(BaseModel):
    """
    Request schema for login.
    """

    email: EmailStr

    password: str


class TokenResponse(BaseModel):
    """
    JWT response.
    """

    access_token: str

    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    """
    Response for authenticated user.
    """

    user_id: int

    seller_id: int

    email: str

    business_name: str


class UpdateProfileRequest(BaseModel):
    """
    Request schema for updating the seller's own profile.

    Only fields the backend actually models (business_name) can be
    updated here — there's no phone/GSTIN/photo storage yet.
    """

    business_name: str = Field(
        min_length=1,
        max_length=255,
    )


class ChangePasswordRequest(BaseModel):
    """
    Request schema for changing the current user's password.
    """

    current_password: str

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )
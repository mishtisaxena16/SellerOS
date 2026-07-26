from pydantic import BaseModel
from pydantic import Field


class ConnectMarketplaceRequest(BaseModel):
    platform: str = Field(
        min_length=1,
        max_length=50,
    )

    credentials: dict


class MarketplaceResponse(BaseModel):
    id: int
    platform: str
    credentials: dict

    class Config:
        from_attributes = True
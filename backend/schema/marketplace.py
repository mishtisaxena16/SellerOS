from datetime import datetime

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

# The three platforms the Connector Layer actually supports
# (backend/ai/connectors_layer/*_connector.py). Anything else is
# accepted into the DB with a 200 today and then silently does
# nothing useful, because session_store/orchestrator only know how
# to build sessions for these.
SUPPORTED_PLATFORMS = {"amazon", "flipkart", "meesho"}


class ConnectMarketplaceRequest(BaseModel):
    platform: str = Field(
        min_length=1,
        max_length=50,
    )

    credentials: dict

    @field_validator("platform")
    @classmethod
    def platform_must_be_supported(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_PLATFORMS:
            raise ValueError(
                f"Unsupported platform '{value}'. "
                f"Supported platforms: {', '.join(sorted(SUPPORTED_PLATFORMS))}."
            )
        return normalized


class MarketplaceResponse(BaseModel):
    """
    Deliberately excludes `credentials`. This is returned directly from
    POST /marketplaces/connect and GET /marketplaces, both of which sit
    behind normal seller auth but are still logged, cached by browsers/
    proxies, and visible to anything with access to the response body —
    none of which should ever see a seller's stored API keys/tokens back
    in plaintext, even though they own the account.
    """
    id: int
    platform: str
    created_at: datetime

    class Config:
        from_attributes = True
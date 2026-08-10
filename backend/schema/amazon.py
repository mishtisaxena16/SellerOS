from pydantic import BaseModel


class AmazonAuthorizeResponse(BaseModel):
    """Returned by GET /marketplaces/amazon/authorize -- the frontend
    redirects the seller's browser to `authorization_url` to start the
    Connect Amazon flow."""
    authorization_url: str


class AmazonCallbackResponse(BaseModel):
    """Returned by GET /marketplaces/amazon/callback once the OAuth
    exchange completes successfully."""
    status: str
    platform: str
    message: str

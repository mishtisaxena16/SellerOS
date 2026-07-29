from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    get_current_seller,
)
from backend.database.session import get_db
from backend.model.seller import Seller
from backend.schema.marketplace import (
    ConnectMarketplaceRequest,
    MarketplaceResponse,
)
from backend.schema.amazon import (
    AmazonAuthorizeResponse,
    AmazonCallbackResponse,
)
from backend.service.marketplace_service import (
    MarketplaceService,
)
from backend.service.amazon_auth_service import AmazonAuthService
from backend.ai.connectors_layer.exceptions import AuthenticationError, InvalidCredentialsError

router = APIRouter(
    prefix="/marketplaces",
    tags=["Marketplaces"],
)

@router.post("/connect", response_model=MarketplaceResponse)
def connect_marketplace(
    request: ConnectMarketplaceRequest,
    db: Session = Depends(get_db),
    seller: Seller = Depends(
        get_current_seller
    ),
):

    return MarketplaceService.connect_marketplace(
        db=db,
        seller_id=seller.id,
        platform=request.platform,
        credentials=request.credentials,
    )
    
@router.get("", response_model=List[MarketplaceResponse])
def get_marketplaces(
    db: Session = Depends(get_db),
    seller: Seller = Depends(
        get_current_seller
    ),
):

    return MarketplaceService.get_marketplaces(
        db=db,
        seller_id=seller.id,
    )

@router.delete("/{marketplace_id}")
def delete_marketplace(
    marketplace_id: int,
    db: Session = Depends(get_db),
    seller: Seller = Depends(
        get_current_seller
    ),
):
    # delete_marketplace raises ValueError when the account doesn't
    # exist or belongs to another seller. Without this catch, that
    # ValueError propagated straight out of the route handler as a bare
    # 500 with a Python traceback instead of a clean, expected 404.
    try:
        MarketplaceService.delete_marketplace(
            db=db,
            seller_id=seller.id,
            marketplace_id=marketplace_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    return {
        "message": "Marketplace deleted successfully"
    }


# ---------------------------------------------------------------------------
# Amazon "Connect Amazon" OAuth (Website Authorization Workflow)
# ---------------------------------------------------------------------------
# Two-step flow, kept as separate routes (not reusing POST /connect above)
# because the second step is Amazon redirecting the seller's *browser*
# back to us with query parameters -- it can't carry the Bearer token
# every other route here requires. See amazon_auth_service.py and
# amazon_sdk/auth.py for the CSRF/state-token mechanism that keeps this
# safe without one.

@router.get("/amazon/authorize", response_model=AmazonAuthorizeResponse)
def amazon_authorize(
    region: str = Query(default="eu", description="SP-API region: na, eu, or fe"),
    seller: Seller = Depends(get_current_seller),
):
    """
    Step 1: the seller (already logged into SellerOS) clicks "Connect
    Amazon". Returns the URL the frontend should redirect the browser
    to -- Amazon's own sign-in and consent pages. SellerOS never asks
    for the seller's Amazon credentials directly.
    """
    try:
        url = AmazonAuthService.build_authorize_url(seller_id=seller.id, region=region)
    except InvalidCredentialsError as e:
        # AMAZON_LWA_CLIENT_ID / AMAZON_APP_ID / AMAZON_OAUTH_REDIRECT_URI
        # missing from backend/.env -- a deployment/config problem, not
        # something the seller can fix, but still a clean 500 rather
        # than a raw traceback.
        raise HTTPException(status_code=500, detail=str(e))

    return AmazonAuthorizeResponse(authorization_url=url)


@router.get("/amazon/callback", response_model=AmazonCallbackResponse)
def amazon_callback(
    state: str = Query(...),
    spapi_oauth_code: str = Query(...),
    selling_partner_id: str | None = Query(default=None),
    region: str = Query(default="eu"),
    db: Session = Depends(get_db),
):
    """
    Step 2: Amazon redirects the seller's browser here after consent,
    with `state` (echoed back unmodified -- validated for CSRF) and
    `spapi_oauth_code` (exchanged for a refresh_token, which is what
    gets stored -- encrypted -- against this seller's account).

    Deliberately unauthenticated (no get_current_seller dependency):
    this request comes from the seller's browser being redirected by
    Amazon, not from an API client holding a Bearer token. `state`
    is what proves it's legitimate and identifies the seller.
    """
    try:
        result = AmazonAuthService.handle_callback(
            db=db,
            state=state,
            spapi_oauth_code=spapi_oauth_code,
            selling_partner_id=selling_partner_id,
            region=region,
        )
    except AuthenticationError as e:
        # Invalid/expired/tampered state, or the LWA code exchange
        # itself failed -- both are "this authorization attempt didn't
        # work," not a server bug.
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return AmazonCallbackResponse(
        status=result["status"],
        platform=result["platform"],
        message="Amazon account connected. You can close this window.",
    )
    

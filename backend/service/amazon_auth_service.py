"""
amazon_auth_service.py — the seller-facing half of the "Connect
Amazon" flow (Website Authorization Workflow). Sits at the same layer
as marketplace_service.py, and deliberately reuses it rather than
writing a parallel persistence path: once a refresh_token is in hand,
storing it is exactly the same "encrypt at rest, upsert, register into
session_store" job MarketplaceService.connect_marketplace already
does for every platform, so this service does not touch the DB or
session_store directly.
"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.orm import Session

from backend.ai.connectors_layer.amazon_sdk import auth as amazon_auth
from backend.ai.connectors_layer.exceptions import AuthenticationError
from backend.service.marketplace_service import MarketplaceService


class AmazonAuthService:

    @staticmethod
    def build_authorize_url(seller_id: int, region: str = "eu", beta: bool = False) -> str:
        """
        Step 1 of the flow: called when the seller clicks "Connect
        Amazon" on the frontend. Returns the URL the frontend should
        redirect the browser to -- Amazon's own login + consent
        screens. seller_id is embedded (signed) in the state
        parameter so the callback below can identify the seller
        without needing an Authorization header on that request.
        """
        return amazon_auth.build_authorization_url(seller_id=str(seller_id), region=region, beta=beta)

    @staticmethod
    def handle_callback(
        db: Session,
        state: str,
        spapi_oauth_code: str,
        selling_partner_id: str | None = None,
        region: str = "eu",
    ) -> Dict[str, Any]:
        """
        Step 2 of the flow: called by the OAuth redirect URI endpoint
        when Amazon redirects the seller's browser back.

        1. Validates `state` (CSRF check, recovers seller_id) --
           raises AuthenticationError if invalid/expired/tampered.
        2. Exchanges spapi_oauth_code for a refresh_token (must happen
           within 5 minutes of the code being issued).
        3. Persists the refresh_token via MarketplaceService, exactly
           like any other platform's connect flow -- encrypted at
           rest (backend/database/crypto.py), upserted, and
           registered into session_store so the AI runtime can use it
           immediately without a process restart.

        Never logs spapi_oauth_code, the refresh_token, or the access
        token -- only the seller_id and platform name.
        """
        seller_id = amazon_auth.validate_state(state)

        token_response = amazon_auth.exchange_code_for_refresh_token(spapi_oauth_code)
        refresh_token = token_response.get("refresh_token")
        if not refresh_token:
            raise AuthenticationError(
                "Amazon LWA token exchange did not return a refresh_token."
            )

        credentials: Dict[str, Any] = {
            "refresh_token": refresh_token,
            "region": region,
        }
        if selling_partner_id:
            credentials["selling_partner_id"] = selling_partner_id

        account = MarketplaceService.connect_marketplace(
            db=db,
            seller_id=int(seller_id),
            platform="amazon",
            credentials=credentials,
        )

        return {
            "seller_id": account.seller_id,
            "platform": account.platform,
            "status": "connected",
        }

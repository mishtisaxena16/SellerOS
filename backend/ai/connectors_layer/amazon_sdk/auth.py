"""
auth.py — Login with Amazon (LWA) OAuth 2.0, verified against the
official SP-API docs (developer-docs.amazon.com/sp-api):
"Website authorization workflow", "Authorize Public Applications",
"Connect to the SP-API", and the Oct-2023 changelog entry "SP-API no
longer requires AWS IAM or AWS Signature Version 4".

WORKFLOW IMPLEMENTED: Website Authorization Workflow (the flow the
task requires: seller clicks "Connect Amazon" on SellerOS's own site,
not the Selling Partner Appstore).

    1. Seller clicks "Connect Amazon" -> build_authorization_url()
    2. Amazon shows its own login + consent screens (SellerOS never
       sees the seller's Amazon password)
    3. Amazon redirects back to our OAuth redirect URI with
       ?state=...&spapi_oauth_code=...&selling_partner_id=...
    4. validate_state() checks the state we generated in step 1 came
       back unmodified (CSRF protection) and recovers which SellerOS
       seller_id initiated the flow
    5. exchange_code_for_refresh_token() trades spapi_oauth_code for a
       refresh_token (must happen within 5 minutes per the docs --
       spapi_oauth_code is short-lived)
    6. The refresh_token is what gets stored (encrypted -- see
       backend/database/crypto.py) via MarketplaceService; SellerOS
       never stores the seller's Amazon login/password, only Amazon's
       own long-lived OAuth credential.

SIGNING: SP-API dropped AWS Signature Version 4 / IAM entirely on
2 Oct 2023. Only a bearer LWA access token is required on API calls
now (see client.py) -- no request-signing code appears anywhere in
this SDK, intentionally.

CREDENTIALS: LWA client ID/secret and the Solution Provider
application ID are read from environment variables only
(AMAZON_LWA_CLIENT_ID / AMAZON_LWA_CLIENT_SECRET / AMAZON_APP_ID /
AMAZON_OAUTH_REDIRECT_URI) -- never hardcoded, never logged. The
per-seller refresh_token is the one credential SellerOS's own DB
stores (encrypted), because it's what's actually needed on every
future API call -- the LWA client id/secret are the same for every
seller and stay in .env only.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from backend.ai.connectors_layer.amazon_sdk.config import (
    LWA_TOKEN_URL,
    SELLER_CENTRAL_BASE,
)
from backend.ai.connectors_layer.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    MarketplaceUnavailableError,
)
from backend.config.settings import settings

# spapi_oauth_code expires 5 minutes after issue, and the docs warn
# the whole workflow can break past 10 minutes end-to-end -- 10
# minutes gives the state token the same outer bound as Amazon's own
# workflow, rather than an arbitrarily different one.
STATE_TTL_SECONDS = 600


# ---------------------------------------------------------------------------
# Credential loading (env only -- see module docstring)
# ---------------------------------------------------------------------------

def _env_or_raise(var_name: str, hint: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise InvalidCredentialsError(
            f"{var_name} is not set in backend/.env. {hint}"
        )
    return value


def _lwa_client_id() -> str:
    return _env_or_raise(
        "AMAZON_LWA_CLIENT_ID",
        "Get this from Seller Central > Develop Apps after registering your LWA security profile.",
    )


def _lwa_client_secret() -> str:
    return _env_or_raise(
        "AMAZON_LWA_CLIENT_SECRET",
        "Get this from the same LWA security profile as AMAZON_LWA_CLIENT_ID.",
    )


def _app_id() -> str:
    return _env_or_raise(
        "AMAZON_APP_ID",
        "The Solution Provider application ID (e.g. amzn1.sp.solution.xxxxx) from the Solution Provider Portal.",
    )


def _redirect_uri() -> str:
    return _env_or_raise(
        "AMAZON_OAUTH_REDIRECT_URI",
        "Must exactly match the OAuth Redirect URI registered for this application "
        "(e.g. https://app.selleros.com/marketplaces/amazon/callback).",
    )


# ---------------------------------------------------------------------------
# CSRF state token
# ---------------------------------------------------------------------------

def generate_state(seller_id: str) -> str:
    """
    Self-contained, HMAC-signed state token: carries seller_id + a
    nonce + an expiry, signed with the app's SECRET_KEY (same secret
    already required to be a real value in production -- see
    backend/config/settings.py's assert_secret_key_is_safe).

    Self-contained rather than looked up server-side because the OAuth
    callback is Amazon redirecting the seller's *browser* back to us --
    there is no Authorization header on that request to identify which
    seller this is. This is both how we recover the seller_id and the
    CSRF protection the SP-API docs require ("Validate state parameters
    to prevent cross-site request forgery").
    """
    nonce = base64.urlsafe_b64encode(os.urandom(16)).decode().rstrip("=")
    payload = {
        "seller_id": seller_id,
        "nonce": nonce,
        "exp": int(time.time()) + STATE_TTL_SECONDS,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(settings.SECRET_KEY.encode("utf-8"), raw, hashlib.sha256).digest()
    return (
        base64.urlsafe_b64encode(raw).decode().rstrip("=")
        + "."
        + base64.urlsafe_b64encode(signature).decode().rstrip("=")
    )


def validate_state(token: str) -> str:
    """Returns the seller_id encoded in a valid, unexpired, correctly-
    signed state token. Raises AuthenticationError otherwise -- this
    is the single choke point for rejecting a forged or replayed
    callback."""
    try:
        raw_b64, sig_b64 = token.split(".", 1)
        raw = base64.urlsafe_b64decode(raw_b64 + "==")
        signature = base64.urlsafe_b64decode(sig_b64 + "==")
    except Exception as exc:
        raise AuthenticationError(f"Malformed OAuth state parameter: {exc}") from exc

    expected_signature = hmac.new(settings.SECRET_KEY.encode("utf-8"), raw, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthenticationError("OAuth state signature mismatch -- possible CSRF attempt.")

    try:
        payload = json.loads(raw)
    except Exception as exc:
        raise AuthenticationError(f"OAuth state payload is not valid JSON: {exc}") from exc

    if payload.get("exp", 0) < time.time():
        raise AuthenticationError("OAuth state has expired -- please restart the Connect Amazon flow.")

    seller_id = payload.get("seller_id")
    if not seller_id:
        raise AuthenticationError("OAuth state is missing seller_id.")

    return str(seller_id)


# ---------------------------------------------------------------------------
# Authorization URL (Website Authorization Workflow)
# ---------------------------------------------------------------------------

def build_authorization_url(seller_id: str, region: str = "eu", beta: bool = False) -> str:
    """
    Builds the OAuth authorization URI a seller is redirected to when
    they click "Connect Amazon" -- Amazon's own sign-in + consent
    pages. SellerOS never sees the seller's Amazon credentials.

    `beta=True` adds version=beta, required while testing an
    application still in Draft status (per "Website authorization
    workflow" docs) -- remove once the app is published.
    """
    base = SELLER_CENTRAL_BASE.get(region)
    if not base:
        raise ValueError(
            f"Unsupported region '{region}'. Supported: {sorted(SELLER_CENTRAL_BASE)}."
        )

    params = {
        "application_id": _app_id(),
        "state": generate_state(seller_id),
        "redirect_uri": _redirect_uri(),
    }
    if beta:
        params["version"] = "beta"

    return f"{base}/apps/authorize/consent?{urlencode(params)}"


# ---------------------------------------------------------------------------
# Token exchange (LWA authorization server)
# ---------------------------------------------------------------------------

def _post_token_request(data: Dict[str, str]) -> Dict[str, Any]:
    try:
        response = requests.post(LWA_TOKEN_URL, data=data, timeout=15)
        response.raise_for_status()
    except requests.HTTPError as exc:
        # Deliberately not including `data` (contains client_secret /
        # refresh_token / auth code) in the exception message -- errors
        # from this function must never leak a secret into logs.
        raise AuthenticationError(
            f"Amazon LWA token request failed: {exc.response.status_code if exc.response is not None else ''} {exc}"
        ) from exc
    except requests.RequestException as exc:
        raise MarketplaceUnavailableError(f"Could not reach Amazon LWA token endpoint: {exc}") from exc

    return response.json()


def exchange_code_for_refresh_token(spapi_oauth_code: str) -> Dict[str, Any]:
    """
    Exchanges the short-lived spapi_oauth_code (from the OAuth
    callback) for a refresh_token + access_token. Must be called
    within 5 minutes of receiving the code (SP-API docs).
    Returns the raw LWA response: {access_token, refresh_token,
    token_type, expires_in}.
    """
    return _post_token_request(
        {
            "grant_type": "authorization_code",
            "code": spapi_oauth_code,
            "client_id": _lwa_client_id(),
            "client_secret": _lwa_client_secret(),
        }
    )


def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """Exchanges a long-lived refresh_token for a fresh (~1hr) access_token."""
    return _post_token_request(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": _lwa_client_id(),
            "client_secret": _lwa_client_secret(),
        }
    )


# ---------------------------------------------------------------------------
# Per-seller access-token cache
# ---------------------------------------------------------------------------

class _AccessTokenCache:
    """
    In-memory access-token cache, keyed per seller_id -- unlike
    flipkart_api_connector.FlipkartAuth's single global instance
    (Flipkart's placeholder connector is single-tenant), Amazon is
    multi-tenant: many sellers, each with their own refresh_token, so
    each needs its own cached access_token.

    Process-local and lost on restart, same tradeoff session_store.py
    already makes for credentials in general -- acceptable because an
    access token is cheap to re-derive from the (persisted, encrypted)
    refresh_token on the next call.
    """

    def __init__(self) -> None:
        self._tokens: Dict[str, tuple[str, float]] = {}

    def get(self, seller_id: str, refresh_token: str) -> str:
        cached = self._tokens.get(seller_id)
        if cached and time.time() < cached[1] - 30:
            return cached[0]

        payload = refresh_access_token(refresh_token)
        access_token = payload["access_token"]
        expires_at = time.time() + payload.get("expires_in", 3600)
        self._tokens[seller_id] = (access_token, expires_at)
        return access_token

    def clear(self, seller_id: Optional[str] = None) -> None:
        """Mostly for tests -- drop one seller's cached token, or all of them."""
        if seller_id is None:
            self._tokens.clear()
        else:
            self._tokens.pop(seller_id, None)


_token_cache = _AccessTokenCache()


def get_access_token(seller_id: str, refresh_token: str) -> str:
    """Returns a cached, still-valid access token, refreshing automatically
    (and re-caching) when the cached one is missing or about to expire."""
    return _token_cache.get(seller_id, refresh_token)

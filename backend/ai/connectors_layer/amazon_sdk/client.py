"""
client.py — shared SP-API HTTP client.

Every call goes through `call()`: resolves a valid access token (auto-
refreshing via auth.get_access_token), sends the request with the
bearer header SP-API now requires (no AWS SigV4 signing -- see
auth.py's module docstring), retries transient failures with backoff,
and translates HTTP error responses into the existing
connectors_layer.exceptions hierarchy so callers above this file never
see a raw `requests` exception or a bare status code.

Scope for this phase: the generic caller + pagination helper only.
Endpoint-specific wrappers (Orders, Inventory, Listings, ...) are
explicitly out of scope per the task's Phase 3 boundary and belong to
a later phase.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Iterator, Optional

import requests

from backend.ai.connectors_layer.amazon_sdk import auth as amazon_auth
from backend.ai.connectors_layer.amazon_sdk.config import REGION_ENDPOINTS
from backend.ai.connectors_layer.exceptions import (
    AuthenticationError,
    ConnectorError,
    MarketplaceUnavailableError,
    RateLimitError,
)

DEFAULT_TIMEOUT_SECONDS = 20
MAX_RETRIES = 3


def _base_url(region: str) -> str:
    base = REGION_ENDPOINTS.get(region)
    if not base:
        raise ValueError(
            f"Unsupported SP-API region '{region}'. Supported: {sorted(REGION_ENDPOINTS)}."
        )
    return base


def _resolve_refresh_token(session: Any) -> str:
    """
    `session` is a MarketplaceSession (marketplace_connector.py).
    Amazon's refresh_token lives in session.credentials['refresh_token']
    -- the same key session_store.py's env-var fallback already
    populates from AMAZON_REFRESH_TOKEN, and the same key
    MarketplaceService.connect_marketplace persists (encrypted) after
    the OAuth callback in this phase. session.refresh_token (the
    dedicated field on MarketplaceSession) is checked second, for any
    caller that sets it directly instead of going through credentials.
    """
    refresh_token = (session.credentials or {}).get("refresh_token") or session.refresh_token
    if not refresh_token:
        raise AuthenticationError(
            "No Amazon refresh token on this session -- the seller must complete "
            "the Connect Amazon OAuth flow before any live SP-API call can be made."
        )
    return refresh_token


def _resolve_region(session: Any) -> str:
    return (session.credentials or {}).get("region") or session.region or "eu"


def call(
    session: Any,
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    max_retries: int = MAX_RETRIES,
) -> Dict[str, Any]:
    """
    Makes one logical SP-API call, retrying transient failures.
    Returns the parsed JSON response body on success (2xx).
    """
    refresh_token = _resolve_refresh_token(session)
    region = _resolve_region(session)
    url = _base_url(region) + path

    attempt = 0
    while True:
        attempt += 1
        access_token = amazon_auth.get_access_token(session.seller_id, refresh_token)
        headers = {
            "x-amz-access-token": access_token,
            "content-type": "application/json",
        }

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            if attempt <= max_retries:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise MarketplaceUnavailableError(f"Could not reach SP-API ({region}) at {path}: {exc}") from exc

        # Rate-limited: back off and retry rather than failing the
        # caller outright -- SP-API's usage plans are token-bucket
        # based and a short wait is normally enough (getMarketplace
        # Participations' own limit is 0.016 rps / burst 15).
        if response.status_code == 429:
            if attempt <= max_retries:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise RateLimitError(f"SP-API rate limit exceeded for {path} after {max_retries} retries.")

        if response.status_code >= 500:
            if attempt <= max_retries:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise MarketplaceUnavailableError(
                f"SP-API returned {response.status_code} for {path} after {max_retries} retries."
            )

        if response.status_code == 401:
            # Access token was rejected outright (not just expired --
            # get_access_token already handles normal expiry). Most
            # likely the refresh_token itself was revoked by the
            # seller in Seller Central.
            raise AuthenticationError(
                f"SP-API rejected the access token for {path} (401) -- the seller may have "
                "revoked SellerOS's authorization; they need to reconnect Amazon."
            )

        if response.status_code >= 400:
            raise ConnectorError(
                f"SP-API request failed ({response.status_code}) for {path}: {response.text[:500]}"
            )

        if not response.content:
            return {}
        return response.json()


def paginate(
    session: Any,
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    request_token_param: str = "nextToken",
) -> Iterator[Dict[str, Any]]:
    """
    Yields one parsed response page per SP-API call, following a
    pagination token until it's absent.

    `request_token_param` is the *request* query-param name the token
    is sent back under on the next call -- most SP-API list operations
    use `nextToken` (the default), but Orders API v2026-01-01's
    searchOrders uses `paginationToken` instead (same concept, renamed
    -- see the Orders API Migration Guide's "Query parameter mappings"
    table: NextToken -> paginationToken, and note that token now
    expires after 24 hours). The *response* is still read from
    `pagination.nextToken` / a bare `nextToken` key -- that part of the
    convention is unchanged across SP-API list operations.
    """
    params = dict(params or {})
    while True:
        page = call(session, method, path, params=params)
        yield page

        next_token = (
            page.get("pagination", {}).get("nextToken")
            if isinstance(page.get("pagination"), dict)
            else None
        ) or page.get("nextToken")
        if not next_token:
            return
        params[request_token_param] = next_token

"""
flipkart_api_connector.py — Flipkart Seller API (REST), currently a
scaffold waiting on API approval.

Status: NOT LIVE YET. This file exists so that once Flipkart approves
API access, filling in the marked TODOs is the ONLY change needed —
flipkart_connector.py (the facade) already knows to route here
automatically the moment FLIPKART_CLIENT_ID / FLIPKART_CLIENT_SECRET /
FLIPKART_REFRESH_TOKEN are all present in backend/.env. Nothing above
the connector layer (tools, agents, marketplace_connector.py's
registries) needs to change either.

I don't have verified Flipkart Seller API endpoint paths/payload shapes
from here — Flipkart's API docs require an approved seller/partner
account to view in full, and I'm not going to guess at exact endpoint
URLs and pass them off as correct. The auth flow below follows
Flipkart's documented OAuth2 client-credentials pattern, but every
endpoint path is marked TODO — copy them from your approved API docs
when you get access rather than trusting the placeholders as-is.

Same public function contract as flipkart_playwright_connector.py:
fetch_products / fetch_orders / fetch_inventory / update_inventory /
verify_connection, all taking a MarketplaceSession and returning
list[dict] / dict — so normalizer.py and everything above the
connector layer is unaffected by which implementation is active.
"""
from __future__ import annotations

import os
import time
from typing import Any, Optional

import requests

from backend.ai.connectors_layer.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    RateLimitError,
    MarketplaceUnavailableError,
)

# TODO: confirm this against your approved Flipkart API docs — this is
# Flipkart's documented OAuth token endpoint as of general public docs,
# but re-verify once you have sandbox access.
TOKEN_URL = "https://api.flipkart.net/oauth-service/oauth/token"

# TODO: fill in real Seller API base + paths once approved. Placeholders
# below follow Flipkart's general REST conventions but are NOT verified.
API_BASE = "https://api.flipkart.net/sellers"
PATHS = {
    "products": f"{API_BASE}/listings/v3/search",
    "orders": f"{API_BASE}/orders/v2/shipments/filter",
    "inventory": f"{API_BASE}/listings/v3/skus",
}


class FlipkartAuth:
    """
    Client-credentials OAuth2, refreshed and cached in-memory for the
    life of the process. Credentials come from environment variables
    (backend/.env) — never hardcode them here.
    """

    def __init__(self) -> None:
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0

    def get_access_token(self) -> str:
        if self._access_token and time.time() < self._expires_at - 30:
            return self._access_token

        client_id = os.getenv("FLIPKART_CLIENT_ID")
        client_secret = os.getenv("FLIPKART_CLIENT_SECRET")
        refresh_token = os.getenv("FLIPKART_REFRESH_TOKEN")

        if not (client_id and client_secret and refresh_token):
            raise InvalidCredentialsError(
                "FLIPKART_CLIENT_ID / FLIPKART_CLIENT_SECRET / "
                "FLIPKART_REFRESH_TOKEN must all be set in backend/.env "
                "before the API connector can authenticate."
            )

        try:
            response = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                timeout=15,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise AuthenticationError(f"Flipkart OAuth token request failed: {exc}") from exc
        except requests.RequestException as exc:
            raise MarketplaceUnavailableError(f"Could not reach Flipkart auth service: {exc}") from exc

        payload = response.json()
        self._access_token = payload["access_token"]
        self._expires_at = time.time() + payload.get("expires_in", 3600)
        return self._access_token


_auth = FlipkartAuth()


def _authed_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_auth.get_access_token()}",
        "Content-Type": "application/json",
    }


def _get(url: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    try:
        response = requests.get(url, headers=_authed_headers(), params=params, timeout=20)
    except requests.RequestException as exc:
        raise MarketplaceUnavailableError(f"Flipkart API request failed: {exc}") from exc

    if response.status_code == 429:
        raise RateLimitError("Flipkart API rate limit exceeded.")
    if response.status_code in (401, 403):
        raise InvalidCredentialsError(f"Flipkart API rejected the request: {response.text}")
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Public fetch functions — same signature shape as
# flipkart_playwright_connector.py, on purpose.
# ---------------------------------------------------------------------------

def fetch_products(session, page: int = 1, limit: int = 50, category: Optional[str] = None) -> list[dict[str, Any]]:
    # TODO: replace param names/response parsing with the real Seller
    # API contract once you have docs access.
    params = {"pageNumber": page, "pageSize": limit}
    if category:
        params["category"] = category
    data = _get(PATHS["products"], params=params)
    return data.get("listings", data.get("items", []))


def fetch_orders(
    session,
    status: Optional[str] = None,
    start_date=None,
    end_date=None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    # TODO: replace with the real orders/shipments filter contract.
    params: dict[str, Any] = {"pageNumber": page, "pageSize": limit}
    if status:
        params["status"] = status
    if start_date:
        params["fromDate"] = start_date.date().isoformat()
    if end_date:
        params["toDate"] = end_date.date().isoformat()
    data = _get(PATHS["orders"], params=params)
    return data.get("shipments", data.get("orders", []))


def fetch_shipments(
    session,
    order_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    # Deliberately hitting the SAME endpoint as fetch_orders above, not
    # a separate "shipments" path — Flipkart's Seller API models orders
    # at shipment granularity (one order can split into multiple
    # shipments), which is exactly why PATHS["orders"] is already
    # "orders/v2/shipments/filter" rather than an "/orders" path. Once
    # you have real docs access, confirm whether tracking-specific
    # fields (carrier, tracking_number) come back on this same payload
    # or need a second call — TODO either way, same as fetch_orders.
    params: dict[str, Any] = {"pageNumber": page, "pageSize": limit}
    if order_id:
        params["orderId"] = order_id
    if status:
        params["status"] = status
    data = _get(PATHS["orders"], params=params)
    return data.get("shipments", data.get("orders", []))


def fetch_inventory(session, sku: Optional[str] = None, page: int = 1, limit: int = 50) -> list[dict[str, Any]]:
    # TODO: replace with the real listings/skus contract.
    params: dict[str, Any] = {"pageNumber": page, "pageSize": limit}
    if sku:
        params["sku"] = sku
    data = _get(PATHS["inventory"], params=params)
    return data.get("skus", data.get("items", []))


def update_inventory(session, sku: str, quantity: int) -> dict[str, Any]:
    # TODO: replace with the real inventory-update endpoint + payload shape.
    url = f"{PATHS['inventory']}/{sku}"
    try:
        response = requests.put(
            url,
            headers=_authed_headers(),
            json={"quantity": quantity},
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MarketplaceUnavailableError(f"Flipkart inventory update failed: {exc}") from exc

    return {
        "sku": sku,
        "updated_quantity": quantity,
        "status": "success",
        "message": "Inventory updated via Flipkart Seller API.",
    }


def verify_connection(session) -> dict[str, Any]:
    try:
        _auth.get_access_token()
        return {
            "platform": "flipkart",
            "seller_id": session.seller_id,
            "is_connected": True,
            "message": "Authenticated with Flipkart Seller API successfully.",
        }
    except (AuthenticationError, InvalidCredentialsError, MarketplaceUnavailableError) as exc:
        return {
            "platform": "flipkart",
            "seller_id": session.seller_id,
            "is_connected": False,
            "message": str(exc),
        }


# Not part of this scaffold's original contract (see module docstring) --
# flipkart_playwright_connector.py added these three later, and
# flipkart_connector.py's facade calls whichever implementation is
# active without checking first. Left unimplemented here (no verified
# Flipkart Seller API endpoint for them -- same reason every endpoint
# above is a TODO), but defined so a real Flipkart-API-credentialed
# deployment gets a clear, diagnosable NotImplementedError instead of
# an AttributeError buried in the facade.
def fetch_sales_metrics(session, start_date=None, end_date=None, timeframe: str = "30d") -> dict[str, Any]:
    raise NotImplementedError(
        "flipkart_api_connector.fetch_sales_metrics: no verified Flipkart Seller API "
        "endpoint for sales metrics yet -- TODO once API docs are available."
    )


def fetch_business_metrics(session, start_date=None, end_date=None, timeframe: str = "30d") -> dict[str, Any]:
    raise NotImplementedError(
        "flipkart_api_connector.fetch_business_metrics: no verified Flipkart Seller API "
        "endpoint for business metrics yet -- TODO once API docs are available."
    )


def fetch_inventory_metrics(session) -> dict[str, Any]:
    raise NotImplementedError(
        "flipkart_api_connector.fetch_inventory_metrics: no verified Flipkart Seller API "
        "endpoint for inventory metrics yet -- TODO once API docs are available."
    )

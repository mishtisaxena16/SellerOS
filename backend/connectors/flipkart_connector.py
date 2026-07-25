"""
flipkart_connector.py — the switchboard between the two Flipkart
implementations. This is the ONLY file marketplace_connector.py ever
imports for Flipkart; it never sees flipkart_api_connector.py or
flipkart_playwright_connector.py directly.

Why a facade instead of picking one at registry-build time: Flipkart's
API approval is pending. Right now every function here routes to
flipkart_playwright_connector (Live Mode via Seller Hub automation).
The moment FLIPKART_CLIENT_ID, FLIPKART_CLIENT_SECRET, and
FLIPKART_REFRESH_TOKEN are all set in backend/.env, every function
below routes to flipkart_api_connector instead — automatically, on the
next call, with zero code changes anywhere: not here, not in
marketplace_connector.py's registries, not in any tool or agent.

The check is re-evaluated on every call rather than cached at import
time, so flipping credentials into .env and restarting the process is
all it takes — no need to also touch this file that day.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from connectors import flipkart_api_connector as _api
from connectors import flipkart_playwright_connector as _playwright


def _api_credentials_present() -> bool:
    return bool(
        os.getenv("FLIPKART_CLIENT_ID")
        and os.getenv("FLIPKART_CLIENT_SECRET")
        and os.getenv("FLIPKART_REFRESH_TOKEN")
    )


def _active_impl():
    """
    Single choke point for the switch. Everything below calls this
    instead of hardcoding _api or _playwright, so there's exactly one
    place that ever needs to change if the switch condition itself
    changes (e.g. adding an explicit FLIPKART_API_APPROVED flag later).
    """
    return _api if _api_credentials_present() else _playwright


def active_mode() -> str:
    """Exposed for logging/diagnostics — 'api' or 'playwright'."""
    return "api" if _api_credentials_present() else "playwright"


# ---------------------------------------------------------------------------
# Public fetch functions — identical signatures to both backing modules,
# and to the old Mock Mode connector this replaces.
# ---------------------------------------------------------------------------

def fetch_products(session, page: int = 1, limit: int = 50, category: Optional[str] = None) -> list[dict[str, Any]]:
    return _active_impl().fetch_products(session, page=page, limit=limit, category=category)


def fetch_orders(
    session,
    status: Optional[str] = None,
    start_date=None,
    end_date=None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return _active_impl().fetch_orders(
        session, status=status, start_date=start_date, end_date=end_date, page=page, limit=limit
    )


def fetch_shipments(
    session,
    order_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    return _active_impl().fetch_shipments(session, order_id=order_id, status=status, page=page, limit=limit)


def fetch_inventory(session, sku: Optional[str] = None, page: int = 1, limit: int = 50) -> list[dict[str, Any]]:
    return _active_impl().fetch_inventory(session, sku=sku, page=page, limit=limit)


def update_inventory(session, sku: str, quantity: int) -> dict[str, Any]:
    return _active_impl().update_inventory(session, sku, quantity)


def verify_connection(session) -> dict[str, Any]:
    result = _active_impl().verify_connection(session)
    # Tag which mode actually served this call — cheap to add, useful
    # the day you're checking whether the switch-over actually happened.
    result.setdefault("mode", active_mode())
    return result

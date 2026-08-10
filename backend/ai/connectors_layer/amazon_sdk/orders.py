"""
orders.py — Orders API v2026-01-01 endpoint wrappers.

Verified against the official Amazon SP-API documentation for this
phase (developer-docs.amazon.com/sp-api):
  - "Orders API" overview + "Orders API Migration Guide"
  - "Orders API Rate Limits"

Why v2026-01-01 and not v0: the Orders API v0 is deprecated (sellers
must migrate to v2026-01-01 by 2027-03-27, per the migration guide).
v0's ten operations collapse into exactly two in v2026-01-01:

    v0 operation              -> v2026-01-01 operation
    ------------------------------------------------------------
    GetOrders                 -> searchOrders
    GetOrder                  -> getOrder
    GetOrderItems              -> getOrder (items always included)
    GetOrderBuyerInfo          -> getOrder with includedData=BUYER
    GetOrderAddress             -> getOrder with includedData=RECIPIENT
    GetOrderItemsBuyerInfo      -> getOrder with includedData=BUYER

This module only implements searchOrders + getOrder -- everything this
phase's normalized Order schema needs. No Restricted Data Token (RDT)
call is made anywhere in this module: v2026-01-01 replaced RDTs with
role-based PII access (see "Access Orders PII"), and this phase's
`DEFAULT_ORDERS_INCLUDED_DATA` (config.py) doesn't request BUYER/
RECIPIENT/PAYMENT/TAX data in the first place, so the question doesn't
even arise here.

Every function in this module takes `session` (a MarketplaceSession)
and delegates the actual HTTP call to amazon_sdk.client.call /
.paginate -- so token refresh, retry/backoff, and error translation
are all inherited for free, unchanged, per the task's "reuse the
existing HTTP client / retry layer / token manager" requirement.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterator, Optional, Sequence

from backend.ai.connectors_layer.amazon_sdk import client as amazon_client
from backend.ai.connectors_layer.amazon_sdk.config import (
    DEFAULT_ORDERS_INCLUDED_DATA,
    MARKETPLACE_IDS,
    ORDERS_API_VERSION,
)

ORDERS_BASE_PATH = f"/orders/{ORDERS_API_VERSION}/orders"

# searchOrders/getOrder's own request-side pagination token param name
# (renamed from v0's NextToken -- see client.paginate's docstring).
_PAGINATION_TOKEN_PARAM = "paginationToken"


def _resolve_marketplace_ids(session: Any) -> list[str]:
    """
    `session.marketplace_id` (a single id) takes priority if the seller
    connected with one; falls back to session.credentials['marketplace_id'],
    then to India (config.MARKETPLACE_IDS['IN']) -- the same India-first
    default config.py's DEFAULT_REGION already documents as matching
    SellerOS's actual seller base, so a seller who authorized Amazon but
    has no marketplace_id recorded yet still gets a sane default instead
    of an opaque 400 from SP-API for a missing required parameter.
    """
    explicit = getattr(session, "marketplace_id", None) or (session.credentials or {}).get("marketplace_id")
    if explicit:
        return [explicit]
    return [MARKETPLACE_IDS["IN"]]


def _iso8601(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        # SP-API requires ISO 8601; Z suffix (not +00:00) matches every
        # example in the official docs and in this SDK's own sample data.
        iso = value.isoformat()
        return iso.replace("+00:00", "Z") if iso.endswith("+00:00") else iso
    return str(value)


def _build_search_params(
    marketplace_ids: Sequence[str],
    created_after: Any = None,
    created_before: Any = None,
    last_updated_after: Any = None,
    last_updated_before: Any = None,
    fulfillment_statuses: Optional[Sequence[str]] = None,
    fulfilled_by: Optional[str] = None,
    max_results_per_page: int = 100,
    included_data: Optional[Sequence[str]] = None,
    pagination_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Builds the searchOrders query params, enforcing the one documented
    hard constraint the official docs call out explicitly: "You must
    provide exactly one of createdAfter and lastUpdatedAfter. If
    createdAfter is provided, neither lastUpdatedAfter nor
    lastUpdatedBefore may be provided" (and symmetrically for
    lastUpdatedAfter). Raising early with a clear message here is much
    more useful to a caller than the 400 InvalidInput SP-API would
    otherwise return.
    """
    if pagination_token:
        # Once a paginationToken is present it supersedes every filter
        # for that follow-up call (same as v0's NextToken behaviour --
        # "NextToken doesn't affect any filters ... it only impacts the
        # pagination for the filtered orders response", i.e. the
        # filters were already locked in on the first call).
        return {"marketplaceIds": marketplace_ids, "paginationToken": pagination_token}

    has_created_after = created_after is not None
    has_last_updated_after = last_updated_after is not None

    if has_created_after == has_last_updated_after:
        raise ValueError(
            "search_orders requires exactly one of created_after / last_updated_after "
            "(both given or both omitted) -- this is a hard SP-API Orders API constraint, "
            "not a SellerOS one."
        )
    if has_created_after and (last_updated_after is not None or last_updated_before is not None):
        raise ValueError("created_after cannot be combined with last_updated_after/last_updated_before.")
    if has_last_updated_after and (created_after is not None or created_before is not None):
        raise ValueError("last_updated_after cannot be combined with created_after/created_before.")

    params: Dict[str, Any] = {
        "marketplaceIds": marketplace_ids,
        "maxResultsPerPage": max_results_per_page,
    }
    if created_after is not None:
        params["createdAfter"] = _iso8601(created_after)
    if created_before is not None:
        params["createdBefore"] = _iso8601(created_before)
    if last_updated_after is not None:
        params["lastUpdatedAfter"] = _iso8601(last_updated_after)
    if last_updated_before is not None:
        params["lastUpdatedBefore"] = _iso8601(last_updated_before)
    if fulfillment_statuses:
        params["fulfillmentStatuses"] = list(fulfillment_statuses)
    if fulfilled_by:
        params["fulfilledBy"] = fulfilled_by

    included = list(included_data) if included_data is not None else list(DEFAULT_ORDERS_INCLUDED_DATA)
    if included:
        params["includedData"] = included

    return params


def search_orders(
    session: Any,
    marketplace_ids: Optional[Sequence[str]] = None,
    created_after: Any = None,
    created_before: Any = None,
    last_updated_after: Any = None,
    last_updated_before: Any = None,
    fulfillment_statuses: Optional[Sequence[str]] = None,
    fulfilled_by: Optional[str] = None,
    max_results_per_page: int = 100,
    included_data: Optional[Sequence[str]] = None,
    pagination_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    One page of GET /orders/2026-01-01/orders (searchOrders).
    Returns the raw parsed JSON body -- callers that want every order
    across every page should use `iterate_orders` instead.
    """
    params = _build_search_params(
        marketplace_ids or _resolve_marketplace_ids(session),
        created_after=created_after,
        created_before=created_before,
        last_updated_after=last_updated_after,
        last_updated_before=last_updated_before,
        fulfillment_statuses=fulfillment_statuses,
        fulfilled_by=fulfilled_by,
        max_results_per_page=max_results_per_page,
        included_data=included_data,
        pagination_token=pagination_token,
    )
    return amazon_client.call(session, "GET", ORDERS_BASE_PATH, params=params)


def iterate_orders(
    session: Any,
    marketplace_ids: Optional[Sequence[str]] = None,
    created_after: Any = None,
    created_before: Any = None,
    last_updated_after: Any = None,
    last_updated_before: Any = None,
    fulfillment_statuses: Optional[Sequence[str]] = None,
    fulfilled_by: Optional[str] = None,
    max_results_per_page: int = 100,
    included_data: Optional[Sequence[str]] = None,
) -> Iterator[Dict[str, Any]]:
    """
    Yields individual raw order dicts, transparently following
    paginationToken across as many searchOrders calls as needed (via
    client.paginate, so retry/backoff on each page is inherited
    unchanged). Callers that only want N orders should stop iterating
    once they have N -- this generator does not itself cap page count.

    Note (search response shape, "Requires Live Validation"): the
    official docs confirm the *request* token param renamed
    NextToken -> paginationToken and now expires after 24 hours, but
    the publicly available docs for this phase did not show the exact
    *response* JSON key the next token comes back under. This reuses
    client.paginate's existing convention (pagination.nextToken, or a
    bare nextToken key -- the same one v0 and other SP-API list
    operations use) as the best-available assumption; confirming it
    against a live sandbox call is flagged as a live-validation item
    in this phase's final report.
    """
    params = _build_search_params(
        marketplace_ids or _resolve_marketplace_ids(session),
        created_after=created_after,
        created_before=created_before,
        last_updated_after=last_updated_after,
        last_updated_before=last_updated_before,
        fulfillment_statuses=fulfillment_statuses,
        fulfilled_by=fulfilled_by,
        max_results_per_page=max_results_per_page,
        included_data=included_data,
    )
    for page in amazon_client.paginate(
        session, "GET", ORDERS_BASE_PATH, params=params, request_token_param=_PAGINATION_TOKEN_PARAM
    ):
        orders = page.get("orders")
        if orders is None:
            # Defensive fallback in case a given account/region wraps
            # the list under "payload" like several other SP-API list
            # endpoints do -- avoids silently yielding nothing rather
            # than raising, since an empty order list is also a valid,
            # common response (new/quiet seller).
            payload = page.get("payload")
            orders = payload.get("orders", []) if isinstance(payload, dict) else []
        for order in orders:
            yield order


def get_order(
    session: Any,
    order_id: str,
    included_data: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    GET /orders/2026-01-01/orders/{orderId} (getOrder) -- a single
    order, with items always included (unlike v0, which needed a
    separate getOrderItems call).
    """
    included = list(included_data) if included_data is not None else list(DEFAULT_ORDERS_INCLUDED_DATA)
    params: Dict[str, Any] = {}
    if included:
        params["includedData"] = included
    return amazon_client.call(session, "GET", f"{ORDERS_BASE_PATH}/{order_id}", params=params)

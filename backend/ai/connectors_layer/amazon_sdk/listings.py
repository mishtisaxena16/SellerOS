"""
listings.py — Listings Items API v2021-08-01 endpoint wrappers.

Verified against the official Amazon SP-API documentation for this
phase (developer-docs.amazon.com/sp-api):
  - "Listings Items API" reference (getListingsItem, searchListingsItems,
    patchListingsItem)
  - "Manage Product Listings with the Selling Partner API" guide
  - "Multi-Location Inventory Integration Guide"

Why one module covers Product Details + Listings + Pricing + Inventory:
this phase's own task list splits those into four sections, but the
current (non-deprecated) SP-API doesn't -- a single getListingsItem/
searchListingsItems call with includedData=summaries,attributes,offers,
fulfillmentAvailability returns:
  - Product Details -> summaries[].asin/itemName/mainImage, attributes
  - Listings          -> the same summaries/attributes/status
  - Pricing           -> offers[].price (current selling price + currency)
  - Inventory         -> fulfillmentAvailability[].quantity (merchant-
                          fulfilled quantity at each supply source)
Splitting this into 3-4 separate API modules that each re-fetch
overlapping data would mean more calls against the same (fairly tight,
5 rps/burst 10) rate limit for no benefit, so this phase deliberately
implements the "Pricing" and "Product Details" task sections as a
byproduct of the same Listings call rather than a second API
(Product Pricing API v2022-05-01, Catalog Items API) -- see the
CHANGELOG for the explicit "why not" reasoning per section.

Every function takes `session` and delegates to amazon_sdk.client, same
as orders.py -- token refresh/retry/error-translation reused unchanged.
"""
from __future__ import annotations

from typing import Any, Dict, Iterator, Optional, Sequence

from backend.ai.connectors_layer.amazon_sdk import client as amazon_client
from backend.ai.connectors_layer.amazon_sdk.config import MARKETPLACE_IDS
from backend.ai.connectors_layer.exceptions import ConnectorError

LISTINGS_API_VERSION = "2021-08-01"
LISTINGS_BASE_PATH = f"/listings/{LISTINGS_API_VERSION}/items"

# getListingsItem/searchListingsItems includedData this phase requests.
# Deliberately excludes "issues" (listing-health diagnostics -- belongs
# to a future Seller Coach / listing-quality phase, not Orders/Inventory/
# Product-details parity) and "relationships" (variation parent/child --
# out of scope, no SellerOS model field for it yet).
DEFAULT_LISTINGS_INCLUDED_DATA: tuple[str, ...] = ("summaries", "attributes", "offers", "fulfillmentAvailability")

# Multi-Location Inventory's default single-location supply source code
# -- see the Multi-Location Inventory Integration Guide.
DEFAULT_FULFILLMENT_CHANNEL_CODE = "DEFAULT"


def _seller_id(session: Any) -> str:
    """
    Listings Items API paths are keyed by Amazon's own Selling Partner
    ID (the `sellerId` path segment), which is NOT the same value as
    SellerOS's internal `session.seller_id` (an internal integer id).
    The real value is `selling_partner_id`, captured from Amazon's own
    OAuth callback query param and stored in session.credentials by
    AmazonAuthService.handle_callback (see service/amazon_auth_service.py)
    -- reused here rather than re-deriving it a second way.
    """
    selling_partner_id = (session.credentials or {}).get("selling_partner_id")
    if not selling_partner_id:
        raise ConnectorError(
            "Amazon session has no selling_partner_id in credentials -- this is captured from "
            "Amazon's OAuth callback (see AmazonAuthService.handle_callback) and is required for "
            "every Listings Items API call. Re-authorize the seller via Login with Amazon."
        )
    return selling_partner_id


def _resolve_marketplace_ids(session: Any) -> list[str]:
    explicit = getattr(session, "marketplace_id", None) or (session.credentials or {}).get("marketplace_id")
    if explicit:
        return [explicit]
    return [MARKETPLACE_IDS["IN"]]  # India-first default, same as orders.py


def get_listings_item(
    session: Any,
    sku: str,
    marketplace_ids: Optional[Sequence[str]] = None,
    included_data: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """GET /listings/2021-08-01/items/{sellerId}/{sku} (getListingsItem)."""
    params: Dict[str, Any] = {
        "marketplaceIds": list(marketplace_ids) if marketplace_ids else _resolve_marketplace_ids(session),
        "includedData": list(included_data) if included_data is not None else list(DEFAULT_LISTINGS_INCLUDED_DATA),
    }
    return amazon_client.call(session, "GET", f"{LISTINGS_BASE_PATH}/{_seller_id(session)}/{sku}", params=params)


def search_listings_items(
    session: Any,
    marketplace_ids: Optional[Sequence[str]] = None,
    identifiers: Optional[Sequence[str]] = None,
    identifiers_type: Optional[str] = None,
    included_data: Optional[Sequence[str]] = None,
    page_size: int = 20,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    GET /listings/2021-08-01/items (searchListingsItems) -- one page.

    Note (query param gotcha, confirmed against multiple independent
    sources incl. Amazon's own seller forums, since the reference page
    itself doesn't spell this out clearly): the response's pagination
    object key is `nextToken`, but the *request* query param to send it
    back as is **`pageToken`**, not `nextToken` -- unlike Orders API,
    where the request param and a same-named response field both exist.
    Getting this wrong silently loops on page 1 forever rather than
    erroring, which is exactly the kind of thing worth flagging loudly:
    handled correctly below via `request_token_param="pageToken"`.
    """
    params: Dict[str, Any] = {
        "marketplaceIds": list(marketplace_ids) if marketplace_ids else _resolve_marketplace_ids(session),
        "sellerId": _seller_id(session),
        "pageSize": page_size,
        "includedData": list(included_data) if included_data is not None else list(DEFAULT_LISTINGS_INCLUDED_DATA),
    }
    if identifiers:
        params["identifiers"] = list(identifiers)
        params["identifiersType"] = identifiers_type or "SKU"
    if page_token:
        params["pageToken"] = page_token
    return amazon_client.call(session, "GET", LISTINGS_BASE_PATH, params=params)


def iterate_listings_items(
    session: Any,
    marketplace_ids: Optional[Sequence[str]] = None,
    included_data: Optional[Sequence[str]] = None,
    page_size: int = 20,
) -> Iterator[Dict[str, Any]]:
    """Yields individual raw listings items, following pageToken across pages."""
    params: Dict[str, Any] = {
        "marketplaceIds": list(marketplace_ids) if marketplace_ids else _resolve_marketplace_ids(session),
        "sellerId": _seller_id(session),
        "pageSize": page_size,
        "includedData": list(included_data) if included_data is not None else list(DEFAULT_LISTINGS_INCLUDED_DATA),
    }
    for page in amazon_client.paginate(
        session, "GET", LISTINGS_BASE_PATH, params=params, request_token_param="pageToken"
    ):
        for item in page.get("items") or []:
            yield item


def patch_listings_item_quantity(
    session: Any,
    sku: str,
    quantity: int,
    fulfillment_channel_code: str = DEFAULT_FULFILLMENT_CHANNEL_CODE,
) -> Dict[str, Any]:
    """
    PATCH /listings/2021-08-01/items/{sellerId}/{sku} (patchListingsItem)
    -- inventory-only quantity update via the JSON Patch merge operation
    (see the Multi-Location Inventory guide's worked example + the
    "JSON patch merge operation" changelog entry). `productType:
    "PRODUCT"` is a valid hardcoded value for inventory-only patches
    regardless of the listing's real product type (confirmed in the
    official "New Listings Items API submission when updating inventory
    only" guidance) -- avoids an extra getListingsItem/
    getDefinitionsProductType round-trip just to discover the real
    product type before every quantity update.

    Note the attribute-name casing asymmetry vs. GET responses: this
    patch body uses snake_case (`fulfillment_availability`,
    `fulfillment_channel_code`) — the Product Type Definitions attribute
    schema's naming — while getListingsItem's response uses camelCase
    (`fulfillmentAvailability`, `fulfillmentChannelCode`). Both are
    correct for their respective directions; easy to typo one for the
    other, so documented explicitly here.
    """
    body = {
        "productType": "PRODUCT",
        "patches": [
            {
                "op": "replace",
                "path": "/attributes/fulfillment_availability",
                "value": [{"fulfillment_channel_code": fulfillment_channel_code, "quantity": quantity}],
            }
        ],
    }
    params = {"marketplaceIds": _resolve_marketplace_ids(session)}
    return amazon_client.call(
        session, "PATCH", f"{LISTINGS_BASE_PATH}/{_seller_id(session)}/{sku}", params=params, json_body=body
    )

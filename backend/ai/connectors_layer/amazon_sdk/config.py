"""
config.py — SP-API region endpoints and Seller Central URLs.

Verified against official docs (developer-docs.amazon.com/sp-api,
"SP-API Endpoints" + "Website authorization workflow", checked for
this phase): SP-API is region-scoped (not per-marketplace), and each
region has one API base URL and one Seller Central sign-in base URL
used to build the OAuth consent link.
"""
from __future__ import annotations

# The LWA token endpoint is the same for every region -- only the
# SP-API and Seller Central URLs vary by region.
LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"

# SP-API base URL per region.
REGION_ENDPOINTS: dict[str, str] = {
    "na": "https://sellingpartnerapi-na.amazon.com",
    "eu": "https://sellingpartnerapi-eu.amazon.com",
    "fe": "https://sellingpartnerapi-fe.amazon.com",
}

# Seller Central sign-in base URL per region -- used to build the
# "/apps/authorize/consent" OAuth authorization URI (Website
# Authorization Workflow). India (RelXtra's actual marketplace) is
# under the EU region's Seller Central for this purpose.
SELLER_CENTRAL_BASE: dict[str, str] = {
    "na": "https://sellercentral.amazon.com",
    "eu": "https://sellercentral.amazon.in",
    "fe": "https://sellercentral.amazon.co.jp",
}

# Common marketplace IDs a seller might connect (not exhaustive --
# extend as later phases need more). Amazon.in is included since
# that's the marketplace SellerOS's existing sellers actually use.
MARKETPLACE_IDS: dict[str, str] = {
    "IN": "A21TJRUUN4KGV",
    "US": "ATVPDKIKX0DER",
    "UK": "A1F83G8C2ARO7P",
    "DE": "A1PA6795UKMFR9",
    "JP": "A1VC38T7YXB528",
}

DEFAULT_REGION = "eu"  # India-first default, matches SellerOS's actual seller base

# ---------------------------------------------------------------------------
# Orders API
#
# Verified against the official "Orders API Migration Guide"
# (developer-docs.amazon.com/sp-api/docs/orders-api-migration-guide),
# checked for this phase: the Orders API v0 is deprecated (sellers must
# migrate to v2026-01-01 by 2027-03-27) and is replaced by exactly two
# operations -- searchOrders (list/filter) and getOrder (single order,
# items always included). This phase implements against v2026-01-01
# directly rather than the deprecated v0, per the task's instruction to
# follow current official documentation over older tutorials/repos.
# ---------------------------------------------------------------------------

ORDERS_API_VERSION = "2026-01-01"

# fulfillment.fulfillmentStatus values (v2026-01-01) -- upper snake case,
# renamed/reshaped from v0's OrderStatus. "Canceled" also picked up a
# spelling change (-> "CANCELLED", double L) in the new version.
ORDER_STATUS_VALUES: tuple[str, ...] = (
    "PENDING",
    "PENDING_AVAILABILITY",
    "UNSHIPPED",
    "PARTIALLY_SHIPPED",
    "SHIPPED",
    "CANCELLED",
    "UNFULFILLABLE",
    "INVOICE_UNCONFIRMED",
)

# fulfillment.fulfilledBy values (v2026-01-01) -- replaces v0's
# FulfillmentChannel MFN/AFN pair.
FULFILLMENT_CHANNEL_VALUES: dict[str, str] = {
    "MERCHANT": "Merchant Fulfilled Network (FBM)",
    "AMAZON": "Amazon Fulfilled Network (FBA)",
}

# includedData values this phase actually requests. Deliberately
# excludes BUYER/RECIPIENT/PAYMENT/TAX (buyer PII and payment detail) --
# SellerOS's normalized Order schema for this phase (order id, dates,
# status, fulfillment channel, currency, total, marketplace, item count,
# shipping service level) needs none of it, and the docs themselves note
# "the less data you request, the better the performance will be."
# PACKAGES/PROMOTION/EXPENSE/CANCELLATION are similarly left out as
# out-of-scope for this phase (shipment-tracking detail belongs to
# fetch_shipments, not fetch_orders).
DEFAULT_ORDERS_INCLUDED_DATA: tuple[str, ...] = ("FULFILLMENT", "PROCEEDS")

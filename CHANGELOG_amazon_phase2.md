# SellerOS – Amazon Integration Phase 2 (Orders API) — Changelog

## Documentation verification

Verified against the official Amazon SP-API docs (developer-docs.amazon.com/sp-api)
before writing any code:

- **API version**: Orders API v0 is deprecated. Amazon requires migration to
  **Orders API v2026-01-01** by 2027-03-27 (Orders API Migration Guide,
  SP-API Release Notes). v0's ten operations collapse into two:
  `searchOrders` (list/filter) and `getOrder` (single order, items always
  included — no separate `getOrderItems` call needed).
- **Decision**: since this is new (not existing) Orders code, implemented
  directly against v2026-01-01 rather than the deprecated v0, per the
  task's instruction to follow current official docs over older
  tutorials/repos. This is a deliberate deviation from what a literal
  reading of "Orders API v0-shaped" sample data in the checkpoint might
  have suggested, and is explained via updated sample data + normalizer
  field maps below.
- **Pagination**: request-side token param renamed `NextToken` →
  `paginationToken`, and the token now expires after 24 hours (was
  unspecified/longer in v0).
- **Status values**: `fulfillment.fulfillmentStatus`, upper-snake-case
  (`UNSHIPPED`, `PARTIALLY_SHIPPED`, `SHIPPED`, `CANCELLED` — note spelling
  change, `PENDING`, `UNFULFILLABLE`, `PENDING_AVAILABILITY`,
  `INVOICE_UNCONFIRMED`).
- **Fulfillment channel**: `fulfillment.fulfilledBy` — `MERCHANT` (was MFN)
  / `AMAZON` (was AFN).
- **Required params**: `searchOrders` requires *exactly one* of
  `createdAfter` / `lastUpdatedAfter` (enforced in `orders.py` before any
  HTTP call is made, not left to a 400 from SP-API).
- **PII**: v2026-01-01 replaced Restricted Data Tokens with role-based
  access. This phase's default `includedData` (`FULFILLMENT`, `PROCEEDS`)
  requests no buyer PII at all, so no RDT/role question even arises for
  the Orders sync this phase implements.
- **Marketplace IDs / regions**: unchanged from Phase 1 (`amazon_sdk/config.py`
  `MARKETPLACE_IDS` / `REGION_ENDPOINTS`), reused as-is.
- **Rate limits**: `getOrder` — 0.5 req/s, burst 30 (per-operation usage
  plan). Reused the existing retry/backoff layer (`client.call`) unchanged;
  no new rate-limit logic was written.

## Fixed / Implemented

- **New**: `backend/ai/connectors_layer/amazon_sdk/orders.py` —
  `search_orders`, `iterate_orders`, `get_order` wrappers around
  `searchOrders`/`getOrder`, built entirely on the existing shared
  `client.call` / `auth.get_access_token` / retry layer (no duplicated
  HTTP/auth/retry logic).
- **Changed**: `amazon_sdk/client.paginate` — added an optional
  `request_token_param` (default `"nextToken"`, unchanged for any other
  caller) so Orders' renamed `paginationToken` request param can reuse the
  same pagination helper instead of a duplicate.
- **Changed**: `amazon_sdk/config.py` — added `ORDERS_API_VERSION`,
  verified `ORDER_STATUS_VALUES`, `FULFILLMENT_CHANNEL_VALUES`, and
  `DEFAULT_ORDERS_INCLUDED_DATA` (documented reasoning for excluding
  PII-bearing `includedData` values by default).
- **Changed**: `amazon_connector.py` — `fetch_orders` now dispatches to
  Live Mode (real SP-API via `orders.iterate_orders`) when a refresh token
  is present on the session, falling back to the existing Mock Mode
  sample-data path otherwise (unchanged behavior when no OAuth is
  connected). New `fetch_order(session, order_id)` (Live + Mock Mode).
  `fetch_sales_metrics` / `fetch_business_metrics` updated to read the new
  order shape (still Mock-Mode-only, unaffected by Live Mode Orders work).
- **Changed**: `marketplace_connector.py` — wired
  `SINGLE_ORDER_FETCHERS["amazon"] = amazon_connector.fetch_order`
  (previously empty for every platform — `get_order()` existed but had no
  registry entry, so it raised `NotImplementedError` for all platforms).
  No public function signatures changed.
- **Changed**: `normalizer.py` — `ORDER_FIELD_MAPS["amazon"]` updated to
  v2026-01-01's nested field paths; new `_extract_amazon_order_items`
  helper for the `orderItems[].product.*` shape (meesho/flipkart's flat
  item extraction is untouched, still uses the old code path).
- **Changed**: `models.py` — `Order` gained optional
  `last_updated_date`, `fulfillment_channel`, `marketplace`, `item_count`,
  `shipping_service_level`; `OrderItem` gained optional `order_item_id`,
  `asin`, `title`. All additive/optional — meesho/flipkart normalization
  (which don't populate them) are unaffected.
- **Changed**: `sample_data/amazon/orders.json` — updated to the
  v2026-01-01 response shape so Mock Mode and Live Mode normalize
  through the identical code path (no separate "mock schema" to maintain).
- **New**: `backend/tests/test_amazon_orders.py` — unit tests for
  parameter building (incl. the createdAfter/lastUpdatedAfter mutual-
  exclusivity rule), pagination-token following, Mock Mode vs Live Mode
  `fetch_orders`/`fetch_order`, error propagation, `normalize_order`
  (dates, items, missing-PROCEEDS edge case), and end-to-end dispatch
  through `marketplace_connector.get_orders`/`get_order`.

## Remaining Amazon integration phases

Explicitly out of scope for this phase (per task instructions) and not
touched: Inventory (write path — read path already existed pre-Phase-2),
Listings, Pricing, Reports, Finance, Notifications, Feeds.

## Requires Live Validation

Everything below needs a live SP-API sandbox/production call to confirm —
flagged rather than guessed:

1. **`searchOrders` pagination response shape**: the docs confirm the
   *request* token param renamed to `paginationToken` (24h expiry), but
   the publicly available docs pulled for this phase didn't show the
   exact *response* JSON key the next token comes back under.
   `iterate_orders` reuses the existing `pagination.nextToken` / bare
   `nextToken` convention (same one `client.paginate` already used for
   other list endpoints) as the best-available assumption, plus a
   defensive `payload.orders` fallback for the order-list key itself.
   **Needs confirmation against a live/sandbox `searchOrders` response.**
2. **`orders` vs `payload.orders` response key**: same reasoning as above —
   assumed `orders` at the top level per the migration guide's examples;
   defensive fallback included but unconfirmed live.
3. **Full test suite execution**: this sandbox has no network access and
   none of `backend/requirements.txt` (pydantic, fastapi, sqlalchemy,
   pytest, ...) could be installed here. Every test in
   `test_amazon_orders.py` was hand-traced against the implementation and
   additionally re-verified with a manual script (real project code,
   minimal local pydantic/pydantic_settings stubs providing just enough
   to import and execute — not part of the deliverable) confirming
   `normalize_order`, Mock Mode `fetch_orders`/`fetch_order`, and
   `marketplace_connector.get_orders`/`get_order` (both Mock and
   SDK-mocked Live Mode) all produce the expected results against the
   real code. **`pytest backend/tests/test_amazon_orders.py` (and the
   full suite, to confirm zero regressions) still needs to be run in an
   environment with the real dependencies installed** before this is
   considered fully verified.

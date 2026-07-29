# backend/scripts/

Standalone, developer-run scripts. Nothing under this directory is
imported by `backend/main.py`, any API router, or any other
production code path -- these are invoked directly from the command
line by a developer, on purpose, so they stay easy to delete without
touching production code.

## dev_bootstrap_amazon.py

**Development-only.** Seeds one seller's Amazon marketplace
connection for local dev/testing, without going through the
browser-based "Connect Amazon" OAuth flow.

- Amazon OAuth (`AmazonAuthService`, the
  `/marketplaces/amazon/authorize` and `/marketplaces/amazon/callback`
  routes) remains the only production connection flow and is
  unmodified by this script.
- This script calls the existing, unmodified
  `MarketplaceService.connect_marketplace(...)` -- the exact same
  method the real OAuth callback calls. Same upsert, same
  encryption-at-rest, same `session_store` registration. There is no
  duplicated persistence logic and no direct database or
  `session_store` access.

### Usage

Set the following in `SellerOS/.env` (or your shell environment):

```
AMAZON_DEV_SELLER_ID=1
AMAZON_REFRESH_TOKEN=Atzr|Iw...
AMAZON_DEV_REGION=eu
```

Then, from the `SellerOS/` repo root:

```
python backend/scripts/dev_bootstrap_amazon.py
```

### Removing this bootstrap later

Delete this directory (`backend/scripts/`). Nothing else references
it -- no import, no router registration, no config elsewhere depends
on its presence.

"""
dev_bootstrap_amazon.py — DEVELOPMENT-ONLY Amazon connection bootstrap.

WHAT THIS IS
------------
A standalone command-line script, run manually by a developer, that
seeds one seller's Amazon marketplace connection without going
through the browser-based "Connect Amazon" OAuth flow. It exists
purely so local/dev work (chat, dashboard, orders, etc. for Amazon)
can proceed without a developer having to click through Amazon's own
login+consent screens every time a fresh local DB is created.

THIS IS NOT A REPLACEMENT FOR OAUTH
------------------------------------
- Amazon OAuth (backend/service/amazon_auth_service.py + the
  /marketplaces/amazon/authorize and /marketplaces/amazon/callback
  routes) remains the one and only production connection flow.
- This script is not registered anywhere in backend/main.py, does not
  add an API route, and is not imported by any production code path.
  It is invoked directly by a developer:

      python backend/scripts/dev_bootstrap_amazon.py

  (run from the SellerOS/ repo root, or anywhere -- see the sys.path
  bootstrap below).

WHY THIS IS SAFE / ISOLATED
----------------------------
- It calls the *existing*, unmodified
  MarketplaceService.connect_marketplace(...) -- the exact same
  method AmazonAuthService.handle_callback(...) calls after a real
  OAuth exchange. There is no separate/duplicated persistence logic:
  same upsert, same encryption-at-rest, same session_store
  registration. Dev and production write through the identical path.
- It never touches the database directly (no raw SQL, no direct
  MarketplaceAccount(...) construction/commit).
- It never touches backend/ai/connectors_layer/session_store.py
  directly -- session_store.register(...) is only ever called from
  inside MarketplaceService.connect_marketplace(...) itself.
- It does not modify AmazonAuthService, the OAuth routes, any
  connector, or any frontend code.
- Deleting this one file removes the entire bootstrap with no other
  code changes required anywhere else in the app.

CONFIGURATION
-------------
Reads everything it needs from environment variables / the backend's
existing `.env` (loaded the same way backend/config/settings.py loads
it), so no secrets are hardcoded here:

    AMAZON_DEV_SELLER_ID          required -- integer seller_id to
                                  attach the connection to (must be an
                                  existing seller/user id).
    AMAZON_REFRESH_TOKEN          required -- the SP-API refresh
                                  token to store. (Same variable
                                  already documented in .env.example
                                  as a single-seller dev/test value.)
    AMAZON_DEV_REGION             optional -- defaults to "eu", same
                                  default AmazonAuthService uses.
    AMAZON_DEV_SELLING_PARTNER_ID optional -- selling_partner_id, if
                                  you have one, mirroring what the
                                  real callback stores when Amazon
                                  supplies it.

USAGE
-----
    # in SellerOS/.env (or exported in your shell):
    AMAZON_DEV_SELLER_ID=1
    AMAZON_REFRESH_TOKEN=Atzr|Iw...
    AMAZON_DEV_REGION=eu

    python backend/scripts/dev_bootstrap_amazon.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Mirrors conftest.py's own bootstrap: backend/ has no __init__.py, so
# `from backend...` absolute imports only resolve once SellerOS/ (this
# file's grandparent directory) is on sys.path. Done here explicitly
# so this script also works when run directly (not just via `-m` from
# the repo root).
_SELLEROS_ROOT = Path(__file__).resolve().parents[2]
if str(_SELLEROS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SELLEROS_ROOT))

from dotenv import load_dotenv  # noqa: E402

# Load the same .env file backend/config/settings.py reads, so this
# script picks up whatever a developer already has configured locally
# without requiring a second, separate config file.
load_dotenv(_SELLEROS_ROOT / ".env")

from backend.database.session import SessionLocal  # noqa: E402
from backend.service.marketplace_service import MarketplaceService  # noqa: E402


class DevBootstrapConfigError(RuntimeError):
    """Raised when required dev bootstrap environment variables are missing."""


def _load_dev_config() -> dict:
    seller_id_raw = os.environ.get("AMAZON_DEV_SELLER_ID")
    refresh_token = os.environ.get("AMAZON_REFRESH_TOKEN")

    missing = []
    if not seller_id_raw:
        missing.append("AMAZON_DEV_SELLER_ID")
    if not refresh_token:
        missing.append("AMAZON_REFRESH_TOKEN")
    if missing:
        raise DevBootstrapConfigError(
            "Missing required dev bootstrap environment variable(s): "
            + ", ".join(missing)
            + ". Set these in SellerOS/.env or your shell environment "
            "before running this script. See the module docstring for "
            "details."
        )

    try:
        seller_id = int(seller_id_raw)
    except ValueError as exc:
        raise DevBootstrapConfigError(
            f"AMAZON_DEV_SELLER_ID must be an integer, got {seller_id_raw!r}."
        ) from exc

    region = os.environ.get("AMAZON_DEV_REGION", "eu")
    selling_partner_id = os.environ.get("AMAZON_DEV_SELLING_PARTNER_ID") or None

    return {
        "seller_id": seller_id,
        "refresh_token": refresh_token,
        "region": region,
        "selling_partner_id": selling_partner_id,
    }


def bootstrap_amazon_connection() -> None:
    """
    Seeds one seller's Amazon MarketplaceAccount for local development
    by calling the existing MarketplaceService.connect_marketplace(...)
    -- the same method the production OAuth callback uses.
    """
    config = _load_dev_config()

    # Same credentials shape AmazonAuthService.handle_callback(...)
    # builds after a real OAuth token exchange.
    credentials = {
        "refresh_token": config["refresh_token"],
        "region": config["region"],
    }
    if config["selling_partner_id"]:
        credentials["selling_partner_id"] = config["selling_partner_id"]

    db = SessionLocal()
    try:
        account = MarketplaceService.connect_marketplace(
            db=db,
            seller_id=config["seller_id"],
            platform="amazon",
            credentials=credentials,
        )
        print(
            "[dev_bootstrap_amazon] Amazon connected for "
            f"seller_id={account.seller_id} (region={config['region']}, "
            f"marketplace_account_id={account.id})."
        )
    finally:
        db.close()


if __name__ == "__main__":
    try:
        bootstrap_amazon_connection()
    except DevBootstrapConfigError as exc:
        print(f"[dev_bootstrap_amazon] {exc}", file=sys.stderr)
        sys.exit(1)

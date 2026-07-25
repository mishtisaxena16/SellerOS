"""
session_store.py — supplies a MarketplaceSession for a given
(seller_id, platform) pair, until the real backend (auth, DB, per-
seller OAuth/connect flows) exists to own this properly.

THE GAP THIS CLOSES
-----------------------------------------------------------------------
Every marketplace tool (inventory/listing/orders/ads/account) calls
`context.require_session()` (tools/base/tool_context.py) before doing
anything, which raises a clear ValueError if no MarketplaceSession is
attached. Before this file existed, nothing in orchestrator.py ever
built one — `_run_agent_node` called `agent.run(...)` with no
`session=` argument, so EVERY marketplace-touching agent (Inventory,
Listing, Orders, Pricing, Ads, ...) failed at the exact same point,
every time, regardless of query. Read-only/knowledge agents (Seller
Coach, Sustainability) never noticed, because they don't touch
marketplace tools at all — which is exactly why this was easy to miss
end-to-end and only shows up once you actually run an inventory/listing
query through the graph.

ARCHITECTURAL GUARANTEE THIS PRESERVES
-----------------------------------------------------------------------
guardrails.py's own module docstring states the rule plainly: real
credentials must live ONLY in a MarketplaceSession the Connector Layer
owns, and SellerOSState must only ever carry an opaque reference, never
the secret itself — because SellerOSState gets checkpointed
(MemorySaver/PostgresSaver) and can be surfaced in a human-approval UI.
So the MarketplaceSession built here is handed directly into
`agent.run(session=...)` for the lifetime of one node call and never
written back into the dict orchestrator.py returns as node output —
grep orchestrator.py's `_run_agent_node` and it never assigns `session`
into the returned state update. Only `state["marketplace"]` (a plain
string like "meesho") flows through state; the session object itself
does not.

TWO SOURCES, CHECKED IN ORDER
-----------------------------------------------------------------------
1. `_REGISTERED` — an in-memory seller_id -> platform -> credentials
   map. Empty today. This is the integration point for the backend:
   once real per-seller OAuth/login exists, it calls
   `session_store.register(seller_id, platform, credentials)` once per
   connected account and everything above this file (agents, tools,
   orchestrator) needs zero changes.
2. Environment variables (`backend/.env`) — a single-seller dev/test
   convenience so the graph is actually runnable today without a real
   backend: `AMAZON_*` / `FLIPKART_*` / `MEESHO_*` prefixed vars, same
   naming convention connectors/flipkart_api_connector.py already uses
   for FLIPKART_CLIENT_ID etc.

Returns None (not a session with empty credentials) when nothing is
configured for Meesho/Flipkart — a MarketplaceSession with no
credentials would just fail confusingly two layers down inside a
Playwright login or an OAuth call instead of failing clearly here.
Amazon is the one exception: its connector is Mock Mode
(sample_data/amazon/products.json), so a bare session with no
credentials is legitimate and expected to work.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from ai.connectors_layer.marketplace_connector import MarketplaceSession

_REGISTERED: Dict[str, Dict[str, Dict[str, Any]]] = {}

_ENV_CREDENTIAL_FIELDS = (
    ("USERNAME", "username"),
    ("PASSWORD", "password"),
    ("ACCESS_TOKEN", "access_token"),
    ("REFRESH_TOKEN", "refresh_token"),
    ("STORAGE_STATE_PATH", "storage_state_path"),
)


def register(seller_id: str, platform: str, credentials: Dict[str, Any]) -> None:
    """
    Attach a live session's credentials for one seller+platform.
    Idempotent/overwriting by design — reconnecting an account should
    just replace the old credentials, not require a separate "update"
    call. This is the ONE function the backend needs to call once real
    seller auth exists; nothing else in this file, or in orchestrator.py,
    needs to change when that happens.
    """
    _REGISTERED.setdefault(seller_id, {})[platform] = dict(credentials)


def clear(seller_id: str, platform: Optional[str] = None) -> None:
    """Mostly for tests — drop one platform's registered session, or
    all of a seller's, without leaving stale state between test runs."""
    if seller_id not in _REGISTERED:
        return
    if platform is None:
        _REGISTERED.pop(seller_id, None)
    else:
        _REGISTERED[seller_id].pop(platform, None)


def _env_credentials(platform: str) -> Dict[str, Any]:
    prefix = platform.upper()
    creds: Dict[str, Any] = {}
    for suffix, key in _ENV_CREDENTIAL_FIELDS:
        value = os.getenv(f"{prefix}_{suffix}")
        if value:
            creds[key] = value
    return creds


def get_marketplace_session(seller_id: str, platform: Optional[str]) -> Optional[MarketplaceSession]:
    if not platform or platform == "general":
        return None

    credentials = _REGISTERED.get(seller_id, {}).get(platform)
    if credentials is None:
        credentials = _env_credentials(platform)

    if not credentials and platform != "amazon":
        return None

    return MarketplaceSession(platform=platform, seller_id=seller_id, credentials=credentials)

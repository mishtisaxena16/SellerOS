"""
amazon_sdk — reusable Login-with-Amazon (LWA) OAuth + SP-API client
foundation, kept separate from amazon_connector.py (which stays Mock
Mode / sample-data-backed) so that later phases (Orders, Inventory,
Listings, ...) can build on this without touching connector.py's
public contract at all.

Modules:
    config    — region -> SP-API / Seller Central base URLs, marketplace IDs
    auth      — OAuth authorization URL, state CSRF token, code/refresh/
                access token exchange, per-seller access-token cache
    client    — shared HTTP client: bearer auth, retry, rate-limit
                backoff, pagination helper, error translation
"""

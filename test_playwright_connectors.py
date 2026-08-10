"""
Regression tests for three real bugs found by actually running
flipkart_playwright_connector.py / meesho_connector.py against a local
mock panel server (tests/mock_panel_server.py) — not by code review
alone. None of these depend on the real Flipkart/Meesho CSS
selectors matching production (that remains genuinely unverified
without live seller access — see each connector's own module
docstring) — they test the connector's *mechanics*, which are
independent of exactly which data-testid strings the real sites use.

1. `page` parameter was accepted but silently ignored — fetch_orders
   (etc.) always returned the panel's own first page regardless of
   what page was requested.
2. Rate-limit detection ran too late — a rate-limited response has no
   row elements, so the code timed out waiting for rows (15s) before
   ever checking for the rate-limit banner, misreporting a specific,
   actionable RateLimitError as a generic "did not respond in time".
3. `browser.launch()` sat outside the try block — a missing/broken
   Chromium install (e.g. `playwright install chromium` never run)
   raised a raw, unmapped Playwright Error instead of a diagnosable
   MarketplaceUnavailableError.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mock_panel_server import start_mock_server  # noqa: E402

import backend.ai.connectors_layer.flipkart_playwright_connector as fk  # noqa: E402
import backend.ai.connectors_layer.meesho_connector as me  # noqa: E402
from backend.ai.connectors_layer.exceptions import RateLimitError  # noqa: E402


class FakeSession:
    def __init__(self, platform: str):
        self.seller_id = "seller_1"
        self.credentials = {"username": "test", "password": "test"}
        self.platform = platform


@pytest.fixture(params=[
    ("flipkart", "dash"),
    ("meesho", "panel"),
])
def connector(request):
    """Parametrized over both connectors — they share the exact same
    bugs and the exact same fix, so one test body covers both."""
    platform, panel_word = request.param
    mod = fk if platform == "flipkart" else me

    port = 8950 if platform == "flipkart" else 8951
    server, thread = start_mock_server(port)
    base = f"http://127.0.0.1:{port}"
    mod.BASE_URL = base
    mod.ROUTES = {
        "login": f"{base}/login",
        "catalog": f"{base}/{panel_word}/products" if platform == "flipkart" else f"{base}/panel/catalog",
        "orders": f"{base}/{panel_word}/orders",
        "shipments": f"{base}/{panel_word}/orders/shipments",
        "inventory": f"{base}/{panel_word}/listings" if platform == "flipkart" else f"{base}/panel/inventory",
    }
    yield mod, FakeSession(platform)
    server.shutdown()


def test_page_param_actually_skips_ahead(connector):
    mod, session = connector
    page1 = mod.fetch_orders(session, page=1, limit=3)
    page2 = mod.fetch_orders(session, page=2, limit=3)
    assert page1 != page2
    assert [o["orderId"] for o in page1] == ["ORD-0001", "ORD-0002", "ORD-0003"]
    assert [o["orderId"] for o in page2] == ["ORD-0004", "ORD-0005", "ORD-0006"]


def test_rate_limit_raises_specific_error_not_generic_timeout(connector):
    mod, session = connector
    with pytest.raises(RateLimitError):
        mod.fetch_orders(session, status="rate_limited_test", limit=5)


def test_multi_page_click_through_pagination_still_works(connector):
    mod, session = connector
    rows = mod.fetch_orders(session, limit=8)
    assert len(rows) == 8
    assert [o["orderId"] for o in rows] == [f"ORD-{i:04d}" for i in range(1, 9)]


def test_verify_connection_reports_connected(connector):
    mod, session = connector
    result = mod.verify_connection(session)
    assert result["is_connected"] is True

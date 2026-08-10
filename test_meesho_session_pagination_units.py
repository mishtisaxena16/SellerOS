"""
Unit-level tests for two Phase 5/6 fixes in meesho_connector.py, using
fake Page/Locator stand-ins instead of a real headless Chromium
instance (unlike test_playwright_connectors.py, which needs a real
browser + tests/mock_panel_server.py and can't run in an environment
with no network access to install Playwright's browser binaries).

These tests exercise the connector's internal mechanics directly
(_goto_with_session_recovery, _paginate_rows) rather than the public
fetch_*() facade, so they don't need sync_playwright()/a real browser
at all -- same "test the mechanics, not the unverified selectors"
philosophy as test_playwright_connectors.py's own docstring.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backend.ai.connectors_layer.meesho_connector as me  # noqa: E402


# ---------------------------------------------------------------------------
# Phase 5 — _goto_with_session_recovery
# ---------------------------------------------------------------------------

class FakePage:
    def __init__(self, redirect_to_login_once: bool):
        self.url = ""
        self._redirect_to_login_once = redirect_to_login_once
        self.goto_calls: list[str] = []

    def goto(self, url):
        self.goto_calls.append(url)
        if self._redirect_to_login_once and len(self.goto_calls) == 1:
            self.url = "https://supplier.meesho.com/login"
        else:
            self.url = url


class FakeSession:
    def __init__(self):
        self.seller_id = "seller_1"
        self.credentials = {"username": "u", "password": "p"}


def test_session_recovery_detects_login_redirect_and_retries(monkeypatch):
    """An expired stored session (goto lands on /login) triggers exactly
    one re-login + one retry of the original request -- not zero (silent
    failure) and not an infinite loop."""
    login_calls = []
    monkeypatch.setattr(me, "_login", lambda page, session, context: login_calls.append(1))

    page = FakePage(redirect_to_login_once=True)
    me._goto_with_session_recovery(page, FakeSession(), context=object(), url="https://supplier.meesho.com/panel/orders")

    assert login_calls == [1]  # re-login attempted exactly once
    assert page.goto_calls == [
        "https://supplier.meesho.com/panel/orders",  # original request
        "https://supplier.meesho.com/panel/orders",  # retried after login
    ]
    assert page.url == "https://supplier.meesho.com/panel/orders"  # ended up on the page we asked for, not stuck on /login


def test_session_recovery_is_a_noop_when_session_is_already_valid(monkeypatch):
    """A still-valid stored session should navigate once and never touch
    _login at all -- no wasted re-auth on the common/happy path."""
    login_calls = []
    monkeypatch.setattr(me, "_login", lambda page, session, context: login_calls.append(1))

    page = FakePage(redirect_to_login_once=False)
    me._goto_with_session_recovery(page, FakeSession(), context=object(), url="https://supplier.meesho.com/panel/orders")

    assert login_calls == []
    assert page.goto_calls == ["https://supplier.meesho.com/panel/orders"]


# ---------------------------------------------------------------------------
# Phase 6 — _paginate_rows dedup / safe termination
# ---------------------------------------------------------------------------

class FakeRow:
    def __init__(self, dataset: dict):
        self._dataset = dataset

    def evaluate(self, _js):
        return self._dataset


class FakeRowsLocator:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def count(self):
        return len(self._rows)

    def nth(self, i):
        return FakeRow(self._rows[i])


class FakeNextButtonLocator:
    def __init__(self, enabled: bool):
        self._enabled = enabled
        self.click_count = 0

    def count(self):
        return 1 if self._enabled else 0

    @property
    def first(self):
        return self

    def click(self):
        self.click_count += 1


class StuckPaginationPage:
    """Simulates a panel whose 'Next' button is clickable but the table
    never actually changes -- e.g. a disabled-state selector mismatch,
    which is exactly the class of bug Phase 6 asks to guard against
    without inventing/guessing real Meesho selectors."""

    def __init__(self, rows: list[dict], next_enabled: bool):
        self._rows_locator = FakeRowsLocator(rows)
        self._next_locator = FakeNextButtonLocator(next_enabled)

    def locator(self, selector):
        if selector == me.SELECTORS["pagination_next"]:
            return self._next_locator
        if selector == me.SELECTORS["rate_limit_banner"]:
            return FakeRowsLocator([])  # never rate-limited in this test
        return self._rows_locator

    def wait_for_load_state(self, _state):
        pass


def test_paginate_rows_stops_instead_of_looping_forever_on_stuck_pagination(monkeypatch):
    """Next button reports enabled forever, but the underlying rows never
    change page-to-page -- pagination must terminate (not hang / not
    return duplicate-padded results) once no new rows show up."""
    monkeypatch.setattr(me.time, "sleep", lambda _s: None)  # don't actually sleep in tests

    rows = [{"orderId": "ORD-0001"}, {"orderId": "ORD-0002"}]
    page = StuckPaginationPage(rows, next_enabled=True)

    result = me._paginate_rows(page, "order_row_selector", limit=10, skip_pages=0)

    assert len(result) == 2  # only the two genuinely distinct rows, no duplicates padded in to reach `limit`
    assert {r["orderId"] for r in result} == {"ORD-0001", "ORD-0002"}
    # Exactly one click: the second iteration sees zero new rows and
    # breaks before clicking Next again -- proof this terminates rather
    # than looping until `limit`/forever.
    assert page._next_locator.click_count == 1


def test_paginate_rows_collects_across_genuinely_new_pages(monkeypatch):
    """Sanity check the dedup logic doesn't accidentally break the normal
    multi-page case where each click DOES surface new rows."""
    monkeypatch.setattr(me.time, "sleep", lambda _s: None)

    pages = [
        [{"orderId": "ORD-0001"}, {"orderId": "ORD-0002"}],
        [{"orderId": "ORD-0003"}, {"orderId": "ORD-0004"}],
    ]

    class MultiPage(StuckPaginationPage):
        def __init__(self):
            self._call = 0
            super().__init__(pages[0], next_enabled=True)

        def locator(self, selector):
            if selector == me.SELECTORS["pagination_next"]:
                return self._next_locator
            if selector == me.SELECTORS["rate_limit_banner"]:
                return FakeRowsLocator([])
            idx = min(self._next_locator.click_count, len(pages) - 1)
            return FakeRowsLocator(pages[idx])

    page = MultiPage()
    result = me._paginate_rows(page, "order_row_selector", limit=4, skip_pages=0)

    assert [r["orderId"] for r in result] == ["ORD-0001", "ORD-0002", "ORD-0003", "ORD-0004"]

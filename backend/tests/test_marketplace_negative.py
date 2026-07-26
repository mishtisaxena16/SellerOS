"""
Negative-path and regression tests for the marketplace connect/
disconnect flow. Covers the bugs fixed in this pass:

1. Credentials leaking back in API responses (MarketplaceResponse /
   response_model).
2. Duplicate marketplace connections (connect must be an upsert, plus
   a DB-level UniqueConstraint as defense-in-depth).
3. Deleting a nonexistent/other-seller's marketplace raising a clean
   ValueError -> 404, not a bare 500 (router-level catch is exercised
   separately via the API; here we confirm the service still raises
   ValueError so the router has something to catch).
4. Platform whitelist validation.
5. The SECRET_KEY production startup guard.
6. Session restore on process restart, and that disconnect actually
   clears AI-runtime access rather than just the DB row.

These run against an isolated in-memory SQLite DB per test (never the
real selleros.db) and reset the in-process session_store registry
around every test, so tests can't leak state into each other or into
a real deployment.

NOTE: written and statically reviewed, but not executed in this
environment -- the sandbox has no network access, so `fastapi`,
`sqlalchemy`, etc. aren't installed here. Run with:
    cd Marketsellers/SellerOS && pytest backend/tests/test_marketplace_negative.py -v
before relying on these as a regression gate.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.ai.connectors_layer import session_store
from backend.config.settings import (
    InsecureConfigurationError,
    Settings,
    assert_secret_key_is_safe,
)
from backend.database.base import Base
from backend.model.marketplace_account import MarketplaceAccount

# Import User/Seller so their tables exist too -- MarketplaceAccount's
# seller_id column has a ForeignKey("sellers.id"), and while SQLite
# doesn't enforce FKs by default, creating the full schema keeps this
# test DB structurally honest with production.
from backend.model.seller import Seller  # noqa: F401
from backend.model.user import User  # noqa: F401
from backend.schema.marketplace import ConnectMarketplaceRequest, MarketplaceResponse
from backend.service.marketplace_service import MarketplaceService


@pytest.fixture
def db_session():
    """A fresh in-memory SQLite DB per test -- never touches selleros.db."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def clean_session_store():
    """session_store._REGISTERED is process-global; isolate every test."""
    session_store._REGISTERED.clear()
    yield
    session_store._REGISTERED.clear()


# --- 1. Credentials must never leak in the serialized response ------------

class TestCredentialsNeverLeakInResponse:
    def test_response_model_excludes_credentials_field(self, db_session):
        account = MarketplaceService.connect_marketplace(
            db=db_session,
            seller_id=1,
            platform="amazon",
            credentials={"api_key": "SECRET123"},
        )

        dumped = MarketplaceResponse.model_validate(account).model_dump()

        assert "credentials" not in dumped
        assert "SECRET123" not in str(dumped)

    def test_response_model_still_exposes_safe_fields(self, db_session):
        account = MarketplaceService.connect_marketplace(
            db=db_session, seller_id=1, platform="amazon", credentials={"api_key": "x"}
        )
        dumped = MarketplaceResponse.model_validate(account).model_dump()
        assert dumped["id"] == account.id
        assert dumped["platform"] == "amazon"
        assert "created_at" in dumped


# --- 2. Duplicate connect must upsert, not duplicate ------------------------

class TestDuplicateConnectIsUpsert:
    def test_connecting_same_platform_twice_updates_the_same_row(self, db_session):
        first = MarketplaceService.connect_marketplace(
            db=db_session, seller_id=1, platform="amazon", credentials={"api_key": "old"}
        )
        second = MarketplaceService.connect_marketplace(
            db=db_session, seller_id=1, platform="amazon", credentials={"api_key": "new"}
        )

        assert first.id == second.id

        rows = MarketplaceService.get_marketplaces(db=db_session, seller_id=1)
        assert len(rows) == 1
        assert rows[0].credentials["api_key"] == "new"

    def test_connecting_different_platforms_creates_separate_rows(self, db_session):
        MarketplaceService.connect_marketplace(db=db_session, seller_id=1, platform="amazon", credentials={})
        MarketplaceService.connect_marketplace(db=db_session, seller_id=1, platform="flipkart", credentials={})

        rows = MarketplaceService.get_marketplaces(db=db_session, seller_id=1)
        assert len(rows) == 2

    def test_two_different_sellers_can_each_connect_the_same_platform(self, db_session):
        MarketplaceService.connect_marketplace(db=db_session, seller_id=1, platform="amazon", credentials={})
        MarketplaceService.connect_marketplace(db=db_session, seller_id=2, platform="amazon", credentials={})

        assert len(MarketplaceService.get_marketplaces(db=db_session, seller_id=1)) == 1
        assert len(MarketplaceService.get_marketplaces(db=db_session, seller_id=2)) == 1

    def test_unique_constraint_blocks_a_raw_duplicate_insert(self, db_session):
        """Defense-in-depth: even code that bypasses the service's
        upsert logic entirely must be stopped by the DB itself."""
        db_session.add(MarketplaceAccount(seller_id=1, platform="amazon", credentials={}))
        db_session.commit()

        db_session.add(MarketplaceAccount(seller_id=1, platform="amazon", credentials={}))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


# --- 3. Deleting a nonexistent/foreign marketplace raises cleanly ----------

class TestDeleteNonexistentRaisesValueError:
    def test_delete_missing_id_raises_value_error(self, db_session):
        with pytest.raises(ValueError):
            MarketplaceService.delete_marketplace(db=db_session, seller_id=1, marketplace_id=9999)

    def test_delete_another_sellers_marketplace_raises_value_error(self, db_session):
        account = MarketplaceService.connect_marketplace(
            db=db_session, seller_id=1, platform="amazon", credentials={}
        )
        with pytest.raises(ValueError):
            MarketplaceService.delete_marketplace(db=db_session, seller_id=2, marketplace_id=account.id)

    def test_delete_does_not_affect_other_rows(self, db_session):
        account = MarketplaceService.connect_marketplace(
            db=db_session, seller_id=1, platform="amazon", credentials={}
        )
        with pytest.raises(ValueError):
            MarketplaceService.delete_marketplace(db=db_session, seller_id=1, marketplace_id=99999)

        # The failed delete must not have touched the real row.
        rows = MarketplaceService.get_marketplaces(db=db_session, seller_id=1)
        assert len(rows) == 1 and rows[0].id == account.id


# --- 4. Platform whitelist --------------------------------------------------

class TestPlatformWhitelist:
    @pytest.mark.parametrize("platform", ["amazon", "flipkart", "meesho", "AMAZON", " Flipkart "])
    def test_supported_platforms_are_accepted(self, platform):
        req = ConnectMarketplaceRequest(platform=platform, credentials={})
        assert req.platform in {"amazon", "flipkart", "meesho"}

    def test_unsupported_platform_is_rejected(self):
        with pytest.raises(ValidationError):
            ConnectMarketplaceRequest(platform="not_a_real_marketplace", credentials={})

    def test_empty_platform_is_rejected(self):
        with pytest.raises(ValidationError):
            ConnectMarketplaceRequest(platform="", credentials={})


# --- 5. SECRET_KEY production guard ----------------------------------------

class TestSecretKeyGuard:
    def test_refuses_default_secret_when_debug_is_false(self):
        bad = Settings(DEBUG=False, SECRET_KEY="CHANGE_THIS_IN_PRODUCTION")
        with pytest.raises(InsecureConfigurationError):
            assert_secret_key_is_safe(bad)

    def test_allows_default_secret_when_debug_is_true(self):
        dev = Settings(DEBUG=True, SECRET_KEY="CHANGE_THIS_IN_PRODUCTION")
        assert_secret_key_is_safe(dev)  # must not raise

    def test_allows_real_secret_when_debug_is_false(self):
        prod = Settings(DEBUG=False, SECRET_KEY="a-real-random-secret-value")
        assert_secret_key_is_safe(prod)  # must not raise


# --- 6. Disconnect actually clears AI-runtime access, restore repopulates it

class TestDisconnectAndRestoreSessionStore:
    def test_connect_registers_a_session(self, db_session):
        MarketplaceService.connect_marketplace(
            db=db_session, seller_id=1, platform="flipkart", credentials={"username": "u"}
        )
        session = session_store.get_marketplace_session("1", "flipkart")
        assert session is not None
        assert session.credentials["username"] == "u"

    def test_disconnect_clears_the_session(self, db_session):
        account = MarketplaceService.connect_marketplace(
            db=db_session, seller_id=1, platform="flipkart", credentials={"username": "u"}
        )
        MarketplaceService.delete_marketplace(db=db_session, seller_id=1, marketplace_id=account.id)

        # flipkart has no env-var fallback configured in a test
        # environment and isn't the Mock Mode exception (amazon), so
        # once cleared, no session should resolve for it at all.
        assert session_store.get_marketplace_session("1", "flipkart") is None

    def test_disconnect_does_not_affect_other_sellers_sessions(self, db_session):
        acct_1 = MarketplaceService.connect_marketplace(
            db=db_session, seller_id=1, platform="flipkart", credentials={"username": "seller1"}
        )
        MarketplaceService.connect_marketplace(
            db=db_session, seller_id=2, platform="flipkart", credentials={"username": "seller2"}
        )

        MarketplaceService.delete_marketplace(db=db_session, seller_id=1, marketplace_id=acct_1.id)

        assert session_store.get_marketplace_session("1", "flipkart") is None
        seller_2_session = session_store.get_marketplace_session("2", "flipkart")
        assert seller_2_session is not None
        assert seller_2_session.credentials["username"] == "seller2"

    def test_restore_all_sessions_repopulates_after_simulated_restart(self, db_session):
        MarketplaceService.connect_marketplace(
            db=db_session, seller_id=1, platform="flipkart", credentials={"username": "persisted"}
        )

        session_store._REGISTERED.clear()  # simulate a process restart
        assert session_store.get_marketplace_session("1", "flipkart") is None

        restored_count = MarketplaceService.restore_all_sessions(db_session)
        assert restored_count == 1

        session = session_store.get_marketplace_session("1", "flipkart")
        assert session is not None
        assert session.credentials["username"] == "persisted"

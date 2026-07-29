"""
Unit tests for the Amazon LWA OAuth foundation added in this phase:
- amazon_sdk/auth.py (state CSRF token, authorization URL, token
  exchange, per-seller access-token cache)
- amazon_sdk/client.py (bearer-token calls, retry/backoff, error
  translation)
- service/amazon_auth_service.py (the seller-facing authorize/callback
  flow, reusing MarketplaceService for encrypted persistence)
- connectors_layer/amazon_connector.verify_connection (Mock Mode
  fallback vs. live Marketplace Participation API)

No live Amazon credentials, live seller account, or network access
required anywhere in this file -- every HTTP call is mocked.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ai.connectors_layer import session_store
from backend.ai.connectors_layer.amazon_sdk import auth as amazon_auth
from backend.ai.connectors_layer.exceptions import AuthenticationError, InvalidCredentialsError
from backend.ai.connectors_layer.marketplace_connector import MarketplaceSession
from backend.ai.connectors_layer import amazon_connector
from backend.config.settings import Settings
from backend.database.base import Base
from backend.model.marketplace_account import MarketplaceAccount  # noqa: F401
from backend.model.seller import Seller  # noqa: F401
from backend.model.user import User  # noqa: F401
from backend.service.amazon_auth_service import AmazonAuthService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def clean_state():
    session_store._REGISTERED.clear()
    amazon_auth._token_cache.clear()
    yield
    session_store._REGISTERED.clear()
    amazon_auth._token_cache.clear()


@pytest.fixture(autouse=True)
def amazon_env(monkeypatch):
    monkeypatch.setenv("AMAZON_LWA_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("AMAZON_LWA_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("AMAZON_APP_ID", "amzn1.sp.solution.test")
    monkeypatch.setenv("AMAZON_OAUTH_REDIRECT_URI", "https://app.example.com/marketplaces/amazon/callback")
    # amazon_auth.generate_state/validate_state sign with settings.SECRET_KEY
    # (module-level singleton loaded at import time) -- patch it directly
    # rather than relying on env var reload timing.
    with patch("backend.ai.connectors_layer.amazon_sdk.auth.settings", Settings(SECRET_KEY="test-secret-key")):
        yield


# --- State token: CSRF protection -------------------------------------------

class TestStateToken:
    def test_valid_state_round_trips_seller_id(self):
        token = amazon_auth.generate_state("42")
        assert amazon_auth.validate_state(token) == "42"

    def test_tampered_state_is_rejected(self):
        token = amazon_auth.generate_state("42")
        raw, sig = token.split(".", 1)
        tampered = raw + "x." + sig
        with pytest.raises(AuthenticationError):
            amazon_auth.validate_state(tampered)

    def test_expired_state_is_rejected(self):
        with patch("backend.ai.connectors_layer.amazon_sdk.auth.time") as mock_time:
            mock_time.time.return_value = 1_000_000
            token = amazon_auth.generate_state("42")

        with patch("backend.ai.connectors_layer.amazon_sdk.auth.time") as mock_time:
            mock_time.time.return_value = 1_000_000 + amazon_auth.STATE_TTL_SECONDS + 1
            with pytest.raises(AuthenticationError):
                amazon_auth.validate_state(token)

    def test_malformed_state_is_rejected(self):
        with pytest.raises(AuthenticationError):
            amazon_auth.validate_state("not-a-valid-token")


# --- Authorization URL -------------------------------------------------------

class TestAuthorizationUrl:
    def test_builds_expected_url_shape(self):
        url = amazon_auth.build_authorization_url(seller_id="7", region="eu")
        assert url.startswith("https://sellercentral.amazon.in/apps/authorize/consent?")
        assert "application_id=amzn1.sp.solution.test" in url
        assert "redirect_uri=" in url
        assert "state=" in url

    def test_beta_flag_adds_version_param(self):
        url = amazon_auth.build_authorization_url(seller_id="7", region="eu", beta=True)
        assert "version=beta" in url

    def test_unsupported_region_rejected(self):
        with pytest.raises(ValueError):
            amazon_auth.build_authorization_url(seller_id="7", region="mars")

    def test_missing_app_id_raises_invalid_credentials(self, monkeypatch):
        monkeypatch.delenv("AMAZON_APP_ID", raising=False)
        with pytest.raises(InvalidCredentialsError):
            amazon_auth.build_authorization_url(seller_id="7")


# --- Token exchange (mocked HTTP) -------------------------------------------

class TestTokenExchange:
    @patch("backend.ai.connectors_layer.amazon_sdk.auth.requests.post")
    def test_exchange_code_for_refresh_token_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "Atza|fake",
                "refresh_token": "Atzr|fake",
                "token_type": "bearer",
                "expires_in": 3600,
            },
        )
        mock_post.return_value.raise_for_status = lambda: None

        result = amazon_auth.exchange_code_for_refresh_token("fake-spapi-code")

        assert result["refresh_token"] == "Atzr|fake"
        called_data = mock_post.call_args.kwargs["data"]
        assert called_data["grant_type"] == "authorization_code"
        assert called_data["code"] == "fake-spapi-code"
        assert called_data["client_id"] == "test-client-id"

    @patch("backend.ai.connectors_layer.amazon_sdk.auth.requests.post")
    def test_refresh_access_token_uses_refresh_grant(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"access_token": "Atza|fresh", "expires_in": 3600},
        )
        mock_post.return_value.raise_for_status = lambda: None

        result = amazon_auth.refresh_access_token("Atzr|fake")

        assert result["access_token"] == "Atza|fresh"
        called_data = mock_post.call_args.kwargs["data"]
        assert called_data["grant_type"] == "refresh_token"
        assert called_data["refresh_token"] == "Atzr|fake"

    @patch("backend.ai.connectors_layer.amazon_sdk.auth.requests.post")
    def test_http_error_raises_authentication_error_without_leaking_secret(self, mock_post):
        import requests

        response = MagicMock(status_code=400, text="invalid_grant")

        def _raise():
            raise requests.HTTPError(response=response)

        mock_post.return_value = MagicMock(raise_for_status=_raise)

        with pytest.raises(AuthenticationError) as exc_info:
            amazon_auth.exchange_code_for_refresh_token("bad-code")

        # The error message must never contain the client secret.
        assert "test-client-secret" not in str(exc_info.value)


# --- Access token cache -------------------------------------------------------

class TestAccessTokenCache:
    @patch("backend.ai.connectors_layer.amazon_sdk.auth.refresh_access_token")
    def test_caches_token_until_near_expiry(self, mock_refresh):
        mock_refresh.return_value = {"access_token": "Atza|1", "expires_in": 3600}

        first = amazon_auth.get_access_token("seller-1", "Atzr|fake")
        second = amazon_auth.get_access_token("seller-1", "Atzr|fake")

        assert first == second == "Atza|1"
        mock_refresh.assert_called_once()

    @patch("backend.ai.connectors_layer.amazon_sdk.auth.refresh_access_token")
    def test_different_sellers_do_not_share_cached_tokens(self, mock_refresh):
        mock_refresh.side_effect = [
            {"access_token": "Atza|seller1", "expires_in": 3600},
            {"access_token": "Atza|seller2", "expires_in": 3600},
        ]

        token_1 = amazon_auth.get_access_token("seller-1", "Atzr|one")
        token_2 = amazon_auth.get_access_token("seller-2", "Atzr|two")

        assert token_1 == "Atza|seller1"
        assert token_2 == "Atza|seller2"
        assert mock_refresh.call_count == 2


# --- Seller-facing service: full authorize + callback round trip ------------

class TestAmazonAuthService:
    def test_build_authorize_url_embeds_seller_id_in_state(self):
        url = AmazonAuthService.build_authorize_url(seller_id=99, region="eu")
        # Extract state= value and confirm it decodes back to seller 99.
        state = url.split("state=")[1].split("&")[0]
        assert amazon_auth.validate_state(state) == "99"

    @patch("backend.ai.connectors_layer.amazon_sdk.auth.requests.post")
    def test_handle_callback_persists_encrypted_refresh_token_and_registers_session(
        self, mock_post, db_session
    ):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "Atza|fake",
                "refresh_token": "Atzr|realistic-secret-value",
                "expires_in": 3600,
            },
        )
        mock_post.return_value.raise_for_status = lambda: None

        state = amazon_auth.generate_state("5")
        result = AmazonAuthService.handle_callback(
            db=db_session,
            state=state,
            spapi_oauth_code="fake-code",
            selling_partner_id="A1SELLERFAKE",
            region="eu",
        )

        assert result == {"seller_id": 5, "platform": "amazon", "status": "connected"}

        # Encrypted at rest -- same guarantee as every other platform
        # (backend/database/crypto.py), verified directly against the
        # raw DB row rather than trusting the ORM round-trip alone.
        from sqlalchemy import text

        raw = db_session.execute(
            text("SELECT credentials FROM marketplace_accounts WHERE seller_id=5 AND platform='amazon'")
        ).fetchone()
        assert "Atzr|realistic-secret-value" not in raw[0]

        # Immediately usable by the AI runtime without a restart.
        session = session_store.get_marketplace_session("5", "amazon")
        assert session is not None
        assert session.credentials["refresh_token"] == "Atzr|realistic-secret-value"

    def test_handle_callback_rejects_invalid_state(self, db_session):
        with pytest.raises(AuthenticationError):
            AmazonAuthService.handle_callback(
                db=db_session,
                state="garbage",
                spapi_oauth_code="fake-code",
            )

    @patch("backend.ai.connectors_layer.amazon_sdk.auth.requests.post")
    def test_handle_callback_raises_if_no_refresh_token_returned(self, mock_post, db_session):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"access_token": "Atza|fake", "expires_in": 3600},  # no refresh_token
        )
        mock_post.return_value.raise_for_status = lambda: None

        state = amazon_auth.generate_state("5")
        with pytest.raises(AuthenticationError):
            AmazonAuthService.handle_callback(db=db_session, state=state, spapi_oauth_code="fake-code")


# --- verify_connection: Mock Mode fallback vs. live SP-API call -------------

class TestVerifyConnection:
    def test_mock_mode_when_no_refresh_token(self):
        session = MarketplaceSession(platform="amazon", seller_id="1", credentials={})
        result = amazon_connector.verify_connection(session)
        assert result["is_connected"] is True
        assert "Mock Mode" in result["message"]

    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_live_mode_calls_marketplace_participations(self, mock_call):
        mock_call.return_value = {"payload": [{"marketplace": {"id": "A21TJRUUN4KGV"}}]}
        session = MarketplaceSession(
            platform="amazon",
            seller_id="1",
            credentials={"refresh_token": "Atzr|fake", "region": "eu"},
        )

        result = amazon_connector.verify_connection(session)

        assert result["is_connected"] is True
        assert "1 marketplace participation" in result["message"]
        mock_call.assert_called_once_with(session, "GET", "/sellers/v1/marketplaceParticipations")

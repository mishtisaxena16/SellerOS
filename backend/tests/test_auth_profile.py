"""
Tests for AuthService.update_profile and AuthService.change_password —
added alongside the PATCH /auth/me and POST /auth/change-password
endpoints so Settings can stop showing "not available yet" for profile
edits and password changes.

Same isolated-in-memory-SQLite pattern as test_marketplace_negative.py.

NOTE: written and statically reviewed, but not executed in this
environment -- the sandbox has no network access, so `fastapi`,
`sqlalchemy`, `passlib`, etc. aren't installed here. Run with:
    cd Marketsellers/SellerOS && pytest backend/tests/test_auth_profile.py -v
before relying on this as a regression gate.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.base import Base
from backend.model.seller import Seller
from backend.model.user import User
from backend.service.auth_service import AuthService


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


@pytest.fixture
def registered_user(db_session):
    """Register a user the same way AuthService.register_user does."""
    token_payload = AuthService.register_user(
        db=db_session,
        email="seller@example.com",
        password="correct-horse-battery",
        business_name="Original Business Name",
    )
    assert "access_token" in token_payload

    user = db_session.query(User).filter(User.email == "seller@example.com").first()
    seller = db_session.query(Seller).filter(Seller.user_id == user.id).first()
    return user, seller


class TestUpdateProfile:
    def test_updates_business_name(self, db_session, registered_user):
        _, seller = registered_user

        updated = AuthService.update_profile(
            db=db_session,
            seller=seller,
            business_name="New Business Name",
        )

        assert updated.business_name == "New Business Name"

    def test_persists_across_a_fresh_query(self, db_session, registered_user):
        _, seller = registered_user

        AuthService.update_profile(
            db=db_session,
            seller=seller,
            business_name="Persisted Name",
        )

        reloaded = db_session.query(Seller).filter(Seller.id == seller.id).first()
        assert reloaded.business_name == "Persisted Name"

    def test_does_not_touch_email_or_password(self, db_session, registered_user):
        user, seller = registered_user
        original_hash = user.password_hash
        original_email = user.email

        AuthService.update_profile(
            db=db_session,
            seller=seller,
            business_name="Renamed Co",
        )

        assert user.password_hash == original_hash
        assert user.email == original_email


class TestChangePassword:
    def test_changes_password_when_current_password_is_correct(self, db_session, registered_user):
        user, _ = registered_user

        AuthService.change_password(
            db=db_session,
            user=user,
            current_password="correct-horse-battery",
            new_password="a-brand-new-password",
        )

        # login_user re-verifies via the hash, so this is an
        # end-to-end check that the new password actually works.
        AuthService.login_user(
            db=db_session,
            email="seller@example.com",
            password="a-brand-new-password",
        )

    def test_rejects_wrong_current_password(self, db_session, registered_user):
        user, _ = registered_user

        with pytest.raises(ValueError, match="Current password is incorrect"):
            AuthService.change_password(
                db=db_session,
                user=user,
                current_password="totally-wrong",
                new_password="a-brand-new-password",
            )

    def test_old_password_stops_working_after_change(self, db_session, registered_user):
        user, _ = registered_user

        AuthService.change_password(
            db=db_session,
            user=user,
            current_password="correct-horse-battery",
            new_password="a-brand-new-password",
        )

        with pytest.raises(ValueError, match="Invalid email or password"):
            AuthService.login_user(
                db=db_session,
                email="seller@example.com",
                password="correct-horse-battery",
            )

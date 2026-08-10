"""
Tests for backend.ai.context.business_context.get_business_context.

Follows the same isolated-in-memory-SQLite pattern as
test_marketplace_negative.py / test_auth_profile.py. The four
marketplace_data_service functions (get_orders/get_inventory/
get_listings/get_analytics) are mocked here rather than exercised
end-to-end, since they already have their own coverage against the
tool/connector layer elsewhere -- this file only tests the
aggregation behavior that business_context.py itself adds:
assembling their output, degrading gracefully when no marketplace is
connected, and never computing its own business numbers.

NOTE: written and statically reviewed, but not executed in this
environment -- the sandbox has no network access, so `pytest`,
`sqlalchemy`, etc. aren't installed here. Run with:
    cd Marketsellers/SellerOS && pytest backend/tests/test_business_context.py -v
before relying on this as a regression gate.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.base import Base
from backend.model.marketplace_account import MarketplaceAccount
from backend.model.seller import Seller
from backend.model.user import User  # noqa: F401 -- Seller.user_id FK target
from backend.service.marketplace_data_service import NoMarketplaceConnectedError


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
def seller(db_session):
    user = User(email="seller@example.com", password_hash="x")
    db_session.add(user)
    db_session.flush()

    seller = Seller(user_id=user.id, business_name="Test Traders")
    db_session.add(seller)
    db_session.commit()
    return seller


class TestGetBusinessContextAssemblesEverySection:
    @pytest.mark.asyncio
    async def test_all_four_sections_present_with_connected_marketplace(self, db_session, seller):
        db_session.add(
            MarketplaceAccount(seller_id=seller.id, platform="amazon", credentials={})
        )
        db_session.commit()

        from backend.ai.context import business_context as bc

        with patch.object(
            bc, "get_orders", AsyncMock(return_value={"platform": "amazon", "success": True, "orders": []})
        ), patch.object(
            bc, "get_inventory", AsyncMock(return_value={"platform": "amazon", "success": True, "items": []})
        ), patch.object(
            bc, "get_listings", AsyncMock(return_value={"platform": "amazon", "success": True, "listings": []})
        ), patch.object(
            bc,
            "get_analytics",
            AsyncMock(
                return_value={
                    "platform": "amazon",
                    "sales_metrics": {"total_revenue": 1000},
                    "sales_metrics_message": None,
                    "business_metrics": {"pending_orders": 2},
                    "business_metrics_message": None,
                }
            ),
        ):
            context = await bc.get_business_context(db_session, seller.id)

        payload = context.to_dict()
        assert payload["seller"] == {"seller_id": seller.id, "business_name": "Test Traders"}
        assert payload["orders"]["success"] is True
        assert payload["inventory"]["success"] is True
        assert payload["listings"]["success"] is True
        assert payload["analytics"]["sales_metrics"]["total_revenue"] == 1000
        assert payload["marketplace"] == {"platform": "amazon", "connected_marketplaces": 1}
        assert "generatedAt" in payload

    @pytest.mark.asyncio
    async def test_no_marketplace_connected_degrades_gracefully(self, db_session, seller):
        from backend.ai.context import business_context as bc

        with patch.object(
            bc,
            "get_orders",
            AsyncMock(side_effect=NoMarketplaceConnectedError("No marketplace account is connected yet.")),
        ):
            context = await bc.get_business_context(db_session, seller.id)

        payload = context.to_dict()
        assert payload["orders"]["success"] is False
        assert payload["inventory"]["success"] is False
        assert payload["listings"]["success"] is False
        assert payload["analytics"]["sales_metrics"] is None
        assert payload["marketplace"]["connected_marketplaces"] == 0
        # Seller section is unaffected -- it never depends on a connected marketplace.
        assert payload["seller"]["business_name"] == "Test Traders"

    @pytest.mark.asyncio
    async def test_unknown_seller_reports_none_business_name_not_a_crash(self, db_session):
        from backend.ai.context import business_context as bc

        with patch.object(
            bc,
            "get_orders",
            AsyncMock(side_effect=NoMarketplaceConnectedError("No marketplace account is connected yet.")),
        ):
            context = await bc.get_business_context(db_session, seller_id=999)

        assert context.seller == {"seller_id": 999, "business_name": None}

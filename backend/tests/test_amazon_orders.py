"""
Unit tests for the Amazon Orders API v2026-01-01 integration added this
phase:
- amazon_sdk/orders.py (search_orders, iterate_orders, get_order --
  param building, the createdAfter/lastUpdatedAfter mutual-exclusivity
  rule, pagination)
- amazon_connector.fetch_orders / fetch_order (Mock Mode vs. Live Mode
  dispatch, status filtering, page/limit slicing)
- normalizer.normalize_order for platform="amazon" (new nested field
  shape -> Order/OrderItem)
- marketplace_connector.get_orders / get_order (end-to-end through the
  public dispatch layer)

No live Amazon credentials, live seller account, or network access
required anywhere in this file -- every HTTP call is mocked at
amazon_sdk.client.call / amazon_sdk.client.paginate.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest

from backend.ai.connectors_layer import amazon_connector
from backend.ai.connectors_layer.amazon_sdk import orders as amazon_orders
from backend.ai.connectors_layer.exceptions import ConnectorError, RateLimitError
from backend.ai.connectors_layer.marketplace_connector import MarketplaceSession
from backend.ai.connectors_layer import marketplace_connector
from backend.ai.connectors_layer.normalizer import normalize_order


def _mock_session(**credentials) -> MarketplaceSession:
    return MarketplaceSession(platform="amazon", seller_id="seller-1", credentials=credentials)


def _live_session() -> MarketplaceSession:
    return _mock_session(refresh_token="Atzr|fake-refresh-token", region="eu")


SAMPLE_RAW_ORDER = {
    "orderId": "402-1234567-8901234",
    "createdTime": "2026-07-18T10:32:00Z",
    "lastUpdatedTime": "2026-07-19T06:15:00Z",
    "salesChannel": {"marketplaceId": "A21TJRUUN4KGV", "marketplaceName": "Amazon.in"},
    "fulfillment": {
        "fulfillmentStatus": "SHIPPED",
        "fulfilledBy": "MERCHANT",
        "fulfillmentServiceLevel": "Standard",
    },
    "proceeds": {"grandTotal": {"amount": "799.00", "currencyCode": "INR"}},
    "orderItems": [
        {
            "orderItemId": "90111222333441",
            "quantityOrdered": 1,
            "product": {"sellerSku": "AMZ-SKU-001", "asin": "B0EXAMPLE01", "title": "Sample Product 1"},
            "proceeds": {
                "proceedsTotal": {"amount": "799.00", "currencyCode": "INR"},
                "breakdowns": [{"type": "ITEM", "subtotal": {"amount": "799.00", "currencyCode": "INR"}}],
            },
        }
    ],
}


# ---------------------------------------------------------------------------
# amazon_sdk/orders.py — param building
# ---------------------------------------------------------------------------

class TestSearchOrdersParamBuilding:
    def test_requires_exactly_one_of_created_after_or_last_updated_after(self):
        with pytest.raises(ValueError):
            amazon_orders._build_search_params(["A21TJRUUN4KGV"])  # neither given

    def test_rejects_both_created_after_and_last_updated_after(self):
        with pytest.raises(ValueError):
            amazon_orders._build_search_params(
                ["A21TJRUUN4KGV"],
                created_after=datetime(2026, 1, 1),
                last_updated_after=datetime(2026, 1, 1),
            )

    def test_created_before_cannot_combine_with_last_updated_after(self):
        with pytest.raises(ValueError):
            amazon_orders._build_search_params(
                ["A21TJRUUN4KGV"],
                last_updated_after=datetime(2026, 1, 1),
                created_before=datetime(2026, 1, 2),
            )

    def test_builds_created_after_params_with_default_included_data(self):
        params = amazon_orders._build_search_params(
            ["A21TJRUUN4KGV"], created_after=datetime(2026, 7, 1)
        )
        assert params["marketplaceIds"] == ["A21TJRUUN4KGV"]
        assert params["createdAfter"] == "2026-07-01T00:00:00"
        assert params["includedData"] == ["FULFILLMENT", "PROCEEDS"]
        assert "paginationToken" not in params

    def test_pagination_token_supersedes_all_filters(self):
        params = amazon_orders._build_search_params(
            ["A21TJRUUN4KGV"],
            created_after=datetime(2026, 7, 1),
            pagination_token="tok-abc",
        )
        assert params == {"marketplaceIds": ["A21TJRUUN4KGV"], "paginationToken": "tok-abc"}

    def test_fulfillment_statuses_and_fulfilled_by_passed_through(self):
        params = amazon_orders._build_search_params(
            ["A21TJRUUN4KGV"],
            created_after=datetime(2026, 7, 1),
            fulfillment_statuses=["SHIPPED", "UNSHIPPED"],
            fulfilled_by="MERCHANT",
        )
        assert params["fulfillmentStatuses"] == ["SHIPPED", "UNSHIPPED"]
        assert params["fulfilledBy"] == "MERCHANT"

    def test_custom_included_data_overrides_default(self):
        params = amazon_orders._build_search_params(
            ["A21TJRUUN4KGV"], created_after=datetime(2026, 7, 1), included_data=["BUYER"]
        )
        assert params["includedData"] == ["BUYER"]


class TestResolveMarketplaceIds:
    def test_uses_session_marketplace_id_when_set(self):
        session = MarketplaceSession(platform="amazon", seller_id="1", marketplace_id="ATVPDKIKX0DER")
        assert amazon_orders._resolve_marketplace_ids(session) == ["ATVPDKIKX0DER"]

    def test_defaults_to_india_when_unset(self):
        session = _mock_session()
        assert amazon_orders._resolve_marketplace_ids(session) == ["A21TJRUUN4KGV"]


# ---------------------------------------------------------------------------
# amazon_sdk/orders.py — search_orders / get_order / iterate_orders
# ---------------------------------------------------------------------------

class TestSearchOrdersCall:
    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_search_orders_calls_expected_path(self, mock_call):
        mock_call.return_value = {"orders": [SAMPLE_RAW_ORDER]}
        session = _live_session()

        result = amazon_orders.search_orders(session, created_after=datetime(2026, 7, 1))

        assert result["orders"] == [SAMPLE_RAW_ORDER]
        args, kwargs = mock_call.call_args
        assert args[1] == "GET"
        assert args[2] == "/orders/2026-01-01/orders"


class TestGetOrder:
    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_get_order_calls_expected_path_with_included_data(self, mock_call):
        mock_call.return_value = SAMPLE_RAW_ORDER
        session = _live_session()

        result = amazon_orders.get_order(session, "402-1234567-8901234")

        assert result == SAMPLE_RAW_ORDER
        args, kwargs = mock_call.call_args
        assert args[2] == "/orders/2026-01-01/orders/402-1234567-8901234"
        assert kwargs["params"]["includedData"] == ["FULFILLMENT", "PROCEEDS"]


class TestIterateOrders:
    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_single_page_no_pagination(self, mock_call):
        mock_call.return_value = {"orders": [SAMPLE_RAW_ORDER]}
        session = _live_session()

        results = list(amazon_orders.iterate_orders(session, last_updated_after=datetime(1970, 1, 1)))

        assert results == [SAMPLE_RAW_ORDER]
        assert mock_call.call_count == 1

    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_follows_pagination_token_across_pages(self, mock_call):
        page1 = {"orders": [SAMPLE_RAW_ORDER], "pagination": {"nextToken": "tok-2"}}
        page2 = {"orders": [{**SAMPLE_RAW_ORDER, "orderId": "402-2222222-2222222"}]}
        mock_call.side_effect = [page1, page2]
        session = _live_session()

        results = list(amazon_orders.iterate_orders(session, last_updated_after=datetime(1970, 1, 1)))

        assert [o["orderId"] for o in results] == ["402-1234567-8901234", "402-2222222-2222222"]
        assert mock_call.call_count == 2
        # second call must carry the renamed request param (paginationToken, not nextToken)
        second_call_kwargs = mock_call.call_args_list[1].kwargs
        assert second_call_kwargs["params"]["paginationToken"] == "tok-2"

    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_empty_orders_response_yields_nothing(self, mock_call):
        mock_call.return_value = {"orders": []}
        session = _live_session()

        results = list(amazon_orders.iterate_orders(session, last_updated_after=datetime(1970, 1, 1)))

        assert results == []

    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_falls_back_to_payload_orders_key(self, mock_call):
        mock_call.return_value = {"payload": {"orders": [SAMPLE_RAW_ORDER]}}
        session = _live_session()

        results = list(amazon_orders.iterate_orders(session, last_updated_after=datetime(1970, 1, 1)))

        assert results == [SAMPLE_RAW_ORDER]


# ---------------------------------------------------------------------------
# amazon_connector.fetch_orders / fetch_order — Mock Mode vs Live Mode
# ---------------------------------------------------------------------------

class TestFetchOrdersMockMode:
    def test_returns_sample_orders(self):
        session = _mock_session()
        orders = amazon_connector.fetch_orders(session)
        assert len(orders) == 2
        assert orders[0]["orderId"] == "402-1234567-8901234"

    def test_status_filter_is_case_insensitive(self):
        session = _mock_session()
        orders = amazon_connector.fetch_orders(session, status="shipped")
        assert len(orders) == 1
        assert orders[0]["fulfillment"]["fulfillmentStatus"] == "SHIPPED"

    def test_pagination_slicing(self):
        session = _mock_session()
        page1 = amazon_connector.fetch_orders(session, page=1, limit=1)
        page2 = amazon_connector.fetch_orders(session, page=2, limit=1)
        assert len(page1) == 1
        assert len(page2) == 1
        assert page1[0]["orderId"] != page2[0]["orderId"]

    def test_fetch_order_found(self):
        session = _mock_session()
        order = amazon_connector.fetch_order(session, "402-1234567-8901234")
        assert order["orderId"] == "402-1234567-8901234"

    def test_fetch_order_not_found_raises_connector_error(self):
        session = _mock_session()
        with pytest.raises(ConnectorError):
            amazon_connector.fetch_order(session, "no-such-order")


class TestFetchOrdersLiveMode:
    @patch("backend.ai.connectors_layer.amazon_sdk.orders.iterate_orders")
    def test_delegates_to_iterate_orders_with_default_window(self, mock_iterate):
        mock_iterate.return_value = iter([SAMPLE_RAW_ORDER])
        session = _live_session()

        orders = amazon_connector.fetch_orders(session)

        assert orders == [SAMPLE_RAW_ORDER]
        _, kwargs = mock_iterate.call_args
        assert "last_updated_after" in kwargs  # no start_date given -> lastUpdatedAfter fallback

    @patch("backend.ai.connectors_layer.amazon_sdk.orders.iterate_orders")
    def test_start_date_uses_created_after(self, mock_iterate):
        mock_iterate.return_value = iter([SAMPLE_RAW_ORDER])
        session = _live_session()

        amazon_connector.fetch_orders(session, start_date=datetime(2026, 7, 1))

        _, kwargs = mock_iterate.call_args
        assert kwargs["created_after"] == datetime(2026, 7, 1)
        assert "last_updated_after" not in kwargs

    @patch("backend.ai.connectors_layer.amazon_sdk.orders.iterate_orders")
    def test_status_is_uppercased_for_fulfillment_statuses(self, mock_iterate):
        mock_iterate.return_value = iter([SAMPLE_RAW_ORDER])
        session = _live_session()

        amazon_connector.fetch_orders(session, status="shipped")

        _, kwargs = mock_iterate.call_args
        assert kwargs["fulfillment_statuses"] == ["SHIPPED"]

    @patch("backend.ai.connectors_layer.amazon_sdk.orders.iterate_orders")
    def test_limit_stops_iteration_early(self, mock_iterate):
        mock_iterate.return_value = iter([SAMPLE_RAW_ORDER] * 5)
        session = _live_session()

        orders = amazon_connector.fetch_orders(session, limit=2)

        assert len(orders) == 2

    @patch("backend.ai.connectors_layer.amazon_sdk.orders.get_order")
    def test_fetch_order_delegates_to_sdk(self, mock_get_order):
        mock_get_order.return_value = SAMPLE_RAW_ORDER
        session = _live_session()

        order = amazon_connector.fetch_order(session, "402-1234567-8901234")

        assert order == SAMPLE_RAW_ORDER
        mock_get_order.assert_called_once_with(session, "402-1234567-8901234")


class TestFetchOrdersErrorPropagation:
    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_rate_limit_error_propagates_through_iterate_orders(self, mock_call):
        mock_call.side_effect = RateLimitError("throttled")
        session = _live_session()

        with pytest.raises(RateLimitError):
            list(amazon_orders.iterate_orders(session, last_updated_after=datetime(1970, 1, 1)))

    @patch("backend.ai.connectors_layer.amazon_sdk.orders.iterate_orders")
    def test_connector_error_wrapped_by_dispatch(self, mock_iterate):
        # marketplace_connector._dispatch wraps unexpected exceptions in
        # ConnectorError, but lets ConnectorError subclasses (like
        # RateLimitError) pass through unchanged.
        mock_iterate.side_effect = RateLimitError("throttled")
        session = _live_session()

        with pytest.raises(RateLimitError):
            marketplace_connector.get_orders(session)


# ---------------------------------------------------------------------------
# normalizer.normalize_order — Amazon v2026-01-01 shape
# ---------------------------------------------------------------------------

class TestNormalizeAmazonOrder:
    def test_normalizes_core_fields(self):
        order = normalize_order("amazon", SAMPLE_RAW_ORDER)

        assert order.platform == "amazon"
        assert order.order_id == "402-1234567-8901234"
        assert order.status == "SHIPPED"
        assert order.total_amount == 799.0
        assert order.currency == "INR"
        assert order.fulfillment_channel == "MERCHANT"
        assert order.marketplace == "Amazon.in"
        assert order.shipping_service_level == "Standard"
        assert order.item_count == 1

    def test_normalizes_dates(self):
        order = normalize_order("amazon", SAMPLE_RAW_ORDER)
        assert order.order_date == datetime.fromisoformat("2026-07-18T10:32:00+00:00")
        assert order.last_updated_date == datetime.fromisoformat("2026-07-19T06:15:00+00:00")

    def test_normalizes_order_items(self):
        order = normalize_order("amazon", SAMPLE_RAW_ORDER)
        assert len(order.items) == 1
        item = order.items[0]
        assert item.sku == "AMZ-SKU-001"
        assert item.asin == "B0EXAMPLE01"
        assert item.title == "Sample Product 1"
        assert item.quantity == 1
        assert item.unit_price == 799.0
        assert item.order_item_id == "90111222333441"

    def test_missing_proceeds_leaves_unit_price_and_total_none(self):
        raw = {
            "orderId": "402-0000000-0000000",
            "createdTime": "2026-07-01T00:00:00Z",
            "fulfillment": {"fulfillmentStatus": "PENDING", "fulfilledBy": "AMAZON"},
            "salesChannel": {"marketplaceName": "Amazon.in"},
            "orderItems": [
                {"orderItemId": "x", "quantityOrdered": 1, "product": {"sellerSku": "SKU-X"}}
            ],
        }
        order = normalize_order("amazon", raw)
        assert order.total_amount is None
        assert order.items[0].unit_price is None
        # currency falls back to the Order model default (INR) when
        # proceeds.grandTotal.currencyCode isn't present in the raw payload
        assert order.currency == "INR"

    def test_empty_order_items_normalizes_to_empty_list(self):
        raw = {**SAMPLE_RAW_ORDER, "orderItems": []}
        order = normalize_order("amazon", raw)
        assert order.items == []
        assert order.item_count == 0

    def test_raw_payload_preserved_verbatim(self):
        order = normalize_order("amazon", SAMPLE_RAW_ORDER)
        assert order.raw == SAMPLE_RAW_ORDER


# ---------------------------------------------------------------------------
# marketplace_connector — end-to-end through the public dispatch layer
# ---------------------------------------------------------------------------

class TestMarketplaceConnectorOrdersDispatch:
    def test_get_orders_mock_mode_returns_normalized_orders(self):
        session = _mock_session()
        orders = marketplace_connector.get_orders(session)
        assert len(orders) == 2
        assert all(o.platform == "amazon" for o in orders)
        assert {o.order_id for o in orders} == {"402-1234567-8901234", "402-2345678-9012345"}

    def test_get_order_mock_mode_returns_normalized_order(self):
        session = _mock_session()
        order = marketplace_connector.get_order(session, "402-1234567-8901234")
        assert order.order_id == "402-1234567-8901234"
        assert order.status == "SHIPPED"

    def test_get_order_not_found_raises_connector_error(self):
        session = _mock_session()
        with pytest.raises(ConnectorError):
            marketplace_connector.get_order(session, "does-not-exist")

    @patch("backend.ai.connectors_layer.amazon_sdk.orders.iterate_orders")
    def test_get_orders_live_mode_normalizes_sdk_output(self, mock_iterate):
        mock_iterate.return_value = iter([SAMPLE_RAW_ORDER])
        session = _live_session()

        orders = marketplace_connector.get_orders(session)

        assert len(orders) == 1
        assert orders[0].order_id == "402-1234567-8901234"
        assert orders[0].fulfillment_channel == "MERCHANT"

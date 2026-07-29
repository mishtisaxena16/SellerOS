"""
Unit tests for the Amazon Listings Items API integration added in RC1
Phase 1A (Inventory / Listings / Product Details / Pricing).

No live credentials or network required -- every SP-API call is mocked
at amazon_sdk.client.call / amazon_sdk.client.paginate.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.ai.connectors_layer import amazon_connector
from backend.ai.connectors_layer.amazon_sdk import listings as amazon_listings
from backend.ai.connectors_layer.exceptions import ConnectorError
from backend.ai.connectors_layer.marketplace_connector import MarketplaceSession
from backend.ai.connectors_layer import marketplace_connector
from backend.ai.connectors_layer.normalizer import normalize_product, normalize_inventory


def _mock_session(**credentials) -> MarketplaceSession:
    return MarketplaceSession(platform="amazon", seller_id="seller-1", credentials=credentials)


def _live_session() -> MarketplaceSession:
    return _mock_session(refresh_token="Atzr|fake-refresh-token", region="eu", selling_partner_id="A1B2C3D4E5")


SAMPLE_LISTING = {
    "sku": "AMZ-SKU-001",
    "summaries": [
        {
            "marketplaceId": "A21TJRUUN4KGV",
            "asin": "B0EXAMPLE01",
            "itemName": "Cotton Kurti - Blue Floral",
            "status": ["BUYABLE", "DISCOVERABLE"],
            "mainImage": {"link": "https://example.com/images/amz-sku-001.jpg"},
        }
    ],
    "attributes": {},
    "offers": [{"marketplaceId": "A21TJRUUN4KGV", "offerType": "B2C", "price": {"currencyCode": "INR", "amount": "799.00"}}],
    "fulfillmentAvailability": [{"fulfillmentChannelCode": "DEFAULT", "quantity": 42}],
}


# ---------------------------------------------------------------------------
# amazon_sdk/listings.py
# ---------------------------------------------------------------------------

class TestSellerIdResolution:
    def test_requires_selling_partner_id(self):
        session = _mock_session(refresh_token="fake", region="eu")  # no selling_partner_id
        with pytest.raises(ConnectorError):
            amazon_listings._seller_id(session)

    def test_uses_selling_partner_id_from_credentials(self):
        session = _live_session()
        assert amazon_listings._seller_id(session) == "A1B2C3D4E5"


class TestGetListingsItem:
    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_calls_expected_path_and_default_included_data(self, mock_call):
        mock_call.return_value = SAMPLE_LISTING
        session = _live_session()

        result = amazon_listings.get_listings_item(session, "AMZ-SKU-001")

        assert result == SAMPLE_LISTING
        args, kwargs = mock_call.call_args
        assert args[2] == "/listings/2021-08-01/items/A1B2C3D4E5/AMZ-SKU-001"
        assert kwargs["params"]["includedData"] == ["summaries", "attributes", "offers", "fulfillmentAvailability"]


class TestSearchListingsItems:
    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_calls_expected_path(self, mock_call):
        mock_call.return_value = {"numberOfResults": 1, "items": [SAMPLE_LISTING]}
        session = _live_session()

        result = amazon_listings.search_listings_items(session)

        assert result["items"] == [SAMPLE_LISTING]
        args, kwargs = mock_call.call_args
        assert args[2] == "/listings/2021-08-01/items"
        assert kwargs["params"]["sellerId"] == "A1B2C3D4E5"


class TestIterateListingsItems:
    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_follows_page_token_with_renamed_request_param(self, mock_call):
        page1 = {"items": [SAMPLE_LISTING], "pagination": {"nextToken": "tok-2"}}
        page2 = {"items": [{**SAMPLE_LISTING, "sku": "AMZ-SKU-002"}]}
        mock_call.side_effect = [page1, page2]
        session = _live_session()

        results = list(amazon_listings.iterate_listings_items(session))

        assert [i["sku"] for i in results] == ["AMZ-SKU-001", "AMZ-SKU-002"]
        assert mock_call.call_count == 2
        # the request param must be pageToken, NOT nextToken (the response
        # key) -- see search_listings_items' docstring for the gotcha
        second_kwargs = mock_call.call_args_list[1].kwargs
        assert second_kwargs["params"]["pageToken"] == "tok-2"
        assert "nextToken" not in second_kwargs["params"]

    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_empty_items_yields_nothing(self, mock_call):
        mock_call.return_value = {"items": []}
        session = _live_session()
        assert list(amazon_listings.iterate_listings_items(session)) == []


class TestPatchListingsItemQuantity:
    @patch("backend.ai.connectors_layer.amazon_sdk.client.call")
    def test_sends_correct_json_patch_body(self, mock_call):
        mock_call.return_value = {"sku": "AMZ-SKU-001", "status": "ACCEPTED", "submissionId": "abc123"}
        session = _live_session()

        result = amazon_listings.patch_listings_item_quantity(session, "AMZ-SKU-001", 10)

        assert result["status"] == "ACCEPTED"
        args, kwargs = mock_call.call_args
        assert args[1] == "PATCH"
        assert args[2] == "/listings/2021-08-01/items/A1B2C3D4E5/AMZ-SKU-001"
        body = kwargs["json_body"]
        assert body["productType"] == "PRODUCT"
        patch = body["patches"][0]
        assert patch["op"] == "replace"
        assert patch["path"] == "/attributes/fulfillment_availability"
        assert patch["value"] == [{"fulfillment_channel_code": "DEFAULT", "quantity": 10}]


# ---------------------------------------------------------------------------
# amazon_connector — Mock vs Live dispatch
# ---------------------------------------------------------------------------

class TestFetchProductsMockMode:
    def test_returns_sample_products(self):
        session = _mock_session()
        products = amazon_connector.fetch_products(session)
        assert len(products) == 2

    def test_category_filter(self):
        session = _mock_session()
        products = amazon_connector.fetch_products(session, category="footwear")
        assert len(products) == 1
        assert products[0]["sku"] == "AMZ-SKU-002"


class TestFetchProductsLiveMode:
    @patch("backend.ai.connectors_layer.amazon_sdk.listings.iterate_listings_items")
    def test_delegates_to_iterate_listings_items(self, mock_iter):
        mock_iter.return_value = iter([SAMPLE_LISTING])
        session = _live_session()

        products = amazon_connector.fetch_products(session)

        assert products == [SAMPLE_LISTING]

    @patch("backend.ai.connectors_layer.amazon_sdk.listings.iterate_listings_items")
    def test_category_filters_client_side_by_product_type(self, mock_iter):
        mock_iter.return_value = iter([{**SAMPLE_LISTING, "productType": "SHOES"}, {**SAMPLE_LISTING, "sku": "X", "productType": "APPAREL"}])
        session = _live_session()

        products = amazon_connector.fetch_products(session, category="APPAREL")

        assert len(products) == 1 and products[0]["sku"] == "X"


class TestFetchInventoryMockMode:
    def test_returns_sample_inventory(self):
        session = _mock_session()
        inventory = amazon_connector.fetch_inventory(session)
        assert len(inventory) == 2

    def test_sku_filter(self):
        session = _mock_session()
        inventory = amazon_connector.fetch_inventory(session, sku="AMZ-SKU-001")
        assert len(inventory) == 1 and inventory[0]["sku"] == "AMZ-SKU-001"


class TestFetchInventoryLiveMode:
    @patch("backend.ai.connectors_layer.amazon_sdk.listings.get_listings_item")
    def test_single_sku_uses_get_listings_item(self, mock_get):
        mock_get.return_value = SAMPLE_LISTING
        session = _live_session()

        inventory = amazon_connector.fetch_inventory(session, sku="AMZ-SKU-001")

        assert inventory == [SAMPLE_LISTING]
        mock_get.assert_called_once_with(session, "AMZ-SKU-001", included_data=["fulfillmentAvailability"])

    @patch("backend.ai.connectors_layer.amazon_sdk.listings.iterate_listings_items")
    def test_no_sku_iterates_all(self, mock_iter):
        mock_iter.return_value = iter([SAMPLE_LISTING])
        session = _live_session()

        inventory = amazon_connector.fetch_inventory(session)

        assert inventory == [SAMPLE_LISTING]


class TestUpdateInventory:
    def test_mock_mode_reports_not_persisted(self):
        session = _mock_session()
        result = amazon_connector.update_inventory(session, "AMZ-SKU-001", 5)
        assert result["status"] == "success"
        assert "Mock Mode" in result["message"]

    @patch("backend.ai.connectors_layer.amazon_sdk.listings.patch_listings_item_quantity")
    def test_live_mode_accepted(self, mock_patch):
        mock_patch.return_value = {"sku": "AMZ-SKU-001", "status": "ACCEPTED", "submissionId": "abc123"}
        session = _live_session()

        result = amazon_connector.update_inventory(session, "AMZ-SKU-001", 5)

        assert result["status"] == "success"
        assert result["updated_quantity"] == 5
        assert "abc123" in result["message"]

    @patch("backend.ai.connectors_layer.amazon_sdk.listings.patch_listings_item_quantity")
    def test_live_mode_rejected(self, mock_patch):
        mock_patch.return_value = {"sku": "AMZ-SKU-001", "status": "INVALID", "issues": [{"message": "bad sku"}]}
        session = _live_session()

        result = amazon_connector.update_inventory(session, "AMZ-SKU-001", 5)

        assert result["status"] == "failed"


# ---------------------------------------------------------------------------
# normalizer — amazon product/inventory
# ---------------------------------------------------------------------------

class TestNormalizeAmazonProduct:
    def test_normalizes_core_fields(self):
        product = normalize_product("amazon", SAMPLE_LISTING)
        assert product.sku == "AMZ-SKU-001"
        assert product.listing_id == "B0EXAMPLE01"
        assert product.title == "Cotton Kurti - Blue Floral"
        assert product.price == 799.0
        assert product.currency == "INR"
        assert product.stock_quantity == 42
        assert product.status == "BUYABLE,DISCOVERABLE"
        assert product.images == ["https://example.com/images/amz-sku-001.jpg"]

    def test_missing_offers_leaves_price_none(self):
        raw = {**SAMPLE_LISTING, "offers": []}
        product = normalize_product("amazon", raw)
        assert product.price is None
        assert product.currency == "INR"  # Order/Product model default, not from offers

    def test_prefers_default_fulfillment_channel(self):
        raw = {
            **SAMPLE_LISTING,
            "fulfillmentAvailability": [
                {"fulfillmentChannelCode": "AMAZON_IN", "quantity": 5},
                {"fulfillmentChannelCode": "DEFAULT", "quantity": 42},
            ],
        }
        product = normalize_product("amazon", raw)
        assert product.stock_quantity == 42


class TestNormalizeAmazonInventory:
    def test_normalizes_core_fields(self):
        inventory = normalize_inventory("amazon", SAMPLE_LISTING)
        assert inventory.sku == "AMZ-SKU-001"
        assert inventory.available_quantity == 42
        assert inventory.warehouse == "DEFAULT"

    def test_missing_fulfillment_availability_defaults_to_zero(self):
        raw = {"sku": "X", "fulfillmentAvailability": []}
        inventory = normalize_inventory("amazon", raw)
        assert inventory.available_quantity == 0
        assert inventory.warehouse is None


# ---------------------------------------------------------------------------
# marketplace_connector — end-to-end dispatch
# ---------------------------------------------------------------------------

class TestMarketplaceConnectorDispatch:
    def test_get_products_mock_mode(self):
        session = _mock_session()
        products = marketplace_connector.get_products(session)
        assert len(products) == 2 and all(p.platform == "amazon" for p in products)

    def test_get_inventory_mock_mode(self):
        session = _mock_session()
        inventory = marketplace_connector.get_inventory(session)
        assert len(inventory) == 2 and all(i.platform == "amazon" for i in inventory)

    def test_update_inventory_mock_mode_returns_response_model(self):
        session = _mock_session()
        result = marketplace_connector.update_inventory(session, "AMZ-SKU-001", 7)
        assert result.sku == "AMZ-SKU-001"
        assert result.updated_quantity == 7
        assert result.status == "success"

    @patch("backend.ai.connectors_layer.amazon_sdk.listings.iterate_listings_items")
    def test_get_products_live_mode_normalizes_sdk_output(self, mock_iter):
        mock_iter.return_value = iter([SAMPLE_LISTING])
        session = _live_session()

        products = marketplace_connector.get_products(session)

        assert len(products) == 1
        assert products[0].sku == "AMZ-SKU-001"
        assert products[0].price == 799.0

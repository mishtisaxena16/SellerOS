"""Tests for memory.models."""

from datetime import timezone

from memory.models import BusinessMemory, ChatMessage, ConversationMemory, SellerMemory, Warehouse


def test_chat_message_defaults_are_timezone_aware():
    message = ChatMessage(role="user", content="hello")
    assert message.timestamp.tzinfo is not None
    assert message.timestamp.tzinfo == timezone.utc


def test_chat_message_has_unique_id():
    a = ChatMessage(role="user", content="hi")
    b = ChatMessage(role="user", content="hi")
    assert a.message_id != b.message_id


def test_conversation_memory_defaults():
    convo = ConversationMemory(session_id="s1", seller_id="seller_1")
    assert convo.messages == []
    assert convo.total_tokens == 0
    assert convo.approval_required is False


def test_seller_memory_defaults():
    seller = SellerMemory(seller_id="seller_1", seller_name="ABC Traders")
    assert seller.preferred_language == "English"
    assert seller.preferred_currency == "INR"
    assert seller.connected_marketplaces == []


def test_business_memory_with_warehouses():
    business = BusinessMemory(
        seller_id="seller_1",
        business_name="ABC Traders",
        warehouses=[Warehouse(warehouse_id="wh_1", name="Delhi Hub")],
    )
    assert len(business.warehouses) == 1
    assert business.warehouses[0].name == "Delhi Hub"


def test_warehouse_models_are_unhashable_by_default():
    """
    Documents the property that motivates the key-based merge in
    updater.py: Pydantic v2 models with default config are unhashable.
    If this test ever starts failing (e.g. because someone adds
    `frozen=True` to Warehouse), the key-based merge logic in
    updater.py should be revisited.
    """
    wh = Warehouse(warehouse_id="wh_1", name="Delhi Hub")
    try:
        hash(wh)
        unhashable = False
    except TypeError:
        unhashable = True
    assert unhashable

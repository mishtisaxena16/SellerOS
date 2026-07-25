"""Tests for memory.storage.InMemoryStorage."""

from memory.models import ChatMessage, ConversationMemory, SellerMemory


def test_save_and_load_seller(storage):
    seller = SellerMemory(seller_id="s1", seller_name="ABC Traders")
    storage.save_seller(seller)

    loaded = storage.load_seller("s1")
    assert loaded is not None
    assert loaded.seller_name == "ABC Traders"


def test_load_missing_seller_returns_none(storage):
    assert storage.load_seller("does-not-exist") is None


def test_loaded_objects_are_copies_not_live_references(storage):
    """
    Regression test for the defensive-copy behavior: mutating an
    object returned by `load_seller` must not affect what's stored,
    since mutation should only happen via update_seller().
    """
    seller = SellerMemory(seller_id="s1", seller_name="ABC Traders")
    storage.save_seller(seller)

    loaded = storage.load_seller("s1")
    loaded.seller_name = "Mutated Name"

    reloaded = storage.load_seller("s1")
    assert reloaded.seller_name == "ABC Traders"


def test_conversation_message_pagination(storage):
    convo = ConversationMemory(session_id="sess1", seller_id="s1")
    convo.messages = [ChatMessage(role="user", content=f"msg {i}") for i in range(10)]
    storage.save_conversation(convo)

    page = storage.load_messages("sess1", offset=2, limit=3)
    assert [m.content for m in page] == ["msg 2", "msg 3", "msg 4"]


def test_load_messages_for_missing_conversation_returns_empty_list(storage):
    assert storage.load_messages("nope") == []


def test_delete_conversation_is_idempotent(storage):
    storage.delete_conversation("nonexistent")  # should not raise

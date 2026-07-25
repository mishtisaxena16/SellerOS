"""Tests for memory.retrieval.MemoryRetriever."""

from memory.conversation import ConversationManager
from memory.models import BusinessMemory, SellerMemory
from memory.retrieval import MemoryRetriever


def test_get_preferred_marketplace(storage):
    storage.save_seller(
        SellerMemory(seller_id="s1", seller_name="ABC", preferred_marketplace="Amazon")
    )
    retriever = MemoryRetriever(storage)
    assert retriever.get_preferred_marketplace("s1") == "Amazon"


def test_get_preferred_marketplace_missing_seller(storage):
    retriever = MemoryRetriever(storage)
    assert retriever.get_preferred_marketplace("nope") is None


def test_get_business_goals(storage):
    storage.save_business(
        BusinessMemory(seller_id="s1", business_name="ABC", business_goals=["Scale to $1M ARR"])
    )
    retriever = MemoryRetriever(storage)
    assert retriever.get_business_goals("s1") == ["Scale to $1M ARR"]


def test_get_recent_messages_respects_limit(storage):
    convo_manager = ConversationManager(storage)
    convo_manager.create_conversation("sess1", "s1")
    for i in range(20):
        convo_manager.add_message("sess1", "user", f"msg {i}")

    retriever = MemoryRetriever(storage)
    recent = retriever.get_recent_messages("sess1", limit=3)

    assert [m.content for m in recent] == ["msg 17", "msg 18", "msg 19"]


def test_get_recent_messages_limit_larger_than_history(storage):
    convo_manager = ConversationManager(storage)
    convo_manager.create_conversation("sess1", "s1")
    convo_manager.add_message("sess1", "user", "only message")

    retriever = MemoryRetriever(storage)
    recent = retriever.get_recent_messages("sess1", limit=50)

    assert len(recent) == 1

"""Tests for memory.filters.MemoryFilters."""

from memory.filters import MemoryFilters
from memory.models import ChatMessage, ConversationMemory


def test_by_role():
    messages = [
        ChatMessage(role="user", content="hi"),
        ChatMessage(role="assistant", content="hello"),
    ]
    result = MemoryFilters.by_role(messages, "user")
    assert len(result) == 1
    assert result[0].role == "user"


def test_by_keyword():
    messages = [
        ChatMessage(role="user", content="How do I price my Amazon product?"),
        ChatMessage(role="user", content="Unrelated message"),
    ]
    result = MemoryFilters.by_keyword(messages, "price")
    assert len(result) == 1


def test_latest_orders_by_timestamp_descending():
    import time

    messages = []
    for i in range(3):
        messages.append(ChatMessage(role="user", content=f"msg {i}"))
        time.sleep(0.001)

    result = MemoryFilters.latest(messages, limit=2)
    assert [m.content for m in result] == ["msg 2", "msg 1"]


def test_conversations_by_marketplace_matches_structured_field():
    """
    Regression test for the by_marketplace fix: filtering must use the
    conversation's `marketplace` field, not keyword-match message text
    (which would have wrongly matched a message that merely *mentions*
    a marketplace name it doesn't actually belong to).
    """
    amazon_convo = ConversationMemory(session_id="s1", seller_id="seller1", marketplace="Amazon")
    flipkart_convo = ConversationMemory(session_id="s2", seller_id="seller1", marketplace="Flipkart")
    flipkart_convo.messages.append(
        ChatMessage(role="user", content="Not Amazon, I meant Flipkart pricing.")
    )

    result = MemoryFilters.conversations_by_marketplace(
        [amazon_convo, flipkart_convo], "Amazon"
    )

    assert result == [amazon_convo]

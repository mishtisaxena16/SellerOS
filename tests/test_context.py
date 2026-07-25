"""Tests for memory.context.MemoryContextBuilder."""

from memory.context import MemoryContextBuilder
from memory.models import BusinessMemory, ChatMessage, ConversationMemory, SellerMemory


def test_build_with_all_memory_types():
    builder = MemoryContextBuilder()
    seller = SellerMemory(seller_id="s1", seller_name="ABC", preferred_marketplace="Amazon")
    business = BusinessMemory(seller_id="s1", business_name="ABC", business_goals=["Grow"])
    convo = ConversationMemory(session_id="c1", seller_id="s1")
    convo.messages.append(ChatMessage(role="user", content="hi"))

    context = builder.build(seller=seller, business=business, conversations=[convo])

    assert context["seller"]["name"] == "ABC"
    assert context["business"]["goals"] == ["Grow"]
    assert context["conversation_history"] == [{"role": "user", "content": "hi"}]


def test_build_with_nothing_returns_empty_shell():
    builder = MemoryContextBuilder()
    context = builder.build()
    assert context == {"seller": {}, "business": {}, "conversation_history": []}


def test_max_messages_per_conversation_caps_history():
    """
    Regression test for the context-window budget fix: without a cap,
    a long conversation would flatten every message into the context,
    which does not scale. With a cap, only the most recent N messages
    are included.
    """
    builder = MemoryContextBuilder()
    convo = ConversationMemory(session_id="c1", seller_id="s1")
    for i in range(50):
        convo.messages.append(ChatMessage(role="user", content=f"msg {i}"))

    context = builder.build(conversations=[convo], max_messages_per_conversation=5)

    assert len(context["conversation_history"]) == 5
    assert context["conversation_history"][-1]["content"] == "msg 49"

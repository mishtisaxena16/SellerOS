"""Tests for memory.conversation.ConversationManager."""

import pytest

from memory.conversation import ConversationManager
from memory.exceptions import MemoryNotFoundError


def test_create_and_get_conversation(storage):
    manager = ConversationManager(storage)
    manager.create_conversation("sess1", "seller1", marketplace="Amazon")

    convo = manager.get_conversation("sess1")
    assert convo is not None
    assert convo.marketplace == "Amazon"
    assert convo.messages == []


def test_add_message_appends_and_updates_timestamp(storage):
    manager = ConversationManager(storage)
    manager.create_conversation("sess1", "seller1")

    manager.add_message("sess1", "user", "Create an optimized Amazon listing.")
    manager.add_message("sess1", "assistant", "Generated listing.")

    messages = manager.get_messages("sess1")
    assert [m.content for m in messages] == [
        "Create an optimized Amazon listing.",
        "Generated listing.",
    ]


def test_add_message_to_missing_conversation_raises(storage):
    manager = ConversationManager(storage)
    with pytest.raises(MemoryNotFoundError):
        manager.add_message("nope", "user", "hi")


def test_clear_conversation(storage):
    manager = ConversationManager(storage)
    manager.create_conversation("sess1", "seller1")
    manager.add_message("sess1", "user", "hi")

    manager.clear_conversation("sess1")

    assert manager.get_messages("sess1") == []


def test_get_messages_pagination(storage):
    manager = ConversationManager(storage)
    manager.create_conversation("sess1", "seller1")
    for i in range(5):
        manager.add_message("sess1", "user", f"message {i}")

    page = manager.get_messages("sess1", offset=1, limit=2)
    assert [m.content for m in page] == ["message 1", "message 2"]

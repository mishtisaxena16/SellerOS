"""
conversation.py

Conversation Memory Manager.

Responsible for the operations you perform *during* a live session:
starting one, appending messages to it, reading it back, clearing or
deleting it.

This module does NOT know anything about Agents, Tools, LangGraph,
Connectors, or LLMs. It only manages conversation history.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .base import BaseMemoryStore
from .exceptions import MemoryNotFoundError
from .models import ChatMessage, ConversationMemory


class ConversationManager:
    """Handles all conversation-lifecycle operations."""

    def __init__(self, storage: BaseMemoryStore) -> None:
        self.storage = storage

    # --------------------------------------------------
    # Create Conversation
    # --------------------------------------------------

    def create_conversation(
        self,
        session_id: str,
        seller_id: str,
        marketplace: str | None = None,
    ) -> ConversationMemory:
        """Start a brand-new, empty conversation session."""

        conversation = ConversationMemory(
            session_id=session_id,
            seller_id=seller_id,
            marketplace=marketplace,
        )

        self.storage.save_conversation(conversation)

        return conversation

    # --------------------------------------------------
    # Load Conversation
    # --------------------------------------------------

    def get_conversation(self, session_id: str) -> ConversationMemory | None:
        """Return the full conversation, or `None` if it doesn't exist."""
        return self.storage.load_conversation(session_id)

    # --------------------------------------------------
    # Add User / Assistant Message
    # --------------------------------------------------

    def add_message(self, session_id: str, role: str, content: str) -> ChatMessage:
        """
        Append a message to an existing conversation.

        Raises
        ------
        MemoryNotFoundError
            If no conversation exists for `session_id`. Previously this
            raised a bare `ValueError`, which is indistinguishable from
            a programming error; callers that want to auto-create a
            session on first message can now specifically catch
            `MemoryNotFoundError` and call `create_conversation` first.
        """

        conversation = self.storage.load_conversation(session_id)

        if conversation is None:
            raise MemoryNotFoundError(f"No conversation for session_id={session_id!r}")

        message = ChatMessage(role=role, content=content)

        conversation.messages.append(message)
        conversation.updated_at = datetime.now(timezone.utc)

        self.storage.update_conversation(conversation)

        return message

    # --------------------------------------------------
    # Return Chat History
    # --------------------------------------------------

    def get_messages(
        self,
        session_id: str,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[ChatMessage]:
        """
        Return a page of messages for a conversation.

        Delegates to `BaseMemoryStore.load_messages` rather than
        loading the full conversation and slicing in Python, so a real
        backend (Postgres/Redis) can push the offset/limit down into
        the query instead of pulling an entire year of chat history
        into memory to return the last five messages.
        """
        return self.storage.load_messages(session_id, offset=offset, limit=limit)

    # --------------------------------------------------
    # Clear Conversation
    # --------------------------------------------------

    def clear_conversation(self, session_id: str) -> None:
        """Remove all messages from a conversation but keep the session."""

        conversation = self.storage.load_conversation(session_id)

        if conversation is None:
            return

        conversation.messages.clear()
        conversation.updated_at = datetime.now(timezone.utc)

        self.storage.update_conversation(conversation)

    # --------------------------------------------------
    # Delete Conversation
    # --------------------------------------------------

    def delete_conversation(self, session_id: str) -> None:
        """Delete a conversation entirely."""
        self.storage.delete_conversation(session_id)

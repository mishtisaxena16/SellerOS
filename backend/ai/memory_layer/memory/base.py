"""
base.py

Abstract interface for the SellerOS Memory Layer's storage backends.

This file defines the contract that every memory backend must
implement:

- InMemoryStorage  (this package, default/dev backend)
- RedisStorage     (future)
- PostgreSQLStorage (future)
- MongoStorage      (future)

The rest of SellerOS never talks directly to Redis or PostgreSQL.
Instead, it depends only on this abstraction, so storage backends can
be swapped without changing MemoryManager, Agents, or the
Orchestrator.

Import style
------------
This module (and every other module in `memory/`) uses *relative*
imports (`.models`) rather than absolute ones (`memory.models`).
Absolute imports only resolve correctly if `backend/` happens to be on
`sys.path` as a package root, which is not guaranteed once this layer
is imported from a sibling package (e.g. the Orchestrator importing
`backend.memory.manager`). Relative imports are invariant to where the
package is mounted, which matters given the stated goal that the
Memory Layer must be independently importable from anywhere in the
system.

Pagination
----------
`load_conversation` returns the *entire* conversation, including every
message. For a seller with a long history that does not scale — it is
fine for building context (small window) but wrong for, e.g., an
admin UI that wants to page through a year of chat history. For that
reason, message retrieval also has a dedicated paginated method,
`load_messages`, which backends should implement efficiently (e.g. a
real `LIMIT/OFFSET` SQL query) rather than loading everything and
slicing in Python.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    BusinessMemory,
    ChatMessage,
    ConversationMemory,
    SellerMemory,
)


class BaseMemoryStore(ABC):
    """Base interface for all SellerOS memory storage backends."""

    # ==========================================================
    # Conversation Memory
    # ==========================================================

    @abstractmethod
    def save_conversation(self, conversation: ConversationMemory) -> None:
        """Persist a brand-new conversation."""

    @abstractmethod
    def load_conversation(self, session_id: str) -> ConversationMemory | None:
        """Load a full conversation (including all messages) by session ID."""

    @abstractmethod
    def update_conversation(self, conversation: ConversationMemory) -> None:
        """Persist changes to an existing conversation."""

    @abstractmethod
    def delete_conversation(self, session_id: str) -> None:
        """Delete a conversation. No-op if it does not exist."""

    @abstractmethod
    def load_messages(
        self,
        session_id: str,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[ChatMessage]:
        """
        Load a page of messages for a conversation without necessarily
        materializing the whole conversation object.

        Parameters
        ----------
        session_id:
            The conversation to read from.
        offset:
            Number of messages (oldest-first) to skip.
        limit:
            Maximum number of messages to return. `None` means "to the end".

        Returns
        -------
        list[ChatMessage]
            An empty list if the conversation does not exist.
        """

    # ==========================================================
    # Seller Memory
    # ==========================================================

    @abstractmethod
    def save_seller(self, seller: SellerMemory) -> None:
        """Persist a brand-new seller profile."""

    @abstractmethod
    def load_seller(self, seller_id: str) -> SellerMemory | None:
        """Load a seller profile by ID."""

    @abstractmethod
    def update_seller(self, seller: SellerMemory) -> None:
        """Persist changes to an existing seller profile."""

    @abstractmethod
    def delete_seller(self, seller_id: str) -> None:
        """Delete a seller profile. No-op if it does not exist."""

    # ==========================================================
    # Business Memory
    # ==========================================================

    @abstractmethod
    def save_business(self, business: BusinessMemory) -> None:
        """Persist brand-new business memory."""

    @abstractmethod
    def load_business(self, seller_id: str) -> BusinessMemory | None:
        """Load business memory by seller ID."""

    @abstractmethod
    def update_business(self, business: BusinessMemory) -> None:
        """Persist changes to existing business memory."""

    @abstractmethod
    def delete_business(self, seller_id: str) -> None:
        """Delete business memory. No-op if it does not exist."""

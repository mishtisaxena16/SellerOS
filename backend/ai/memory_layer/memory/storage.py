"""
storage.py

Default in-memory storage backend for SellerOS.

Purpose
-------
This is only the storage engine. It contains no business logic - it
simply stores and retrieves memory objects keyed by ID. Later, this
file can be replaced by RedisStorage, PostgreSQLStorage, or
MongoStorage without changing MemoryManager, Agents, or the
Orchestrator, because all of them depend on `BaseMemoryStore`, not on
this class.

Defensive copying
------------------
`load_*` methods return a *deep copy* of the stored object rather than
the object living in `self._conversations` / `self._sellers` /
`self._businesses`. Returning the live reference would let callers
mutate memory state directly (e.g. `conversation.messages.append(...)`)
without going through `update_conversation`, silently bypassing
`updated_at` bookkeeping and any future hooks (audit logging, cache
invalidation, event publishing) attached to the update path. The cost
is one deep copy per read; for an in-memory dev backend this is
negligible, and a real database-backed store gets this property for
free since it deserializes a fresh object on every read anyway.

Lifetime
--------
Data exists only while the process is running. Restarting the process
clears all memory - this is a development/testing backend, not a
production one.
"""

from __future__ import annotations

from .base import BaseMemoryStore
from .models import (
    BusinessMemory,
    ChatMessage,
    ConversationMemory,
    SellerMemory,
)


class InMemoryStorage(BaseMemoryStore):
    """Temporary storage backend using Python dictionaries."""

    def __init__(self) -> None:
        self._conversations: dict[str, ConversationMemory] = {}
        self._sellers: dict[str, SellerMemory] = {}
        self._businesses: dict[str, BusinessMemory] = {}

    # ======================================================
    # Conversation Memory
    # ======================================================

    def save_conversation(self, conversation: ConversationMemory) -> None:
        self._conversations[conversation.session_id] = conversation.model_copy(deep=True)

    def load_conversation(self, session_id: str) -> ConversationMemory | None:
        conversation = self._conversations.get(session_id)
        return conversation.model_copy(deep=True) if conversation else None

    def update_conversation(self, conversation: ConversationMemory) -> None:
        self._conversations[conversation.session_id] = conversation.model_copy(deep=True)

    def delete_conversation(self, session_id: str) -> None:
        self._conversations.pop(session_id, None)

    def load_messages(
        self,
        session_id: str,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[ChatMessage]:
        conversation = self._conversations.get(session_id)

        if conversation is None:
            return []

        messages = conversation.messages[offset:]

        if limit is not None:
            messages = messages[:limit]

        return [message.model_copy(deep=True) for message in messages]

    # ======================================================
    # Seller Memory
    # ======================================================

    def save_seller(self, seller: SellerMemory) -> None:
        self._sellers[seller.seller_id] = seller.model_copy(deep=True)

    def load_seller(self, seller_id: str) -> SellerMemory | None:
        seller = self._sellers.get(seller_id)
        return seller.model_copy(deep=True) if seller else None

    def update_seller(self, seller: SellerMemory) -> None:
        self._sellers[seller.seller_id] = seller.model_copy(deep=True)

    def delete_seller(self, seller_id: str) -> None:
        self._sellers.pop(seller_id, None)

    # ======================================================
    # Business Memory
    # ======================================================

    def save_business(self, business: BusinessMemory) -> None:
        self._businesses[business.seller_id] = business.model_copy(deep=True)

    def load_business(self, seller_id: str) -> BusinessMemory | None:
        business = self._businesses.get(seller_id)
        return business.model_copy(deep=True) if business else None

    def update_business(self, business: BusinessMemory) -> None:
        self._businesses[business.seller_id] = business.model_copy(deep=True)

    def delete_business(self, seller_id: str) -> None:
        self._businesses.pop(seller_id, None)

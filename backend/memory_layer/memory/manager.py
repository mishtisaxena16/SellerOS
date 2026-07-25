"""
manager.py

SellerOS Memory Manager - the low-level public interface to the
Memory Layer's CRUD operations.

Nothing outside the Memory Layer should directly access a storage
backend. Everything goes through `MemoryManager` (for raw CRUD) or
`MemoryService` (for the higher-level, composed operations - see
`service.py`).

    Agent / Orchestrator
           |
           v
     MemoryService  (composition: context, search, summarization...)
           |
           v
     MemoryManager  (this file: raw CRUD)
           |
           v
     BaseMemoryStore
           |
           v
     InMemoryStorage / RedisStorage / PostgreSQLStorage

Changing the storage backend never affects Agents or the Orchestrator,
because both `MemoryManager` and everything above it depend on the
`BaseMemoryStore` abstraction, never on a concrete backend class.
"""

from __future__ import annotations

from .base import BaseMemoryStore
from .exceptions import MemoryNotFoundError
from .models import BusinessMemory, ConversationMemory, SellerMemory


class MemoryManager:
    """
    High-level interface for raw SellerOS memory CRUD.

    Deliberately thin: it does not know whether data lives in RAM,
    Redis, or PostgreSQL, and it does not compose multiple memory
    types together (that is `MemoryService`'s job).
    """

    def __init__(self, storage: BaseMemoryStore) -> None:
        self.storage = storage

    # =====================================================
    # Seller Memory
    # =====================================================

    def save_seller(self, seller: SellerMemory) -> None:
        """Persist a brand-new seller profile."""
        self.storage.save_seller(seller)

    def get_seller(self, seller_id: str) -> SellerMemory | None:
        """Return the seller profile, or `None` if it doesn't exist."""
        return self.storage.load_seller(seller_id)

    def require_seller(self, seller_id: str) -> SellerMemory:
        """Return the seller profile, or raise `MemoryNotFoundError`."""
        seller = self.storage.load_seller(seller_id)
        if seller is None:
            raise MemoryNotFoundError(f"No seller memory for seller_id={seller_id!r}")
        return seller

    def update_seller(self, seller: SellerMemory) -> None:
        """Persist changes to an existing seller profile."""
        self.storage.update_seller(seller)

    def delete_seller(self, seller_id: str) -> None:
        """Delete a seller profile."""
        self.storage.delete_seller(seller_id)

    # =====================================================
    # Business Memory
    # =====================================================

    def save_business(self, business: BusinessMemory) -> None:
        """Persist brand-new business memory."""
        self.storage.save_business(business)

    def get_business(self, seller_id: str) -> BusinessMemory | None:
        """Return business memory, or `None` if it doesn't exist."""
        return self.storage.load_business(seller_id)

    def require_business(self, seller_id: str) -> BusinessMemory:
        """Return business memory, or raise `MemoryNotFoundError`."""
        business = self.storage.load_business(seller_id)
        if business is None:
            raise MemoryNotFoundError(f"No business memory for seller_id={seller_id!r}")
        return business

    def update_business(self, business: BusinessMemory) -> None:
        """Persist changes to existing business memory."""
        self.storage.update_business(business)

    def delete_business(self, seller_id: str) -> None:
        """Delete business memory."""
        self.storage.delete_business(seller_id)

    # =====================================================
    # Conversation Memory
    # =====================================================

    def save_conversation(self, conversation: ConversationMemory) -> None:
        """Persist a brand-new conversation."""
        self.storage.save_conversation(conversation)

    def get_conversation(self, session_id: str) -> ConversationMemory | None:
        """Return the conversation, or `None` if it doesn't exist."""
        return self.storage.load_conversation(session_id)

    def require_conversation(self, session_id: str) -> ConversationMemory:
        """Return the conversation, or raise `MemoryNotFoundError`."""
        conversation = self.storage.load_conversation(session_id)
        if conversation is None:
            raise MemoryNotFoundError(f"No conversation for session_id={session_id!r}")
        return conversation

    def update_conversation(self, conversation: ConversationMemory) -> None:
        """Persist changes to an existing conversation."""
        self.storage.update_conversation(conversation)

    def delete_conversation(self, session_id: str) -> None:
        """Delete a conversation."""
        self.storage.delete_conversation(session_id)

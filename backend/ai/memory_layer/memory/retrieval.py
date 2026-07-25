"""
retrieval.py

SellerOS Memory Retrieval Layer.

Purpose
-------
Provides high-level, business-oriented read operations over the
Memory Layer, instead of forcing callers to know low-level CRUD method
names. Nothing outside the Memory Layer should call `storage.py`
directly - Agents, the Orchestrator, and backend APIs should go
through this module (or `MemoryService`) to read seller, business, and
conversation information.

This module NEVER modifies memory. It is strictly READ ONLY.
"""

from __future__ import annotations

from typing import Optional

from .base import BaseMemoryStore
from .models import BusinessMemory, ChatMessage, ConversationMemory, SellerMemory


class MemoryRetriever:
    """
    High-level retrieval interface for SellerOS Memory.

    Wraps the storage layer and exposes business-oriented retrieval
    methods instead of low-level CRUD methods.
    """

    def __init__(self, storage: BaseMemoryStore) -> None:
        self.storage = storage

    # ==========================================================
    # Seller Memory
    # ==========================================================

    def get_seller(self, seller_id: str) -> Optional[SellerMemory]:
        return self.storage.load_seller(seller_id)

    def get_preferred_marketplace(self, seller_id: str) -> Optional[str]:
        seller = self.get_seller(seller_id)
        return seller.preferred_marketplace if seller else None

    def get_connected_marketplaces(self, seller_id: str) -> list[str]:
        seller = self.get_seller(seller_id)
        return seller.connected_marketplaces if seller else []

    # ==========================================================
    # Business Memory
    # ==========================================================

    def get_business(self, seller_id: str) -> Optional[BusinessMemory]:
        return self.storage.load_business(seller_id)

    def get_business_goals(self, seller_id: str) -> list[str]:
        business = self.get_business(seller_id)
        return business.business_goals if business else []

    def get_brands(self, seller_id: str) -> list[str]:
        business = self.get_business(seller_id)
        return business.brands if business else []

    # ==========================================================
    # Conversation Memory
    # ==========================================================

    def get_conversation(self, session_id: str) -> Optional[ConversationMemory]:
        return self.storage.load_conversation(session_id)

    def get_messages(self, session_id: str) -> list[ChatMessage]:
        """
        Return the full message history for a session.

        For large histories prefer `get_recent_messages`, which uses
        the storage layer's paginated read path instead of loading
        everything.
        """
        return self.storage.load_messages(session_id)

    def get_recent_messages(self, session_id: str, limit: int = 5) -> list[ChatMessage]:
        """
        Return the most recent `limit` messages for a session.

        Implementation note
        --------------------
        This asks the storage backend for messages directly rather
        than loading the entire conversation and slicing the tail in
        Python. For an in-memory dict that distinction is invisible,
        but for a database-backed store it is the difference between
        `ORDER BY timestamp DESC LIMIT 5` and "load a whole year of
        chat history to throw away everything except the last five
        rows" - the latter does not scale to millions of
        conversations.
        """
        all_messages = self.storage.load_messages(session_id)

        if limit >= len(all_messages):
            return all_messages

        return all_messages[-limit:]

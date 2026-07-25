"""
service.py

MemoryService - the single composed entry point to the Memory Layer.

Why this file exists
---------------------
`MemoryManager`, `ConversationManager`, `MemoryRetriever`,
`MemoryContextBuilder`, `MemorySearch`, `ConversationSummarizer`, and
`MemoryUpdater` are each independent and individually testable, but
nothing composed them. Without this file, an Agent that wants "give me
this seller's context" would need to instantiate four different
classes itself and know how to wire them together - which pushes
Memory-internal composition knowledge into the Agent layer, exactly
the coupling the architecture is trying to avoid.

`MemoryService` is the one class the Orchestrator/Agent layer should
depend on. Internally it owns instances of every sub-component; that
composition can change freely (e.g. adding semantic search over a
vector store) without any caller-visible change, as long as the
methods on `MemoryService` keep their signatures.

    Agent / Orchestrator
           |
           v
      MemoryService   <-- this file, the only class other layers import
       /   |   |   \\
      /    |   |    \\
 Manager Retriever Context  Search / Summarizer / Updater
      \\    |   |    /
       \\   |   |   /
        BaseMemoryStore
"""

from __future__ import annotations

from typing import Any

from .base import BaseMemoryStore
from .context import MemoryContextBuilder
from .conversation import ConversationManager
from .manager import MemoryManager
from .models import (
    BusinessMemory,
    ChatMessage,
    ConversationMemory,
    SellerMemory,
)
from .retrieval import MemoryRetriever
from .search import MemorySearch
from .summarizer import ConversationSummarizer
from .updater import MemoryUpdater


class MemoryService:
    """
    Composed facade over the entire Memory Layer.

    Parameters
    ----------
    storage:
        Any `BaseMemoryStore` implementation (`InMemoryStorage` today;
        a Redis- or Postgres-backed store later). Every sub-component
        is constructed against this same instance so they always see
        the same data.
    """

    def __init__(self, storage: BaseMemoryStore) -> None:
        self.storage = storage

        self.manager = MemoryManager(storage)
        self.conversations = ConversationManager(storage)
        self.retriever = MemoryRetriever(storage)
        self.context_builder = MemoryContextBuilder()
        self.search = MemorySearch()
        self.summarizer = ConversationSummarizer()
        self.updater = MemoryUpdater()

    # ==========================================================
    # The primary operation Agents need: build context for a turn
    # ==========================================================

    def get_agent_context(
        self,
        seller_id: str,
        session_id: str | None = None,
        max_messages_per_conversation: int | None = 20,
    ) -> dict[str, Any]:
        """
        Assemble everything an Agent needs to know about a seller (and
        optionally an in-progress conversation) into one context dict.

        Parameters
        ----------
        seller_id:
            Whose seller/business memory to include.
        session_id:
            If given, that conversation's recent history is folded in
            too. Omit this for a "fresh" turn with no active session.
        max_messages_per_conversation:
            Passed through to `MemoryContextBuilder.build` - caps how
            much raw message history is included, preferring the
            conversation's summary for anything older.
        """
        seller = self.retriever.get_seller(seller_id)
        business = self.retriever.get_business(seller_id)

        conversation = (
            self.retriever.get_conversation(session_id) if session_id else None
        )

        return self.context_builder.build(
            seller=seller,
            business=business,
            conversations=[conversation] if conversation else None,
            max_messages_per_conversation=max_messages_per_conversation,
        )

    # ==========================================================
    # Conversation convenience passthroughs
    # ==========================================================

    def start_conversation(
        self,
        session_id: str,
        seller_id: str,
        marketplace: str | None = None,
    ) -> ConversationMemory:
        """Start a new conversation session."""
        return self.conversations.create_conversation(session_id, seller_id, marketplace)

    def record_message(self, session_id: str, role: str, content: str) -> ChatMessage:
        """Append a message to an existing conversation."""
        return self.conversations.add_message(session_id, role, content)

    def summarize_conversation(self, session_id: str, max_messages: int = 10) -> str:
        """
        Generate (but not persist) a summary of a conversation's most
        recent messages. Call `persist_conversation_summary` to save it.
        """
        messages = self.conversations.get_messages(session_id)
        return self.summarizer.summarize(messages, max_messages=max_messages)

    def persist_conversation_summary(self, session_id: str, max_messages: int = 10) -> str:
        """Generate a summary and store it on the conversation record."""
        conversation = self.manager.require_conversation(session_id)
        summary = self.summarizer.summarize(conversation.messages, max_messages=max_messages)
        conversation.summary = summary
        self.manager.update_conversation(conversation)
        return summary

    # ==========================================================
    # Seller / business preference updates (merge, don't overwrite)
    # ==========================================================

    def upsert_seller(self, seller: SellerMemory) -> SellerMemory:
        """
        Create the seller profile if it doesn't exist yet, otherwise
        merge the incoming data into the existing profile (never
        silently overwriting good values with None - see `updater.py`).
        """
        existing = self.retriever.get_seller(seller.seller_id)

        if existing is None:
            self.manager.save_seller(seller)
            return seller

        merged = self.updater.update_seller_memory(existing, seller)
        self.manager.update_seller(merged)
        return merged

    def upsert_business(self, business: BusinessMemory) -> BusinessMemory:
        """Create-or-merge business memory (see `upsert_seller` for the
        same reasoning applied to business facts)."""
        existing = self.retriever.get_business(business.seller_id)

        if existing is None:
            self.manager.save_business(business)
            return business

        merged = self.updater.update_business_memory(existing, business)
        self.manager.update_business(merged)
        return merged

    # ==========================================================
    # Search passthrough
    # ==========================================================

    def search_conversation(self, session_id: str, query: str) -> list[ChatMessage]:
        """Rank a conversation's messages by relevance to `query`."""
        messages = self.conversations.get_messages(session_id)
        return self.search.ranked_search(messages, query)

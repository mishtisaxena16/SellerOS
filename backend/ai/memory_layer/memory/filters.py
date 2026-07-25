"""
filters.py

Filtering utilities for the SellerOS Memory Layer.

`search.py` finds candidate content. Filters narrow candidates down
according to structured business rules (role, date range, session,
marketplace) rather than free-text matching.

Every method returns a NEW filtered list; original data is never
modified.
"""

from __future__ import annotations

from datetime import datetime

from .models import ChatMessage, ConversationMemory


class MemoryFilters:
    """Collection of reusable, stateless filtering methods."""

    # ------------------------------------------------------------
    # Message-level filters
    # ------------------------------------------------------------

    @staticmethod
    def by_role(messages: list[ChatMessage], role: str) -> list[ChatMessage]:
        """Keep only messages written by a given role (e.g. "user")."""
        role = role.lower()
        return [msg for msg in messages if msg.role.lower() == role]

    @staticmethod
    def by_keyword(messages: list[ChatMessage], keyword: str) -> list[ChatMessage]:
        """Keep only messages whose content contains `keyword`."""
        keyword = keyword.lower()
        return [msg for msg in messages if keyword in msg.content.lower()]

    @staticmethod
    def by_date_range(
        messages: list[ChatMessage],
        start: datetime,
        end: datetime,
    ) -> list[ChatMessage]:
        """Keep only messages timestamped within `[start, end]`."""
        return [msg for msg in messages if start <= msg.timestamp <= end]

    @staticmethod
    def latest(messages: list[ChatMessage], limit: int = 10) -> list[ChatMessage]:
        """Return the `limit` most recent messages, newest first."""
        ordered = sorted(messages, key=lambda m: m.timestamp, reverse=True)
        return ordered[:limit]

    # ------------------------------------------------------------
    # Conversation-level filters
    # ------------------------------------------------------------

    @staticmethod
    def conversations_by_marketplace(
        conversations: list[ConversationMemory],
        marketplace: str,
    ) -> list[ConversationMemory]:
        """
        Keep only conversations tagged with the given marketplace.

        Fix note
        --------
        The earlier implementation filtered *message text* for the
        marketplace name (`"amazon" in message.content.lower()`),
        which matches on incidental mentions of a word rather than on
        which marketplace the conversation actually belongs to - a
        seller saying "not Amazon, I meant Flipkart" would have
        wrongly matched "Amazon". `ConversationMemory.marketplace`
        already exists as a structured field, so this filters on that
        field directly instead of doing text matching.
        """
        marketplace = marketplace.lower()
        return [
            conversation
            for conversation in conversations
            if (conversation.marketplace or "").lower() == marketplace
        ]

"""
search.py

SellerOS Memory Search Engine.

Responsible for finding relevant messages among already-retrieved
memory objects.

Current implementation: keyword-based search.
Future: embeddings, a vector database, hybrid retrieval (see the
planned `semantic_search.py` / `vector_store.py` / `embedding.py`
modules).
"""

from __future__ import annotations

from .models import ChatMessage


class MemorySearch:
    """Keyword-based search over chat messages."""

    def keyword_search(self, messages: list[ChatMessage], query: str) -> list[ChatMessage]:
        """
        Return every message containing at least one query word.

        Example
        -------
        query="Amazon pricing" matches "How should I price my Amazon
        product?" because it shares the word "amazon".
        """
        query_words = query.lower().split()

        return [
            message
            for message in messages
            if any(word in message.content.lower() for word in query_words)
        ]

    def exact_search(self, messages: list[ChatMessage], text: str) -> list[ChatMessage]:
        """Return every message containing the exact phrase `text`."""
        text = text.lower()
        return [message for message in messages if text in message.content.lower()]

    def ranked_search(self, messages: list[ChatMessage], query: str) -> list[ChatMessage]:
        """
        Return messages ordered by relevance (most matching query
        words first). Messages with zero matches are excluded.
        """
        query_words = query.lower().split()

        scored: list[tuple[int, ChatMessage]] = []

        for message in messages:
            content = message.content.lower()
            score = sum(1 for word in query_words if word in content)

            if score > 0:
                scored.append((score, message))

        scored.sort(key=lambda pair: pair[0], reverse=True)

        return [message for _, message in scored]


# Module-level singleton for convenience call sites that don't need
# per-instance state (this class is stateless, so sharing one instance
# is safe).
search_engine = MemorySearch()

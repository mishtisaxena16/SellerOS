"""Tests for memory.search.MemorySearch."""

from memory.models import ChatMessage
from memory.search import MemorySearch


def test_keyword_search_matches_any_word():
    search = MemorySearch()
    messages = [
        ChatMessage(role="user", content="How should I price my Amazon product?"),
        ChatMessage(role="user", content="Unrelated"),
    ]
    result = search.keyword_search(messages, "Amazon pricing")
    assert len(result) == 1


def test_exact_search_requires_full_phrase():
    search = MemorySearch()
    messages = [
        ChatMessage(role="user", content="optimize my amazon listing"),
        ChatMessage(role="user", content="amazon and listing separately"),
    ]
    result = search.exact_search(messages, "amazon listing")
    assert len(result) == 1


def test_ranked_search_orders_by_match_count():
    search = MemorySearch()
    messages = [
        ChatMessage(role="user", content="amazon"),
        ChatMessage(role="user", content="amazon pricing strategy"),
        ChatMessage(role="user", content="unrelated"),
    ]
    result = search.ranked_search(messages, "amazon pricing strategy")
    assert result[0].content == "amazon pricing strategy"
    assert len(result) == 2

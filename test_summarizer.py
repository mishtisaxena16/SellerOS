"""Tests for memory.summarizer.ConversationSummarizer."""

from memory.models import ChatMessage
from memory.summarizer import ConversationSummarizer


def test_summarize_empty_history():
    summarizer = ConversationSummarizer()
    assert summarizer.summarize([]) == "No previous conversation."


def test_summarize_truncates_long_messages():
    summarizer = ConversationSummarizer()
    long_content = "x" * 200
    messages = [ChatMessage(role="user", content=long_content)]

    summary = summarizer.summarize(messages)

    assert summary.startswith("User: ")
    assert summary.endswith("...")
    assert len(summary) < len(long_content)


def test_summarize_respects_max_messages():
    summarizer = ConversationSummarizer()
    messages = [ChatMessage(role="user", content=f"msg {i}") for i in range(20)]

    summary = summarizer.summarize(messages, max_messages=3)

    assert summary.count("\n") == 2  # 3 lines joined by 2 newlines
    assert "msg 19" in summary
    assert "msg 0" not in summary


def test_conversation_statistics():
    summarizer = ConversationSummarizer()
    messages = [
        ChatMessage(role="user", content="a"),
        ChatMessage(role="assistant", content="b"),
        ChatMessage(role="user", content="c"),
    ]

    stats = summarizer.conversation_statistics(messages)

    assert stats == {"total_messages": 3, "user_messages": 2, "assistant_messages": 1}

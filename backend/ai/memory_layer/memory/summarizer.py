"""
summarizer.py

SellerOS Memory Layer - conversation summarization.

The Context Builder can use these summaries instead of sending every
message to the LLM once a conversation grows long.

Current implementation: deterministic, rule-based summarization.
Future implementation: LLM-based summarization (swap this class out;
callers depend on the method signatures below, not on how the summary
is produced).
"""

from __future__ import annotations

from .models import ChatMessage


class ConversationSummarizer:
    """
    Creates summaries of conversations.

    Intentionally deterministic for now so behavior is testable and
    reproducible. Can be replaced with an LLM-backed implementation
    later without changing any other module in the Memory Layer, since
    callers only rely on `summarize()` returning a `str`.
    """

    def summarize(self, messages: list[ChatMessage], max_messages: int = 10) -> str:
        """
        Build a concise summary using the most recent messages.

        Parameters
        ----------
        messages:
            Full conversation history.
        max_messages:
            Number of most recent messages to include in the summary.

        Returns
        -------
        str
            A newline-separated "Speaker: content" summary, or a
            placeholder string if there is no history yet.
        """

        if not messages:
            return "No previous conversation."

        recent = messages[-max_messages:]

        lines = []
        for message in recent:
            speaker = message.role.capitalize()
            content = message.content.strip()

            if len(content) > 120:
                content = content[:117] + "..."

            lines.append(f"{speaker}: {content}")

        return "\n".join(lines)

    def conversation_statistics(self, messages: list[ChatMessage]) -> dict[str, int]:
        """Return simple, useful metadata about a conversation."""
        return {
            "total_messages": len(messages),
            "user_messages": sum(1 for m in messages if m.role == "user"),
            "assistant_messages": sum(1 for m in messages if m.role == "assistant"),
        }


# Module-level singleton. Safe to share because this class holds no
# per-conversation state.
summarizer = ConversationSummarizer()

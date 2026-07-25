"""
context.py

Memory context builder for SellerOS.

Transforms stored memories into the flat, LLM/Agent-readable context
object that gets attached to a prompt.

Memory Layer responsibility here: collect memories, format them,
return context. It does NOT call agents, call tools, or execute
workflows - assembling a dict is not orchestration.
"""

from __future__ import annotations

from typing import Any

from .models import BusinessMemory, ConversationMemory, SellerMemory


class MemoryContextBuilder:
    """Converts SellerOS memory objects into structured agent context."""

    def build(
        self,
        seller: SellerMemory | None = None,
        business: BusinessMemory | None = None,
        conversations: list[ConversationMemory] | None = None,
        max_messages_per_conversation: int | None = 20,
    ) -> dict[str, Any]:
        """
        Build a context dict from whichever memory objects are
        available.

        Parameters
        ----------
        max_messages_per_conversation:
            Caps how many of each conversation's most recent messages
            are included. Earlier versions flattened *every* message
            from *every* passed-in conversation into the context with
            no limit - fine for a five-message demo session, but a
            seller with months of history would silently blow past the
            LLM's context window. Pass `None` to disable the cap (e.g.
            when the caller has already summarized long conversations
            and only passes in a short one). Prefer `conversation.summary`
            for anything long instead of raising this limit.
        """

        context: dict[str, Any] = {
            "seller": {},
            "business": {},
            "conversation_history": [],
        }

        if seller:
            context["seller"] = {
                "name": seller.seller_name,
                "language": seller.preferred_language,
                "marketplace": seller.preferred_marketplace,
                "currency": seller.preferred_currency,
            }

        if business:
            context["business"] = {
                "business_name": business.business_name,
                "category": business.business_category,
                "gstin": business.gstin,
                "marketplaces": business.marketplaces,
                "goals": business.business_goals,
            }

        if conversations:
            for conversation in conversations:
                messages = conversation.messages

                if max_messages_per_conversation is not None:
                    messages = messages[-max_messages_per_conversation:]

                for message in messages:
                    context["conversation_history"].append(
                        {"role": message.role, "content": message.content}
                    )

                # If the conversation has a summary and we truncated
                # its messages, surface the summary too so older
                # context isn't silently lost.
                if conversation.summary and max_messages_per_conversation is not None:
                    if len(conversation.messages) > max_messages_per_conversation:
                        context["conversation_history"].insert(
                            0,
                            {"role": "system", "content": f"Earlier context: {conversation.summary}"},
                        )

        return context

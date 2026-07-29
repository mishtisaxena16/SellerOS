"""
SellerCoachAgent — first agent in the build order (section 25: "1.
Seller Coach Agent"). Answers a seller's marketplace/policy/GST/
sustainability question using the Knowledge Tool, in plain conversational
language.

Deliberately the simplest of the three agents: its default_plan has
exactly one tool step (retrieve knowledge) and one LLM step (answer
using it). No marketplace mutation, no permissions beyond read.

Honest status: KnowledgeTool itself raises NOT_IMPLEMENTED today (the
retriever isn't wired — see tools/knowledge/knowledge_tool.py). That
means SellerCoachAgent will currently answer using only the Reasoner's
own knowledge, with `retrieved_context["knowledge"]` absent and a
recorded error in state.errors — not fabricated citations. Once the
Knowledge Layer is pushed and KnowledgeTool is wired to a real
retriever, this agent needs zero changes; it already asks for
`context_sections = ["user", "seller", "marketplace", "business", "knowledge", "conversation"]`
and will pick up real results the moment the tool underneath does.
"""
from __future__ import annotations

from typing import Any

from backend.ai.agent_layer.base.agent import BaseAgent
from backend.ai.agent_layer.base.state import AgentState


class SellerCoachAgent(BaseAgent):
    name = "seller_coach_agent"
    description = (
        "Answers a seller's questions about marketplace policies, GST, "
        "compliance, and sustainability best practices using the SellerOS "
        "knowledge base."
    )

    permissions: dict[str, bool] = {
        "can_answer_questions": True,
        "can_modify_listings": False,
        "can_modify_inventory": False,
    }
    allowed_tools: list[str] = ["knowledge"]

    prompt_name = "coach"
    # "business" adds a computed revenue/orders/stock snapshot (see
    # ContextBuilder._build_business_section) so advice is grounded in
    # this seller's actual numbers instead of being generic — the gap
    # flagged in the earlier checkpoint review.
    context_sections = ["user", "seller", "marketplace", "business", "knowledge", "conversation"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "knowledge", "action": "search", "query": None, "top_k": 5},
        {"step": "answer_question"},
    ]

    def override_plan(self, plan: list[dict[str, Any]], user_query: str) -> list[dict[str, Any]]:
        # The knowledge_tool step's `query` is None in the static
        # template because the template can't know the query in
        # advance — fill it in here rather than hardcoding user_query
        # into default_plan (which is a class-level constant shared by
        # every call).
        for step in plan:
            if step.get("tool") == "knowledge" and step.get("query") is None:
                step["query"] = user_query
        return plan

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "answer_question":
            state.add_error(f"SellerCoachAgent has no handler for step {step!r}.")
            return None

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        # Confidence is undetermined without a real scoring mechanism —
        # left as None (see AgentResult docstring on why that's not 0.0)
        # rather than inventing a number the Reasoner never actually gave us.
        return result.text

"""
SustainabilityAgent — Tier 5 (deliberately last in the doc roadmap).
Answers a seller's questions about sustainable packaging, green
logistics, EPR compliance, eco-labels, and plastic waste regulations,
using the Knowledge Tool.

Modeled on SellerCoachAgent, not on the Business Intelligence agents —
worth being explicit about why. Sustainability guidance in this system
is fundamentally advisory: "what does EPR compliance require", "is
this packaging recyclable", "how do I get an eco-label" are knowledge
questions, not data-fetching questions the way sales performance or
inventory levels are. There's a real knowledge base backing this
(knowledge/sustainability/ has six real documents — sustainable
business practices, packaging, green logistics, eco-labels, plastic
waste regulations, recyclable packaging), so — same as SellerCoachAgent
— this agent leans entirely on KnowledgeTool + the Reasoner, no
marketplace tool, no mutation, no permissions beyond read.

Honest status, identical to SellerCoachAgent's own docstring:
KnowledgeTool itself raises NOT_IMPLEMENTED today (the retriever isn't
wired). This agent will currently answer using only the Reasoner's own
knowledge, with `retrieved_context["knowledge"]` absent and a recorded
error in state.errors — not fabricated citations to documents that
were never actually retrieved. Once the Knowledge Layer is wired to a
real retriever, this agent needs zero changes.
"""
from __future__ import annotations

from typing import Any

from ai.agent_layer.base.agent import BaseAgent
from ai.agent_layer.base.state import AgentState


class SustainabilityAgent(BaseAgent):
    name = "sustainability_agent"
    description = (
        "Answers a seller's questions about sustainable packaging, "
        "green logistics, EPR compliance, eco-labels, and plastic "
        "waste regulations using the SellerOS knowledge base."
    )

    permissions: dict[str, bool] = {
        "can_answer_questions": True,
        "can_modify_listings": False,
        "can_modify_inventory": False,
    }
    allowed_tools: list[str] = ["knowledge"]

    prompt_name = "sustainability"
    context_sections = ["user", "seller", "marketplace", "knowledge", "conversation"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "knowledge", "action": "search", "query": None, "top_k": 5},
        {"step": "answer_question"},
    ]

    def override_plan(self, plan: list[dict[str, Any]], user_query: str) -> list[dict[str, Any]]:
        for step in plan:
            if step.get("tool") == "knowledge" and step.get("query") is None:
                step["query"] = user_query
        return plan

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "answer_question":
            state.add_error(f"SustainabilityAgent has no handler for step {step!r}.")
            return None

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        return result.text

"""
CompetitorAgent — Tier 2 (Business Intelligence), fourth of four. In
principle: compares a seller's listings/pricing against competitors on
the same marketplace.

Honest status, the most constrained of the four BI agents: SellerOS
has NO competitor data source at all — no scraping connector, no
competitor-pricing API, nothing in connectors/marketplace_connector.py
or tools/marketplace/ that returns another seller's data. Unlike
ForecastAgent/ProfitabilityAgent (which at least have real revenue
numbers to reason over honestly), there is nothing real to fetch here.

Rather than skip building this agent (leaving a silent gap the
Supervisor's `_UNIMPLEMENTED_INTENTS` set would have to cover instead)
or fabricate a knowledge-tool-backed illusion of competitor insight,
this agent exists, is wired into the registry like the others, and its
prompt (prompts/competitor.md) explicitly instructs the Reasoner to
say plainly that no competitor data source is connected rather than
invent competitor names, prices, or market share. If a real competitor
data source is added later (e.g. a scraping Tool), this agent's plan
and prompt are exactly where that gets wired in — the agent doesn't
need to be rebuilt, just given something real to point at.
"""
from __future__ import annotations

from typing import Any

from agent_layer.base.agent import BaseAgent
from agent_layer.base.state import AgentState


class CompetitorAgent(BaseAgent):
    name = "competitor_agent"
    description = (
        "Would compare a seller's listings/pricing against competitors. "
        "No competitor data source is connected yet — currently reports "
        "that plainly instead of inventing a comparison."
    )

    permissions: dict[str, bool] = {
        "can_read_listings": True,
        "can_modify_listings": False,
    }
    allowed_tools: list[str] = ["knowledge"]

    prompt_name = "competitor"
    context_sections = ["user", "seller", "marketplace", "knowledge"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "knowledge", "action": "search", "query": None, "top_k": 5},
        {"step": "competitor_analysis"},
    ]

    def override_plan(self, plan: list[dict[str, Any]], user_query: str) -> list[dict[str, Any]]:
        for step in plan:
            if step.get("tool") == "knowledge" and step.get("query") is None:
                step["query"] = user_query
        return plan

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "competitor_analysis":
            state.add_error(f"CompetitorAgent has no handler for step {step!r}.")
            return None

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        return result.text

"""Domain self-registration for business_intelligence — see
agent_layer/registry/agent_registry.py.

Tier 2 complete: AnalyticsAgent, ForecastAgent, ProfitabilityAgent,
CompetitorAgent. Built to the same standard as Tier 1 (Seller Coach /
Operations / Product Studio) — real tool wiring where a real tool
exists (AnalyticsTool), explicit honesty in the agent/prompt where the
underlying data genuinely doesn't exist yet (ForecastAgent has no
statistical model, ProfitabilityAgent has no cost data, CompetitorAgent
has no competitor data source at all). See each agent's module
docstring for specifics.
"""
from __future__ import annotations

from ai.agent_layer.registry.agent_registry import AgentRegistry
from ai.agent_layer.business_intelligence.analytics_agent import AnalyticsAgent
from ai.agent_layer.business_intelligence.forecast_agent import ForecastAgent
from ai.agent_layer.business_intelligence.profitability_agent import ProfitabilityAgent
from ai.agent_layer.business_intelligence.competitor_agent import CompetitorAgent


def register(registry: AgentRegistry, reasoner) -> None:
    registry.register("analytics", AnalyticsAgent(reasoner), domain="business_intelligence")
    registry.register("forecast", ForecastAgent(reasoner), domain="business_intelligence")
    registry.register("profitability", ProfitabilityAgent(reasoner), domain="business_intelligence")
    registry.register("competitor", CompetitorAgent(reasoner), domain="business_intelligence")

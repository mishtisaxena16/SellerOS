"""Domain self-registration for sustainability — see
agent_layer/registry/agent_registry.py.

Tier 5 complete: SustainabilityAgent. Modeled on SellerCoachAgent
(knowledge-driven advisory, no marketplace mutation) rather than the
Business Intelligence agents — see sustainability_agent.py's module
docstring for why.
"""
from __future__ import annotations

from backend.ai.agent_layer.registry.agent_registry import AgentRegistry
from backend.ai.agent_layer.sustainability.sustainability_agent import SustainabilityAgent


def register(registry: AgentRegistry, reasoner) -> None:
    registry.register("sustainability", SustainabilityAgent(reasoner), domain="sustainability")

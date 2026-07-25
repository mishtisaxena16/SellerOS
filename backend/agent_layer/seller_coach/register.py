"""Domain self-registration for seller_coach — see agent_layer/registry/agent_registry.py."""
from __future__ import annotations

from agent_layer.registry.agent_registry import AgentRegistry
from agent_layer.seller_coach.coach_agent import SellerCoachAgent


def register(registry: AgentRegistry, reasoner) -> None:
    registry.register("seller_coach", SellerCoachAgent(reasoner), domain="seller_coach")

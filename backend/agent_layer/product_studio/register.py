"""Domain self-registration for product_studio — see agent_layer/registry/agent_registry.py."""
from __future__ import annotations

from agent_layer.registry.agent_registry import AgentRegistry
from agent_layer.product_studio.listing_agent import ListingAgent
from agent_layer.product_studio.pricing_agent import PricingAgent


def register(registry: AgentRegistry, reasoner) -> None:
    registry.register("listing", ListingAgent(reasoner), domain="product_studio")
    registry.register("pricing", PricingAgent(reasoner), domain="product_studio")

"""Domain self-registration for operations — see agent_layer/registry/agent_registry.py."""
from __future__ import annotations

from agent_layer.registry.agent_registry import AgentRegistry
from agent_layer.operations.inventory_agent import InventoryAgent
from agent_layer.operations.orders_agent import OrdersAgent


def register(registry: AgentRegistry, reasoner) -> None:
    registry.register("inventory", InventoryAgent(reasoner), domain="operations")
    registry.register("orders", OrdersAgent(reasoner), domain="operations")

    # Tier 4 (doc roadmap): ReturnsAgent, ShippingAgent, ComplianceAgent
    # land here later — one more `registry.register(...)` line each,
    # nothing else in this file or its callers changes.

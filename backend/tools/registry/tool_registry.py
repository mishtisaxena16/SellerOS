"""
ToolRegistry — central lookup so agents do

    tool_registry.get("listing")

instead of importing and instantiating ListingTool directly in every
agent file. One registry instance is meant to be created at app
startup and shared.

Kept deliberately dumb: no dependency injection framework, no lazy
loading, no plugin discovery. Register explicitly in
build_default_registry() below. If that function gets unwieldy once
there are 20+ tools, that's the signal to add auto-discovery — not a
reason to add it preemptively now.
"""
from __future__ import annotations

from tools.base.base_tool import BaseTool


class ToolNotFoundError(KeyError):
    """Raised when tool_registry.get(name) is called for an unregistered tool."""


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, key: str, tool: BaseTool) -> None:
        if key in self._tools:
            raise ValueError(
                f"Tool '{key}' is already registered "
                f"(existing: {type(self._tools[key]).__name__}). "
                f"Use a different key or remove the duplicate registration."
            )
        self._tools[key] = tool

    def get(self, key: str) -> BaseTool:
        try:
            return self._tools[key]
        except KeyError:
            available = ", ".join(sorted(self._tools)) or "(none registered)"
            raise ToolNotFoundError(
                f"No tool registered under '{key}'. Available: {available}"
            ) from None

    def list_tools(self) -> list[str]:
        return sorted(self._tools)

    def describe(self) -> dict[str, str]:
        """Name -> description, useful for building an LLM tool-selection prompt."""
        return {key: tool.description for key, tool in self._tools.items()}


def build_default_registry() -> ToolRegistry:
    """
    Wires up every tool that currently exists. Called once at app
    startup (e.g. in the FastAPI lifespan handler); the returned
    registry is then shared across requests.
    """
    from tools.knowledge.knowledge_tool import KnowledgeTool
    from tools.marketplace.listing_tool import ListingTool
    from tools.marketplace.inventory_tool import InventoryTool
    from tools.marketplace.orders_tool import OrdersTool
    from tools.marketplace.analytics_tool import AnalyticsTool
    from tools.marketplace.ads_tool import AdsTool
    from tools.marketplace.account_tool import AccountTool

    registry = ToolRegistry()
    registry.register("knowledge", KnowledgeTool())
    registry.register("listing", ListingTool())
    registry.register("inventory", InventoryTool())
    registry.register("orders", OrdersTool())
    registry.register("analytics", AnalyticsTool())
    registry.register("ads", AdsTool())
    registry.register("account", AccountTool())
    return registry

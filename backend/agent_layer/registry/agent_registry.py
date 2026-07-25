"""
AgentRegistry — same pattern as the Tool Registry
(tools/registry/tool_registry.py), one layer up:

    registry.get("listing_agent")

The Executive Agent should use this registry instead of importing
specialized agents directly (section 20/24) — same rationale as
ToolManager one layer down: routing through a registry means the
Executive Agent's "which agent handles this" logic never needs an
import list that grows/changes every time a new specialized agent is
added.

Deliberately dumb, same as ToolRegistry: no dependency injection
framework, no auto-discovery. Register explicitly in
build_default_registry() below.
"""
from __future__ import annotations

from typing import Optional

from agent_layer.base.agent import BaseAgent


class AgentNotFoundError(KeyError):
    """Raised when agent_registry.get(name) is called for an unregistered agent."""


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self._domains: dict[str, str] = {}  # agent key -> domain name

    def register(self, key: str, agent: BaseAgent, domain: str = "unassigned") -> None:
        if key in self._agents:
            raise ValueError(
                f"Agent '{key}' is already registered "
                f"(existing: {type(self._agents[key]).__name__}). "
                f"Use a different key or remove the duplicate registration."
            )
        self._agents[key] = agent
        self._domains[key] = domain

    def get(self, key: str) -> BaseAgent:
        try:
            return self._agents[key]
        except KeyError:
            available = ", ".join(sorted(self._agents)) or "(none registered)"
            raise AgentNotFoundError(
                f"No agent registered under '{key}'. Available: {available}"
            ) from None

    def list_agents(self) -> list[str]:
        return sorted(self._agents)

    def domain_of(self, key: str) -> Optional[str]:
        """Which domain package registered this agent key — e.g.
        `domain_of("pricing") == "product_studio"`. Purely for
        introspection/observability (Supervisor responses, logging,
        the routing story in AGENT_SDK.md); `get(key)` never needs it."""
        return self._domains.get(key)

    def keys_in_domain(self, domain: str) -> list[str]:
        return sorted(key for key, d in self._domains.items() if d == domain)

    def describe(self) -> dict[str, str]:
        """Name -> description, useful for the Supervisor's own
        intent -> agent selection prompt once that's LLM-driven."""
        return {key: agent.description for key, agent in self._agents.items()}


# Every domain package under agent_layer/ that owns agents. Each module
# listed here exposes `register(registry, reasoner) -> None` (see e.g.
# agent_layer/operations/register.py). Adding a new domain means adding
# one entry here — NOT teaching this file about the domain's individual
# agents; that knowledge lives in the domain's own register.py.
_DOMAIN_MODULES = (
    "agent_layer.seller_coach.register",
    "agent_layer.product_studio.register",
    "agent_layer.operations.register",
    "agent_layer.business_intelligence.register",
    "agent_layer.marketing.register",
    "agent_layer.sustainability.register",
)


def build_default_registry(reasoner) -> AgentRegistry:
    """
    Wires up every specialized agent that currently exists, by asking
    each domain package to register itself (Intent -> Domain ->
    Registry -> Agent — see agent_layer/AGENT_SDK.md).

    `reasoner` is a single shared LLMReasoner (e.g. OllamaReasoner) —
    safe to reuse across every agent instance and every seller's
    requests, unlike ToolManager, which is scoped per-seller/session
    and therefore passed into `agent.run(tool_manager, ...)` at call
    time instead, not injected here (see agent_layer/base/agent.py's
    constructor docstring for why).

    This function itself never imports a concrete agent class or calls
    `registry.register(...)` directly anymore — that would mean every
    new agent requires editing this shared file, exactly the coupling
    domain self-registration exists to avoid. It only knows the list of
    domain modules; each one owns its own agents.
    """
    import importlib

    registry = AgentRegistry()
    for module_path in _DOMAIN_MODULES:
        domain_module = importlib.import_module(module_path)
        domain_module.register(registry, reasoner)
    return registry

"""
agent_planner.py — Phase 6.1, Tasks 2 & 3: which agents does a query need,
and in what order.

    User query -> AgentPlanner.build_plan(query) -> ExecutionPlan

Nothing in here executes an agent. `AgentPlanner` only ever reads
`RoutingRule.keywords` against the query text and returns an
`ExecutionPlan` (see models.py) describing which agents *would* run.

Deliberately simple keyword routing today (same style as
`orchestrator.IntentRouter`/`INTENT_KEYWORDS`, kept independent from it
on purpose — see module note below). `_ROUTING_RULES` is a plain list of
small `RoutingRule` objects specifically so routing can grow later
(more rules, smarter matching, eventually an LLM-driven classifier)
without changing `AgentPlanner`'s public interface or anything that
calls `build_plan()`.

WHY NOT REUSE `orchestrator.INTENT_KEYWORDS`?
Reusing it would couple this new, purely-descriptive planning layer to
the execution-facing Orchestrator's intent table — a change made for
routing reasons in Phase 6.1 could silently alter Phase 1-5 execution
behavior, and vice versa. Phase 6.1 is explicitly scoped to add a
planning layer only, not touch existing routing/execution
(orchestrator.py, supervisor.py's TaskDecomposer). Keeping this table
separate keeps that boundary real, not just documented.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from backend.ai.planner_layer.models import ExecutionPlan, ExecutionStep

# ---------------------------------------------------------------------------
# Agent catalog: agent_id -> display_name
#
# agent_id matches the real agent_registry.py key where one already
# exists (analytics, inventory, pricing, listing, ads, seller_coach), so
# this plan is ready to line up with real agent execution in a later
# phase. "policy" has no registered agent yet (Product Studio only ships
# ListingAgent/PricingAgent today) — included anyway because Task 2's
# routing rules call for it; a future phase either registers a real
# PolicyAgent under this key or removes the step, and nothing here needs
# to change either way.
# ---------------------------------------------------------------------------
AGENT_CATALOG: Dict[str, str] = {
    "analytics": "Analytics Agent",
    "inventory": "Inventory Agent",
    "pricing": "Pricing Agent",
    "marketing": "Marketing Agent",
    "listing": "Listing Agent",
    "policy": "Policy Agent",
    "seller_coach": "Seller Coach",
}

# Seller Coach is never selected by a rule directly — it is appended to
# every plan by build_plan() and always ordered last (Task 3).
_SELLER_COACH = "seller_coach"


@dataclass(frozen=True)
class RoutingRule:
    name: str
    keywords: Tuple[str, ...]
    agent_ids: Tuple[str, ...]  # in priority order, Seller Coach excluded
    reason: str


# ---------------------------------------------------------------------------
# Task 2's example routing table, as data. Add a new RoutingRule here to
# add a new category — nothing else in this file needs to change.
# ---------------------------------------------------------------------------
_ROUTING_RULES: Tuple[RoutingRule, ...] = (
    RoutingRule(
        name="sales",
        keywords=("sales", "revenue", "sold", "earnings", "income dropped", "profit"),
        agent_ids=("analytics", "pricing"),
        reason="Query mentions sales/revenue performance",
    ),
    RoutingRule(
        name="inventory",
        keywords=("inventory", "stock", "restock", "out of stock", "stockout"),
        agent_ids=("inventory",),
        reason="Query mentions inventory/stock levels",
    ),
    RoutingRule(
        name="ads",
        keywords=("ad ", "ads", "advertising", "campaign", "ppc", "sponsored listing", "ad spend"),
        agent_ids=("marketing", "analytics"),
        reason="Query mentions ads/advertising performance",
    ),
    RoutingRule(
        name="listing",
        keywords=("listing", "product page", "product title", "description", "catalog"),
        agent_ids=("listing", "policy"),
        reason="Query mentions a product listing",
    ),
)


class AgentPlanner:
    """Determines which agents are required for a query and builds the
    ExecutionPlan for it (Task 2 + Task 3).

    Kept as a plain class with no constructor dependencies on purpose —
    it doesn't need a reasoner, a tool registry, or a seller_id, because
    it never calls an agent. That keeps it trivially reusable from the
    Supervisor layer, a future Executor, or a standalone script/test.
    """

    def __init__(self, rules: Tuple[RoutingRule, ...] = _ROUTING_RULES) -> None:
        self._rules = rules

    def matching_rules(self, query: str) -> List[RoutingRule]:
        q = query.lower()
        return [rule for rule in self._rules if any(keyword in q for keyword in rule.keywords)]

    def build_plan(self, query: str) -> ExecutionPlan:
        """Build the ExecutionPlan for `query`.

        Every matching rule's agents are unioned together (first-match
        order preserved, duplicates dropped) so a query that legitimately
        touches more than one category (e.g. "sales dropped, and is
        anything out of stock?") gets every relevant agent rather than
        only the first rule that matched. A query matching nothing falls
        back to "general questions -> Seller Coach only" (Task 2).
        Seller Coach is then appended exactly once and always ordered
        last (Task 3), whether or not a rule already asked for it.
        """
        rules = self.matching_rules(query)

        ordered_agent_ids: List[str] = []
        reasons: Dict[str, str] = {}
        for rule in rules:
            for agent_id in rule.agent_ids:
                if agent_id not in ordered_agent_ids:
                    ordered_agent_ids.append(agent_id)
                    reasons[agent_id] = rule.reason

        if not ordered_agent_ids:
            # General question -> Seller Coach only.
            reasons[_SELLER_COACH] = "General question; no specialized agent matched"
        else:
            reasons.setdefault(
                _SELLER_COACH,
                "Seller Coach always summarizes and advises after specialist agents",
            )
        # Seller Coach is appended once, last, regardless of whether a
        # rule already referenced it (none currently do, but this keeps
        # the guarantee true even if a future rule adds it explicitly).
        if _SELLER_COACH in ordered_agent_ids:
            ordered_agent_ids.remove(_SELLER_COACH)
        ordered_agent_ids.append(_SELLER_COACH)

        steps = self._assign_execution_order(ordered_agent_ids, reasons)
        return ExecutionPlan(steps=steps)

    def _assign_execution_order(
        self, agent_ids: List[str], reasons: Dict[str, str]
    ) -> List[ExecutionStep]:
        """1-based execution_order in list order. Seller Coach is
        guaranteed to already be last in `agent_ids` by build_plan(), so
        it always receives the highest execution_order here too."""
        steps: List[ExecutionStep] = []
        for order, agent_id in enumerate(agent_ids, start=1):
            steps.append(
                ExecutionStep(
                    agent_id=agent_id,
                    display_name=AGENT_CATALOG.get(agent_id, agent_id.replace("_", " ").title()),
                    reason=reasons.get(agent_id, "Included by planner"),
                    execution_order=order,
                )
            )
        return steps


# Module-level singleton, same pattern as agent_registry/guardrail_engine/
# supervisor: one shared, stateless instance rather than rebuilt per request.
agent_planner = AgentPlanner()

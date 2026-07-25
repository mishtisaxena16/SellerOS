"""
Planner — creates an execution plan, never runs it (section 16).

    Planner does not execute.

Honest status: there is no LLM-driven dynamic planning yet (that would
mean prompting a model to decompose `user_query` into steps, which
needs the Reasoner/PromptBuilder wired to a real model call — see
reasoning.py for why that's a stub too). What exists today is a
static/rule-based planner: each specialized agent declares its own
default plan as an ordered list of step dicts, and Planner's job is
just to hand that back — optionally letting an agent override specific
steps based on the query (e.g. skip a "fetch_product" step if the
caller already supplied product data).

This keeps the Planner/Executor separation the doc asks for (section 16
+ 17) real from day one, even though the *planning* itself isn't
smart yet. When LLM-driven planning lands, it's a change inside
Planner.create_plan() only — Executor and every agent calling it stay
the same, because they only ever see `list[dict]` steps in, regardless
of how that list was produced.
"""
from __future__ import annotations

from typing import Any, Callable, Optional


class Planner:
    def create_plan(
        self,
        default_plan: list[dict[str, Any]],
        user_query: str,
        overrides: Optional[Callable[[list[dict[str, Any]], str], list[dict[str, Any]]]] = None,
    ) -> list[dict[str, Any]]:
        """
        `default_plan` is the specialized agent's static plan template,
        e.g.:

            [
              {"tool": "listing", "action": "get_listings"},
              {"tool": "knowledge", "action": "search"},
              {"step": "generate_listing"},
              {"step": "quality_check"},
            ]

        `overrides`, if given, is a per-agent hook to adjust that
        template for the specific query (still rule-based, not an LLM
        call) — e.g. drop a step, or fill in a parameter the agent
        already knows. Left as a plain callable rather than a subclass
        hierarchy so a specialized agent can pass a small lambda/closure
        instead of needing a whole PlannerSubclass per agent.
        """
        plan = [dict(step) for step in default_plan]  # shallow copy, don't mutate the template
        if overrides is not None:
            plan = overrides(plan, user_query)
        return plan

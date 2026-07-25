"""
AgentState — what the handover doc calls "Future LangGraph state"
(section 15). Agents update this as they work rather than directly
assembling a final answer inline, so that once the Orchestrator Layer
lands (LangGraph, built by another team member per section 27), this
object is already shaped like a LangGraph state dict and agents don't
need rewriting to plug into it.

Deliberately a plain dataclass with a dict-of-dicts escape hatch
(`scratch`), not a Pydantic model. Two reasons:

1. `retrieved_context` and `tool_results` hold live SDK objects
   (Product, Order, ...) and ToolResult instances — not JSON-safe
   payloads — for the same reason ToolContext isn't a Pydantic model
   (see tools/base/tool_context.py). Validating them on every mutation
   would add friction, not safety.
2. LangGraph state is conventionally a mutable dict/TypedDict that
   nodes read and write incrementally. A dataclass gets 90% of that
   ergonomics with real attribute access instead of state["key"]
   typos, while `to_dict()`/`from_dict()` below give a clean seam for
   whatever the Orchestrator Layer actually expects once it exists.

`errors` is a list, not a single Optional[str]. A Planner might
produce a plan where step 2 fails but step 3 (independent of step 2)
still succeeds — collapsing that into one error slot would force
picking which failure "wins" and silently drop the other.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentState:
    user_query: str

    # Ordered list of steps the Planner produced, e.g.
    # ["fetch_product", "retrieve_knowledge", "generate_listing", "quality_check"].
    # Plain strings/dicts, not a typed Step class yet — see planner.py
    # for why that's a deliberate "not yet" rather than an oversight.
    plan: list[dict[str, Any]] = field(default_factory=list)

    current_step: int = 0

    # Knowledge Layer / marketplace context assembled by ContextBuilder
    # before each LLM call. Keyed by source ("knowledge", "inventory",
    # "seller", ...) rather than being a flat blob, so PromptBuilder can
    # selectively include sections instead of dumping everything into
    # every prompt regardless of relevance.
    retrieved_context: dict[str, Any] = field(default_factory=dict)

    # Every ToolResult produced so far, in call order. This is the same
    # data AgentResult.tool_calls gets populated from at the end — kept
    # here too because a running agent needs to inspect its own
    # tool_results mid-plan (e.g. "did step 1 succeed before running step 2").
    tool_results: list[Any] = field(default_factory=list)

    # Free-form reasoning trace (chain-of-thought, planner rationale,
    # etc.) an agent or the Reasoner may want to record for
    # debuggability. Not shown to the seller — this is a debugging/audit
    # trail, not part of AgentResult.message.
    intermediate_thoughts: list[str] = field(default_factory=list)

    final_response: Optional[str] = None
    confidence: Optional[float] = None
    errors: list[str] = field(default_factory=list)

    # Escape hatch for agent-specific working data that doesn't deserve
    # a first-class field on a shared state object used by every agent
    # (e.g. ListingAgent's in-progress draft). Prefer a real field once
    # more than one agent needs the same thing — that's the signal it's
    # not actually agent-specific.
    scratch: dict[str, Any] = field(default_factory=dict)

    def record_tool_result(self, result: Any) -> None:
        self.tool_results.append(result)

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def advance(self) -> None:
        self.current_step += 1

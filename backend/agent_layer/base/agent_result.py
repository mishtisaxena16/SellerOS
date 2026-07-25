"""
AgentResult — the standard shape every agent returns to whatever called
it (Executive Agent, LangGraph orchestrator node, or a test harness).

Mirrors the Tool Layer's own ToolResult one level up:

    ToolResult  -> what a Tool returns to an Agent
    AgentResult -> what an Agent returns to the Orchestrator

Same reasoning as ToolResult's `message` vs `error` split applies here
to `citations` vs `metadata`: `citations` is specifically "which
Knowledge Layer chunks / marketplace records back up this answer" —
information the frontend or a guardrail may want to render or check
directly, not just log. Collapsing it into a generic `metadata` bag
would work today but makes "show your sources" a data-mining exercise
later instead of a field read.

Per the handover doc (section 23), the frontend should never care
which agent produced a result — every agent, regardless of what it
does internally, normalizes to this one shape.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentResult:
    success: bool
    message: str = ""

    # 0.0-1.0, how confident the agent is in `message`/`data`. Left as
    # None (not 0.0) when an agent hasn't been wired up to produce a
    # real confidence estimate yet — 0.0 would silently look like "very
    # unconfident" instead of "not measured", which is a different and
    # more misleading claim.
    confidence: Optional[float] = None

    # Structured payload for the caller to use programmatically, e.g. a
    # list of Product/Order SDK models a Tool returned. Optional because
    # some agent results are advice/text only (Seller Coach) and have
    # nothing structured to attach.
    data: Any = None

    # Knowledge Layer chunks or marketplace records that back up
    # `message`. Empty list, not None, when an agent hasn't cited
    # anything yet vs. genuinely has no relevant sources — genuinely
    # empty is itself informative (e.g. "no Knowledge Layer hit").
    citations: list[dict[str, Any]] = field(default_factory=list)

    # Every ToolResult the agent's Executor produced while working the
    # plan, in call order. Kept even for successful ToolResults, not
    # just failures — an orchestrator debugging "why did the agent say
    # X" needs the full trace, not just the final answer.
    tool_calls: list[Any] = field(default_factory=list)

    # Anything the agent produced that isn't plain text/data — e.g. a
    # generated listing draft, an image, a chart. Left as a generic
    # dict list rather than a typed union because the artifact types an
    # agent can produce will grow (Product Studio agents in particular)
    # and shouldn't require touching this shared contract each time.
    artifacts: list[dict[str, Any]] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        message: str = "",
        data: Any = None,
        confidence: Optional[float] = None,
        citations: Optional[list[dict[str, Any]]] = None,
        tool_calls: Optional[list[Any]] = None,
        artifacts: Optional[list[dict[str, Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "AgentResult":
        return cls(
            success=True, message=message, data=data, confidence=confidence,
            citations=citations or [], tool_calls=tool_calls or [],
            artifacts=artifacts or [], metadata=metadata or {},
        )

    @classmethod
    def fail(
        cls,
        message: str,
        tool_calls: Optional[list[Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> "AgentResult":
        return cls(
            success=False, message=message, confidence=0.0,
            tool_calls=tool_calls or [], metadata=metadata or {},
        )

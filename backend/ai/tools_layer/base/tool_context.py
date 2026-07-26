"""
ToolContext — the one object every tool.execute() call receives.

Deliberately a plain dataclass, not a Pydantic model. ToolContext holds
live objects (a memory store, a marketplace session) that get passed
by reference within a single request — it is never serialized over a
network boundary the way ToolResult or the connector-layer response
models are. Pydantic validation would add nothing here and would
force awkward arbitrary_types_allowed config for the memory field.

Blind spot to flag now, not later: `memory` is typed as `Any` because
the Memory Layer (Phase 5) doesn't exist yet. When it does, this
should become `Optional[BaseMemory]` or similar — don't let `Any`
survive past that point, or every tool that reads memory becomes
untyped by association.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

from backend.ai.connectors_layer.marketplace_connector import MarketplaceSession


@dataclass
class ToolContext:
    seller_id: str
    platform: Optional[str] = None
    marketplace_session: Optional[MarketplaceSession] = None

    # Memory Layer (backend/memory_layer/memory/) now exists — this
    # stays `Any` rather than `Optional[BaseMemory]` because what's
    # actually passed through here today is
    # MemoryService.get_agent_context()'s plain dict return value
    # (orchestrator.py's `_get_tool_manager(seller_id, memory=recalled_memory)`),
    # not a MemoryService/BaseMemory instance itself. Worth tightening
    # once a tool actually needs to call back into MemoryService rather
    # than just read the recalled dict.
    memory: Any = None

    user: Optional[str] = None

    request_id: str = field(default_factory=lambda: str(uuid4()))
    trace_id: Optional[str] = None

    def require_session(self) -> MarketplaceSession:
        """
        Marketplace tools call this instead of touching
        self.marketplace_session directly, so "no session attached"
        fails with one clear error instead of an AttributeError
        surfacing three layers down inside a connector call.
        """
        if self.marketplace_session is None:
            raise ValueError(
                f"ToolContext for seller_id={self.seller_id!r} has no "
                f"marketplace_session attached. The caller (agent or "
                f"orchestrator) must attach a session before invoking "
                f"a marketplace tool."
            )
        return self.marketplace_session

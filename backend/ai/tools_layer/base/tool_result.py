"""
ToolResult — every tool returns exactly this shape. Never a bare dict,
never a raw exception.

Why `error` is a separate field from `message`:
`message` is meant for a human or an LLM to read ("Inventory updated
for SKU X"). `error` is meant for code to branch on — a stable string
like "AUTHENTICATION_ERROR" or "RATE_LIMIT" that an orchestrator or
guardrail can check with `if result.error == "RATE_LIMIT":` without
parsing prose. Collapsing these into one field is a common shortcut
that works fine until something downstream needs to distinguish
"retry this" from "don't retry this" and has to regex the message.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    message: str = ""

    # Stable machine-readable error code, set only when success=False.
    # Examples: "AUTHENTICATION_ERROR", "RATE_LIMIT", "NOT_IMPLEMENTED",
    # "VALIDATION_ERROR", "UNKNOWN_ERROR".
    error: Optional[str] = None

    execution_time: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any = None, message: str = "", execution_time: Optional[float] = None,
           metadata: Optional[dict[str, Any]] = None) -> "ToolResult":
        return cls(success=True, data=data, message=message,
                    execution_time=execution_time, metadata=metadata or {})

    @classmethod
    def fail(cls, message: str, error: str = "UNKNOWN_ERROR",
             execution_time: Optional[float] = None,
             metadata: Optional[dict[str, Any]] = None) -> "ToolResult":
        return cls(success=False, data=None, message=message, error=error,
                    execution_time=execution_time, metadata=metadata or {})

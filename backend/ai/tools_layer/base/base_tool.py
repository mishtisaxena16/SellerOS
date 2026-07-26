"""
BaseTool — the contract every tool in SellerOS implements.

Two methods, not one:

- `execute()` is what subclasses implement. It's allowed to raise —
  that keeps subclass code simple and readable.
- `run()` is what agents/LangGraph actually call. It wraps execute(),
  times it, and catches anything execute() raises, converting it into
  a ToolResult.fail(...). This is the actual point of having a Tool
  Layer: an agent calling run() can NEVER get an unhandled exception
  back, no matter how a specific tool is implemented. If every
  subclass had to remember to try/except internally, someone would
  eventually forget, and that's the exact failure mode this layer
  exists to prevent.

`permissions` is stored but not enforced here. The Guardrail Layer
(Phase 6 in the roadmap) is what should check permissions before a
tool ever runs. Storing the field now avoids retrofitting every tool
subclass later; enforcing it now would mean building guardrails logic
inside the tool layer, which the architecture explicitly says not to
do (see connector-layer notes on what NOT to add to a foundation
layer — same principle applies here).
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from backend.ai.tools_layer.base.tool_context import ToolContext
from backend.ai.tools_layer.base.tool_result import ToolResult


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool. Override name/description in subclasses."
    permissions: list[str] = []

    @abstractmethod
    async def execute(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        """Subclasses implement business logic here. Raising is fine —
        run() catches it. Return ToolResult.ok(...) or ToolResult.fail(...)
        directly for expected failure paths (e.g. a validation error you
        want to describe precisely, rather than a generic caught exception)."""
        raise NotImplementedError

    async def run(self, context: ToolContext, **kwargs: Any) -> ToolResult:
        start = time.perf_counter()
        try:
            result = await self.execute(context, **kwargs)
            if not isinstance(result, ToolResult):
                # A subclass returned something else. Fail loudly and
                # specifically instead of letting a malformed object
                # propagate to whatever LangGraph node called this.
                return ToolResult.fail(
                    message=f"Tool '{self.name}' returned {type(result).__name__}, "
                            f"expected ToolResult.",
                    error="CONTRACT_VIOLATION",
                    execution_time=time.perf_counter() - start,
                )
            if result.execution_time is None:
                result.execution_time = time.perf_counter() - start
            return result
        except NotImplementedError as exc:
            return ToolResult.fail(
                message=str(exc) or f"Tool '{self.name}' is not implemented yet.",
                error="NOT_IMPLEMENTED",
                execution_time=time.perf_counter() - start,
            )
        except ValueError as exc:
            return ToolResult.fail(
                message=str(exc),
                error="VALIDATION_ERROR",
                execution_time=time.perf_counter() - start,
            )
        except Exception as exc:  # noqa: BLE001 — intentional: this is the safety net
            return ToolResult.fail(
                message=f"Tool '{self.name}' failed: {exc}",
                error="UNKNOWN_ERROR",
                execution_time=time.perf_counter() - start,
                metadata={"exception_type": type(exc).__name__},
            )

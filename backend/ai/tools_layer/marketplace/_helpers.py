"""
Shared plumbing for the six marketplace tools. Not a tool itself —
just the "get connector from context, run it, map errors" logic that
would otherwise be copy-pasted into listing_tool.py, inventory_tool.py,
orders_tool.py, analytics_tool.py, ads_tool.py, and account_tool.py.

Two things worth being explicit about:

1. Error mapping. marketplace_connector.py raises typed exceptions
   (AuthenticationError, RateLimitError, MarketplaceUnavailableError,
   ...). This is exactly the information an orchestrator or guardrail
   needs to decide "retry" vs "ask the seller to reconnect their
   account" vs "give up". If this mapping isn't done here, that
   information dies at the tool boundary and everything downstream
   just sees ToolResult.fail with a generic message.

2. Sync-over-async, and why it's a real limitation right now, not a
   detail. Every function in marketplace_connector.py is synchronous.
   The mock connectors return instantly, so calling them directly from
   an async execute() costs nothing today. But BaseTool.execute() is
   declared async because LangGraph tool nodes expect an awaitable —
   and the moment a *live* connector does a real blocking HTTP call
   (Amazon SP-API, Flipkart REST) or Playwright automation (Meesho)
   inside one of these synchronous functions, calling it directly
   would block the whole event loop for every other in-flight agent
   request. That's why every call below goes through
   asyncio.to_thread(): it costs nothing extra against the mocks, and
   it's what actually needs to be true once live.py replaces the mock
   fetchers. Don't remove this "for no reason, mocks don't need it" —
   it's cheap now and load-bearing later.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, TypeVar

from ai.connectors_layer.marketplace_connector import (
    AuthenticationError,
    InvalidCredentialsError,
    MarketplaceSession,
    MarketplaceUnavailableError,
    RateLimitError,
)
from ai.tools_layer.base.tool_context import ToolContext
from ai.tools_layer.base.tool_result import ToolResult

T = TypeVar("T")

_ERROR_CODE_MAP: dict[type[Exception], str] = {
    InvalidCredentialsError: "INVALID_CREDENTIALS",
    AuthenticationError: "AUTHENTICATION_ERROR",
    RateLimitError: "RATE_LIMIT",
    MarketplaceUnavailableError: "MARKETPLACE_UNAVAILABLE",
    NotImplementedError: "NOT_IMPLEMENTED",
    ValueError: "VALIDATION_ERROR",
}


def get_session(context: ToolContext) -> MarketplaceSession:
    """Every marketplace tool starts a call with this line."""
    return context.require_session()


async def call_connector(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Runs a (currently synchronous) connector function off the event loop."""
    return await asyncio.to_thread(fn, *args, **kwargs)


def error_code_for(exc: Exception) -> str:
    for exc_type, code in _ERROR_CODE_MAP.items():
        if isinstance(exc, exc_type):
            return code
    return "UNKNOWN_ERROR"


async def run_connector_call(
    fn: Callable[..., T],
    *args: Any,
    success_message: str = "OK",
    **kwargs: Any,
) -> ToolResult:
    """
    Full pattern in one call: run connector fn off-thread, wrap success
    in ToolResult.ok, map known connector exceptions to a specific
    error code. Anything NOT in _ERROR_CODE_MAP (an unexpected bug
    inside a connector, say) is deliberately left to propagate — it
    gets caught by BaseTool.run()'s generic handler and tagged
    UNKNOWN_ERROR there. Catching it twice would just hide which layer
    actually caught it when debugging.

    Note on the SDK update: the connector layer's own `_dispatch()` choke
    point now resolves the platform registry lookup itself and raises a
    clear `NotImplementedError` naming the platform + operation when
    nothing is wired up for it — it no longer lets a bare KeyError escape
    a dict lookup like the earlier draft did. That's already covered by
    the NotImplementedError branch below, so there is nothing left for a
    tool-layer KeyError branch to catch. Kept out entirely rather than
    left in as dead code that implies a failure mode which can no longer
    occur here.
    """
    try:
        result = await call_connector(fn, *args, **kwargs)
        return ToolResult.ok(data=result, message=success_message)
    except (AuthenticationError, InvalidCredentialsError, RateLimitError,
            MarketplaceUnavailableError, NotImplementedError, ValueError) as exc:
        return ToolResult.fail(message=str(exc) or exc.__class__.__name__,
                                error=error_code_for(exc))

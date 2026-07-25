"""
AccountTool — wraps verify_connection / get_account.

Note: the connector layer groups these under "Module: Executive Agent",
not a marketplace-specific agent, since account status and connection
health are seller-account-level concerns the Executive Agent cares
about before routing to any specialized agent. AccountTool is exposed
here as a standalone tool (matching the folder tree in the spec) so
any agent can check "is this seller's Amazon connection alive"
without going through the Executive Agent specifically.

Gap to flag: the connector layer has no refresh() or disconnect()
equivalent to what the Connector Layer summary doc proposed under
"Connector Health" (connector.health() / .ping() / .refresh() /
.disconnect()). Only verify_connection() and get_account() exist
today. Those four health/lifecycle methods were explicitly listed as
still-pending production hardening in that doc — this tool can't wrap
what isn't built yet.
"""
from __future__ import annotations

from typing import Any, Optional

from tools.base.base_tool import BaseTool
from tools.base.tool_context import ToolContext
from tools.base.tool_result import ToolResult
from tools.marketplace._helpers import get_session, run_connector_call
from connectors import marketplace_connector as mc


class AccountTool(BaseTool):
    name = "account_tool"
    description = "Verify marketplace connection health and fetch seller account details."
    permissions: list[str] = ["account:read"]

    _ACTIONS = {"verify_connection", "get_account"}

    async def execute(self, context: ToolContext, action: Optional[str] = None,
                       **kwargs: Any) -> ToolResult:
        if action not in self._ACTIONS:
            return ToolResult.fail(
                message=f"AccountTool: unknown or missing action {action!r}. "
                        f"Expected one of: {sorted(self._ACTIONS)}",
                error="VALIDATION_ERROR",
            )
        session = get_session(context)
        return await getattr(self, f"_{action}")(session, **kwargs)

    async def _verify_connection(self, session) -> ToolResult:
        return await run_connector_call(
            mc.verify_connection, session,
            success_message="Connection verified.",
        )

    async def _get_account(self, session) -> ToolResult:
        return await run_connector_call(
            mc.get_account, session,
            success_message="Fetched account details.",
        )

    # -- public convenience wrappers --

    async def verify_connection(self, context: ToolContext) -> ToolResult:
        return await self.run(context, action="verify_connection")

    async def get_account(self, context: ToolContext) -> ToolResult:
        return await self.run(context, action="get_account")

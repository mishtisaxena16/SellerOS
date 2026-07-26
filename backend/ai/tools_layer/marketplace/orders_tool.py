"""
OrdersTool — wraps get_orders / get_order / get_shipments.

All three connector functions are read-only fetches. There is no
create/update/cancel order operation in marketplace_connector.py, which
is consistent with reality: sellers don't create orders, buyers do.
Nothing to flag here — this tool's surface matches the connector
exactly.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from backend.ai.tools_layer.base.base_tool import BaseTool
from backend.ai.tools_layer.base.tool_context import ToolContext
from backend.ai.tools_layer.base.tool_result import ToolResult
from backend.ai.tools_layer.marketplace._helpers import get_session, run_connector_call
from backend.ai.connectors_layer import marketplace_connector as mc


class OrdersTool(BaseTool):
    name = "orders_tool"
    description = "Fetch orders, a single order by ID, and shipments."
    permissions: list[str] = ["orders:read"]

    _ACTIONS = {"get_orders", "get_order", "get_shipments"}

    async def execute(self, context: ToolContext, action: Optional[str] = None,
                       **kwargs: Any) -> ToolResult:
        if action not in self._ACTIONS:
            return ToolResult.fail(
                message=f"OrdersTool: unknown or missing action {action!r}. "
                        f"Expected one of: {sorted(self._ACTIONS)}",
                error="VALIDATION_ERROR",
            )
        session = get_session(context)
        return await getattr(self, f"_{action}")(session, **kwargs)

    async def _get_orders(self, session, status: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           page: int = 1, limit: int = 50) -> ToolResult:
        return await run_connector_call(
            mc.get_orders, session, status=status, start_date=start_date,
            end_date=end_date, page=page, limit=limit,
            success_message="Fetched orders.",
        )

    async def _get_order(self, session, order_id: Optional[str] = None) -> ToolResult:
        if not order_id:
            return ToolResult.fail("get_order requires 'order_id'.", error="VALIDATION_ERROR")
        return await run_connector_call(
            mc.get_order, session, order_id,
            success_message=f"Fetched order {order_id}.",
        )

    async def _get_shipments(self, session, order_id: Optional[str] = None,
                              status: Optional[str] = None,
                              page: int = 1, limit: int = 50) -> ToolResult:
        return await run_connector_call(
            mc.get_shipments, session, order_id=order_id, status=status,
            page=page, limit=limit,
            success_message="Fetched shipments.",
        )

    # -- public convenience wrappers --

    async def get_orders(self, context: ToolContext, status: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          page: int = 1, limit: int = 50) -> ToolResult:
        return await self.run(context, action="get_orders", status=status,
                               start_date=start_date, end_date=end_date, page=page, limit=limit)

    async def get_order(self, context: ToolContext, order_id: str) -> ToolResult:
        return await self.run(context, action="get_order", order_id=order_id)

    async def get_shipments(self, context: ToolContext, order_id: Optional[str] = None,
                             status: Optional[str] = None,
                             page: int = 1, limit: int = 50) -> ToolResult:
        return await self.run(context, action="get_shipments", order_id=order_id,
                               status=status, page=page, limit=limit)

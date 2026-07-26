"""
InventoryTool — wraps get_inventory / update_inventory.

Note on connector-layer behavior this tool inherits as-is: nothing in
marketplace_connector.py or normalizer.py implements reserve_inventory
or release_inventory, even though the earlier architecture doc listed
them as InventoryTool functions. Only get/update exist on the
connector. Same "don't fake it" call as ListingTool.get_listing — this
tool exposes exactly the two operations the connector actually
supports and leaves reserve/release as unimplemented rather than
silently no-op.
"""
from __future__ import annotations

from typing import Any, Optional

from backend.ai.tools_layer.base.base_tool import BaseTool
from backend.ai.tools_layer.base.tool_context import ToolContext
from backend.ai.tools_layer.base.tool_result import ToolResult
from backend.ai.tools_layer.marketplace._helpers import get_session, run_connector_call
from backend.ai.connectors_layer import marketplace_connector as mc


class InventoryTool(BaseTool):
    name = "inventory_tool"
    description = "Fetch and update inventory/stock levels across marketplaces."
    permissions: list[str] = ["inventory:read", "inventory:write"]

    _ACTIONS = {"get_inventory", "update_inventory"}

    async def execute(self, context: ToolContext, action: Optional[str] = None,
                       **kwargs: Any) -> ToolResult:
        if action not in self._ACTIONS:
            return ToolResult.fail(
                message=f"InventoryTool: unknown or missing action {action!r}. "
                        f"Expected one of: {sorted(self._ACTIONS)}",
                error="VALIDATION_ERROR",
            )
        session = get_session(context)
        return await getattr(self, f"_{action}")(session, **kwargs)

    async def _get_inventory(self, session, sku: Optional[str] = None,
                              page: int = 1, limit: int = 50) -> ToolResult:
        return await run_connector_call(
            mc.get_inventory, session, sku=sku, page=page, limit=limit,
            success_message="Fetched inventory.",
        )

    async def _update_inventory(self, session, sku: Optional[str] = None,
                                 quantity: Optional[int] = None) -> ToolResult:
        if not sku or quantity is None:
            return ToolResult.fail("update_inventory requires 'sku' and 'quantity'.",
                                    error="VALIDATION_ERROR")
        return await run_connector_call(
            mc.update_inventory, session, sku, quantity,
            success_message=f"Inventory for SKU {sku} set to {quantity}.",
        )

    # -- public convenience wrappers --

    async def get_inventory(self, context: ToolContext, sku: Optional[str] = None,
                             page: int = 1, limit: int = 50) -> ToolResult:
        return await self.run(context, action="get_inventory", sku=sku, page=page, limit=limit)

    async def update_inventory(self, context: ToolContext, sku: str, quantity: int) -> ToolResult:
        return await self.run(context, action="update_inventory", sku=sku, quantity=quantity)

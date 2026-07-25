"""
ListingTool — the only thing between the Listing Agent and the
marketplace connector layer for listing operations.

Gap worth flagging, not hiding: the spec listed `get_listing()` as one
of ListingTool's functions, but marketplace_connector.py has no
single-listing lookup by listing_id — only `get_products()` (bulk,
paginated) and the create/update/publish/delete listing_id-based
mutations. Those two things aren't the same operation. Rather than
fake a get_listing() that silently does the wrong thing (e.g. fetches
page 1 of products and hopes the listing is in there), this tool
exposes `get_listings()` as the honest bulk-fetch wrapper and leaves
single-listing lookup as a known gap. If the Listing Agent actually
needs "fetch this one listing by ID", that method needs to be added
to the connector layer first — it doesn't exist to wrap yet.
"""
from __future__ import annotations

from typing import Any, Optional

from ai.tools_layer.base.base_tool import BaseTool
from ai.tools_layer.base.tool_context import ToolContext
from ai.tools_layer.base.tool_result import ToolResult
from ai.tools_layer.marketplace._helpers import get_session, run_connector_call
from ai.connectors_layer import marketplace_connector as mc


class ListingTool(BaseTool):
    name = "listing_tool"
    description = (
        "Create, publish, update, delete, and bulk-fetch marketplace listings "
        "(Amazon / Flipkart / Meesho) through the connector layer."
    )
    permissions: list[str] = ["listing:read", "listing:write"]

    _ACTIONS = {"get_listings", "create_listing", "publish_listing",
                "update_listing", "delete_listing"}

    async def execute(self, context: ToolContext, action: Optional[str] = None,
                       **kwargs: Any) -> ToolResult:
        if action not in self._ACTIONS:
            return ToolResult.fail(
                message=f"ListingTool: unknown or missing action {action!r}. "
                        f"Expected one of: {sorted(self._ACTIONS)}",
                error="VALIDATION_ERROR",
            )
        session = get_session(context)
        handler = getattr(self, f"_{action}")
        return await handler(session, **kwargs)

    # -- internal handlers, one per connector operation --------------------

    async def _get_listings(self, session, page: int = 1, limit: int = 50,
                             category: Optional[str] = None) -> ToolResult:
        return await run_connector_call(
            mc.get_products, session, page=page, limit=limit, category=category,
            success_message=f"Fetched page {page} of listings.",
        )

    async def _create_listing(self, session, product_data: Optional[dict] = None) -> ToolResult:
        if not product_data:
            return ToolResult.fail("create_listing requires 'product_data'.", error="VALIDATION_ERROR")
        return await run_connector_call(
            mc.create_listing, session, product_data,
            success_message="Listing created.",
        )

    async def _publish_listing(self, session, listing_id: Optional[str] = None) -> ToolResult:
        if not listing_id:
            return ToolResult.fail("publish_listing requires 'listing_id'.", error="VALIDATION_ERROR")
        return await run_connector_call(
            mc.publish_listing, session, listing_id,
            success_message=f"Listing {listing_id} published.",
        )

    async def _update_listing(self, session, listing_id: Optional[str] = None,
                               update_data: Optional[dict] = None) -> ToolResult:
        if not listing_id or not update_data:
            return ToolResult.fail(
                "update_listing requires 'listing_id' and 'update_data'.", error="VALIDATION_ERROR")
        return await run_connector_call(
            mc.update_listing, session, listing_id, update_data,
            success_message=f"Listing {listing_id} updated.",
        )

    async def _delete_listing(self, session, listing_id: Optional[str] = None) -> ToolResult:
        if not listing_id:
            return ToolResult.fail("delete_listing requires 'listing_id'.", error="VALIDATION_ERROR")
        return await run_connector_call(
            mc.delete_listing, session, listing_id,
            success_message=f"Listing {listing_id} deleted.",
        )

    # -- public convenience wrappers, matching the spec's flat method names --

    async def get_listings(self, context: ToolContext, page: int = 1, limit: int = 50,
                            category: Optional[str] = None) -> ToolResult:
        return await self.run(context, action="get_listings", page=page, limit=limit, category=category)

    async def create_listing(self, context: ToolContext, product_data: dict) -> ToolResult:
        return await self.run(context, action="create_listing", product_data=product_data)

    async def publish_listing(self, context: ToolContext, listing_id: str) -> ToolResult:
        return await self.run(context, action="publish_listing", listing_id=listing_id)

    async def update_listing(self, context: ToolContext, listing_id: str, update_data: dict) -> ToolResult:
        return await self.run(context, action="update_listing", listing_id=listing_id, update_data=update_data)

    async def delete_listing(self, context: ToolContext, listing_id: str) -> ToolResult:
        return await self.run(context, action="delete_listing", listing_id=listing_id)

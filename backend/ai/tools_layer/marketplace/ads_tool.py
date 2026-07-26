"""
AdsTool — wraps get_campaigns / create_campaign / delete_campaign.

Gaps to flag: the architecture doc's Ads Tool list also includes
pause_campaign() and campaign_metrics(). Neither exists in
marketplace_connector.py — there's create/fetch/delete only, no pause
and no per-campaign metrics endpoint (campaign performance would
presumably come through the Analytics tool once that's extended, or a
dedicated ads-metrics connector function that doesn't exist yet).
Exposing pause_campaign() here would mean inventing behavior the
connector layer was never built to support — better to surface the
gap now than ship a tool method that silently does nothing.
"""
from __future__ import annotations

from typing import Any, Optional

from backend.ai.tools_layer.base.base_tool import BaseTool
from backend.ai.tools_layer.base.tool_context import ToolContext
from backend.ai.tools_layer.base.tool_result import ToolResult
from backend.ai.tools_layer.marketplace._helpers import get_session, run_connector_call
from backend.ai.connectors_layer import marketplace_connector as mc


class AdsTool(BaseTool):
    name = "ads_tool"
    description = "Fetch, create, and delete advertising campaigns."
    permissions: list[str] = ["ads:read", "ads:write"]

    _ACTIONS = {"get_campaigns", "create_campaign", "delete_campaign"}

    async def execute(self, context: ToolContext, action: Optional[str] = None,
                       **kwargs: Any) -> ToolResult:
        if action not in self._ACTIONS:
            return ToolResult.fail(
                message=f"AdsTool: unknown or missing action {action!r}. "
                        f"Expected one of: {sorted(self._ACTIONS)}",
                error="VALIDATION_ERROR",
            )
        session = get_session(context)
        return await getattr(self, f"_{action}")(session, **kwargs)

    async def _get_campaigns(self, session, status: Optional[str] = None,
                              page: int = 1, limit: int = 50) -> ToolResult:
        return await run_connector_call(
            mc.get_campaigns, session, status=status, page=page, limit=limit,
            success_message="Fetched campaigns.",
        )

    async def _create_campaign(self, session, campaign_data: Optional[dict] = None) -> ToolResult:
        if not campaign_data:
            return ToolResult.fail("create_campaign requires 'campaign_data'.", error="VALIDATION_ERROR")
        return await run_connector_call(
            mc.create_campaign, session, campaign_data,
            success_message="Campaign created.",
        )

    async def _delete_campaign(self, session, campaign_id: Optional[str] = None) -> ToolResult:
        if not campaign_id:
            return ToolResult.fail("delete_campaign requires 'campaign_id'.", error="VALIDATION_ERROR")
        return await run_connector_call(
            mc.delete_campaign, session, campaign_id,
            success_message=f"Campaign {campaign_id} deleted.",
        )

    # -- public convenience wrappers --

    async def get_campaigns(self, context: ToolContext, status: Optional[str] = None,
                             page: int = 1, limit: int = 50) -> ToolResult:
        return await self.run(context, action="get_campaigns", status=status, page=page, limit=limit)

    async def create_campaign(self, context: ToolContext, campaign_data: dict) -> ToolResult:
        return await self.run(context, action="create_campaign", campaign_data=campaign_data)

    async def delete_campaign(self, context: ToolContext, campaign_id: str) -> ToolResult:
        return await self.run(context, action="delete_campaign", campaign_id=campaign_id)

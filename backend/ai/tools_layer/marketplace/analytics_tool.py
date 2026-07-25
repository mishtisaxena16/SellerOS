"""
AnalyticsTool — wraps get_sales_metrics / get_business_metrics.

Gap to flag: the architecture doc also lists forecast_sales() under
the Analytics Agent's tool. There is no forecasting logic anywhere in
the connector layer or normalizer — forecasting isn't a marketplace
API call to begin with, it's computation SellerOS would do on top of
sales_metrics history. That doesn't belong in a connector-wrapping
tool at all; it belongs in the Analytics Agent itself (or a dedicated
forecasting tool that consumes this tool's output). Not implementing
it here isn't a gap in this file — it would be the wrong place for it.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from ai.tools_layer.base.base_tool import BaseTool
from ai.tools_layer.base.tool_context import ToolContext
from ai.tools_layer.base.tool_result import ToolResult
from ai.tools_layer.marketplace._helpers import get_session, run_connector_call
from ai.connectors_layer import marketplace_connector as mc


class AnalyticsTool(BaseTool):
    name = "analytics_tool"
    description = "Fetch sales metrics and business (KPI) metrics for a seller."
    permissions: list[str] = ["analytics:read"]

    _ACTIONS = {"get_sales_metrics", "get_business_metrics"}

    async def execute(self, context: ToolContext, action: Optional[str] = None,
                       **kwargs: Any) -> ToolResult:
        if action not in self._ACTIONS:
            return ToolResult.fail(
                message=f"AnalyticsTool: unknown or missing action {action!r}. "
                        f"Expected one of: {sorted(self._ACTIONS)}",
                error="VALIDATION_ERROR",
            )
        session = get_session(context)
        return await getattr(self, f"_{action}")(session, **kwargs)

    async def _get_sales_metrics(self, session, start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None,
                                  timeframe: str = "30d") -> ToolResult:
        return await run_connector_call(
            mc.get_sales_metrics, session, start_date=start_date, end_date=end_date,
            timeframe=timeframe, success_message=f"Fetched sales metrics ({timeframe}).",
        )

    async def _get_business_metrics(self, session, start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None,
                                     timeframe: str = "30d") -> ToolResult:
        return await run_connector_call(
            mc.get_business_metrics, session, start_date=start_date, end_date=end_date,
            timeframe=timeframe, success_message=f"Fetched business metrics ({timeframe}).",
        )

    # -- public convenience wrappers --

    async def get_sales_metrics(self, context: ToolContext, start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None, timeframe: str = "30d") -> ToolResult:
        return await self.run(context, action="get_sales_metrics", start_date=start_date,
                               end_date=end_date, timeframe=timeframe)

    async def get_business_metrics(self, context: ToolContext, start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None, timeframe: str = "30d") -> ToolResult:
        return await self.run(context, action="get_business_metrics", start_date=start_date,
                               end_date=end_date, timeframe=timeframe)

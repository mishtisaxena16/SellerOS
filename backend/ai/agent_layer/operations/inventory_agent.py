"""
InventoryAgent — second agent in the build order (section 25: "2.
Inventory Agent"). Reports on stock levels and can update them when
asked, using InventoryTool.

Two separate concerns kept genuinely separate, matching the
Planner/Executor split:

- Reading/reporting: default_plan's tool step fetches the live
  inventory snapshot; the "summarize_inventory" step asks the Reasoner
  to turn that into a plain-language flag (low stock / out of stock /
  overstocked) using ONLY the numbers actually fetched (see
  prompts/inventory.md's explicit "do not invent stock numbers"
  instruction) — a seller acting on a wrong stock number is a real
  business mistake, not a cosmetic one.

- Writing: `update_stock()` is a separate, explicit method — not
  something that happens as a side effect of asking a question. An
  agent silently deciding to write to a marketplace's live inventory
  because it inferred that from a seller's phrasing would be exactly
  the kind of thing the (not-yet-built) Guardrail Layer's "Human
  Approval Gates" (section 29) exists to catch. Until that layer
  exists, requiring an explicit, separate call is this agent's own
  stand-in guardrail — not a replacement for a real one.
"""
from __future__ import annotations

from typing import Any, Optional

from ai.agent_layer.base.agent import BaseAgent
from ai.agent_layer.base.agent_result import AgentResult
from ai.agent_layer.base.state import AgentState
from ai.agent_layer.base.tool_manager import ToolManager
from ai.connectors_layer.marketplace_connector import MarketplaceSession


class InventoryAgent(BaseAgent):
    name = "inventory_agent"
    description = (
        "Reports on stock levels across marketplaces and flags SKUs "
        "that are low, out of stock, or overstocked. Can update stock "
        "quantities when explicitly asked."
    )

    permissions: dict[str, bool] = {
        "can_read_inventory": True,
        "can_update_inventory": True,
        "can_create_ads": False,
    }
    allowed_tools: list[str] = ["inventory"]

    prompt_name = "inventory"
    context_sections = ["user", "seller", "marketplace", "inventory", "business_rules"]

    default_plan: list[dict[str, Any]] = [
        {"tool": "inventory", "action": "get_inventory"},
        {"step": "summarize_inventory"},
    ]

    async def handle_step(self, step: dict[str, Any], state: AgentState, context: Any) -> Any:
        if step.get("step") != "summarize_inventory":
            state.add_error(f"InventoryAgent has no handler for step {step!r}.")
            return None

        rendered = self.prompt_builder.render(self.prompt_name, context, user_query=state.user_query)
        for warning in rendered.warnings:
            state.intermediate_thoughts.append(f"[prompt warning] {warning}")

        result = await self.reasoner.generate(rendered.text)
        state.final_response = result.text
        return result.text

    # -- explicit write path, deliberately separate from run() --------------

    async def update_stock(
        self,
        tool_manager: ToolManager,
        session: MarketplaceSession,
        sku: str,
        quantity: int,
    ) -> AgentResult:
        """
        Updates a single SKU's stock quantity. Deliberately bypasses
        Planner/Executor entirely — this is a direct, single tool call
        with no LLM step in between, because a stock-quantity write
        should reflect exactly what the caller asked for, not an LLM's
        paraphrase of it.
        """
        result = await tool_manager.call(
            "inventory", session=session, action="update_inventory",
            sku=sku, quantity=quantity,
        )
        if not result.success:
            return AgentResult.fail(message=result.message, tool_calls=[result])
        return AgentResult.ok(
            message=f"Updated SKU {sku} to quantity {quantity}.",
            data=result.data,
            tool_calls=[result],
        )

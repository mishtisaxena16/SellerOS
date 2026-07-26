"""
Executor — runs the steps a Planner produced, one at a time, against
AgentState (section 17):

    Run Step 1
    Run Step 2
    Run Step 3

Two kinds of steps by design, distinguished by which key is present:

- {"tool": "<name>", "action": "<action>", **kwargs}
    A tool call. Executor routes this through ToolManager (never
    imports a tool directly — same rule the agents themselves follow)
    and appends the ToolResult to AgentState.tool_results.

- {"step": "<label>", ...}
    A non-tool step — e.g. "generate_listing" or "quality_check" —
    that the calling agent handles itself (typically an LLM call via
    the Reasoner, or agent-specific logic). Executor doesn't know how
    to run these; it hands control back to the agent via the
    `step_handler` callback and records whatever that returns.

This split exists because not every plan step is a tool call — the
handover doc's own example plan
(section 16: Fetch Product, Retrieve Knowledge, Generate Listing,
Quality Check) mixes both: the first two are tool calls, the last two
are agent/LLM work. Forcing everything through ToolManager would mean
inventing fake tools for "generate_listing", which isn't a marketplace
operation and doesn't belong in the Tool Layer.

On failure: a failed step does NOT abort the whole plan by default.
Independent steps (e.g. "fetch inventory" and "fetch knowledge") can
legitimately fail separately without either blocking the other. An
agent that needs strict fail-fast semantics (step 2 requires step 1's
output) should check `state.has_errors()` / the specific prior
ToolResult inside its own `step_handler` and decide to stop early —
that's an agent-specific policy, not something Executor should assume
for every agent.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

from backend.ai.agent_layer.base.state import AgentState
from backend.ai.agent_layer.base.tool_manager import ToolManager
from backend.ai.connectors_layer.marketplace_connector import MarketplaceSession

StepHandler = Callable[[dict[str, Any], AgentState], Awaitable[Any]]


class Executor:
    def __init__(self, tool_manager: ToolManager) -> None:
        self._tool_manager = tool_manager

    async def run_plan(
        self,
        state: AgentState,
        session: Optional[MarketplaceSession] = None,
        step_handler: Optional[StepHandler] = None,
    ) -> AgentState:
        for step in state.plan:
            state.intermediate_thoughts.append(f"Running step {state.current_step + 1}: {step}")

            if "tool" in step:
                tool_name = step["tool"]
                action = step.get("action")
                kwargs = {k: v for k, v in step.items() if k not in ("tool", "action")}
                if action is not None:
                    kwargs["action"] = action
                result = await self._tool_manager.call(tool_name, session=session, **kwargs)
                # Tag after the call, not before: ToolResult.metadata is
                # the tool's own to fill in, so only fill in what it left
                # blank. This is the only place in the whole call chain
                # that knows both "which tool/action was requested" and
                # "here's the ToolResult it produced" — Guardrails'
                # ToolExecutionRule (guardrails.py) has nothing else to
                # check against without this.
                result.metadata.setdefault("tool_name", tool_name)
                result.metadata.setdefault("action", action)
                state.record_tool_result(result)
                if not result.success:
                    state.add_error(f"Step '{tool_name}.{action}' failed: {result.message}")

            elif "step" in step:
                if step_handler is None:
                    state.add_error(
                        f"Step {step!r} requires an agent-provided step_handler, "
                        f"but none was given to Executor.run_plan()."
                    )
                else:
                    try:
                        await step_handler(step, state)
                    except Exception as exc:  # noqa: BLE001 — same safety-net rationale as BaseTool.run()
                        state.add_error(f"Step {step['step']!r} raised: {exc}")

            else:
                state.add_error(f"Malformed plan step (no 'tool' or 'step' key): {step!r}")

            state.advance()

        return state

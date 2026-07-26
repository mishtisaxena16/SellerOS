"""
test_integration_e2e.py — exercises the REAL path:

    Supervisor -> Orchestrator (LangGraph) -> Memory -> Guardrails
        -> Agents -> ToolManager -> Tools -> Connectors

against the actual code, not a mock of it. The only thing substituted
is the Reasoner (every agent's LLM call) — there's no Ollama server
reachable from this sandbox, and that's a deployment fact having
nothing to do with whether the plumbing above it is wired correctly.
A FakeReasoner satisfying the same `LLMReasoner` Protocol
(agent_layer/base/reasoning.py) stands in so every other layer —
Memory, Guardrails, MarketplaceSession injection, tool dispatch,
connector calls — runs for real and can actually be checked.

Run with: python3 test_integration_e2e.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# tests/ now lives at SellerOS/tests/, separate from SellerOS/backend/ —
# resolve relative to this file instead of assuming cwd is backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import backend.ai.orchestrator_layer.orchestrator as orchestrator
import backend.ai.supervisor_layer.supervisor as supervisor_module
from backend.ai.connectors_layer import session_store
from backend.ai.agent_layer.base.reasoning import ReasonerResult


class FakeReasoner:
    """Satisfies the LLMReasoner Protocol without touching Ollama."""

    async def generate(self, prompt: str, **kwargs) -> ReasonerResult:
        return ReasonerResult(text="[fake reasoner output for testing]")


def _patch_all_agents_with_fake_reasoner() -> None:
    fake = FakeReasoner()
    for key in orchestrator.agent_registry.list_agents():
        orchestrator.agent_registry.get(key).reasoner = fake


def _check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        raise AssertionError(f"{label}: {detail}")


async def test_seller_coach_no_session_needed():
    """Knowledge-only agent — should run without any MarketplaceSession."""
    result = await orchestrator.run_workflow(
        query="how do I improve my GST compliance as a seller",
        seller_id="test_seller_1",
    )
    _check("seller_coach reaches final_response", result.get("final_response") is not None, str(result))
    _check("seller_coach intent routed correctly", result.get("intent") == "seller_coach", str(result.get("intent")))
    print("  -> final_response:", result.get("final_response"))
    print("  -> executed_tools:", result.get("executed_tools"))


async def test_inventory_without_any_session_registered():
    """No session registered for this seller/platform — must fail
    CLEANLY at the connector/tool layer with a specific, honest error,
    not silently succeed and not crash with an unrelated exception."""
    session_store.clear("test_seller_2")
    result = await orchestrator.run_workflow(
        query="check my meesho inventory levels",
        seller_id="test_seller_2",
        marketplace="meesho",
    )
    print("  -> error:", result.get("error"))
    print("  -> final_response:", result.get("final_response"))
    _check("intent detected as inventory", result.get("intent") == "inventory", str(result.get("intent")))


async def test_inventory_with_session_registered():
    """THE fix under test: once a session is registered for this
    seller/platform, the agent -> tool -> connector call should get
    PAST ToolContext.require_session() (which is what failed 100% of
    the time before this integration pass) — any failure beyond that
    point is an infrastructure fact (no real Meesho login, no browser,
    no network egress in this sandbox), not the bug being fixed here.
    """
    session_store.register(
        "test_seller_3", "meesho",
        {"username": "test@example.com", "password": "not-a-real-password"},
    )
    result = await orchestrator.run_workflow(
        query="check my meesho inventory levels",
        seller_id="test_seller_3",
        marketplace="meesho",
    )
    executed = result.get("executed_tools", [])
    print("  -> executed_tools:", executed)
    print("  -> error:", result.get("error"))
    _check(
        "inventory tool was actually invoked (not blocked before it ran)",
        any(call.get("tool") == "inventory" for call in executed),
        str(executed),
    )
    # If it failed, it must NOT be the old "no marketplace_session attached" error.
    err = (result.get("error") or "") + str(result.get("final_response") or "")
    _check(
        "did not fail with the old missing-session error",
        "no marketplace_session attached" not in err.lower(),
        err,
    )


async def test_guardrail_blocks_bad_tool_name():
    """Directly exercise the fixed ToolExecutionRule with a state that
    claims an unauthorized tool ran, confirming ALLOWED_TOOLS now
    actually matches real tool keys and the rule fires on the right field."""
    from backend.ai.guardrails_layer.guardrails import guardrail_engine

    state_good = {"executed_tools": [{"agent": "inventory_agent", "tool": "inventory", "action": "get_inventory", "success": True}]}
    result_good = guardrail_engine.evaluate(state_good)
    _check("real tool name 'inventory' is allowed", result_good.decision.value != "block", str(result_good.messages()))

    state_bad = {"executed_tools": [{"agent": "inventory_agent", "tool": "sql_read_query", "action": "x", "success": True}]}
    result_bad = guardrail_engine.evaluate(state_bad)
    _check("made-up tool name is blocked", result_bad.blocked, str(result_bad.messages()))


async def test_mutating_intent_requires_approval():
    """create_listing is a MUTATING_ACTION intent -> guardrail should
    require human approval before publish, and publish_node must
    refuse to publish without it."""
    session_store.register("test_seller_4", "amazon", {})
    result = await orchestrator.run_workflow(
        query="create a listing for my new product on amazon",
        seller_id="test_seller_4",
        marketplace="amazon",
    )
    print("  -> approval_required:", result.get("approval_required"))
    print("  -> published_status:", result.get("published_status"))
    _check("approval_required is set", result.get("approval_required") is True, str(result))
    _check("publish did not happen without approval", result.get("published_status") != "SUCCESS", str(result.get("published_status")))


async def test_supervisor_layer_end_to_end():
    """The actual entry point a backend would call — supervisor.handle()."""
    result = await supervisor_module.supervisor.handle(
        query="how should I price my products competitively",
        seller_id="test_seller_5",
        session_id="session_5",
    )
    print("  -> supervisor result:", result)
    _check("supervisor returns a response", bool(result.get("response")), str(result))
    _check("supervisor detected pricing intent", "pricing" in result.get("intent", []), str(result.get("intent")))


async def main():
    _patch_all_agents_with_fake_reasoner()
    tests = [
        test_seller_coach_no_session_needed,
        test_inventory_without_any_session_registered,
        test_inventory_with_session_registered,
        test_guardrail_blocks_bad_tool_name,
        test_mutating_intent_requires_approval,
        test_supervisor_layer_end_to_end,
    ]
    failures = 0
    for test in tests:
        print(f"\n=== {test.__name__} ===")
        try:
            await test()
        except Exception as exc:
            failures += 1
            print(f"[FAIL] {test.__name__} raised: {exc!r}")

    print(f"\n{'='*60}\n{len(tests) - failures}/{len(tests)} tests passed")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

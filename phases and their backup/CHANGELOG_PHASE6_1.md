# CHANGELOG — Phase 6.1: Agent Execution Planner

## Scope

This phase adds **only** a pre-execution planning layer: given a user
query, determine which agents *would* be involved, in what order, and
why — and attach that plan to the chat response. **No agent execution,
multi-agent orchestration, UI timeline, reasoning flow, or response
aggregation was added or changed.** Phases 1–5 (LangGraph orchestrator,
Supervisor, existing agents, tools, connectors, guardrails, memory,
frontend) are untouched in behavior; the only frontend-visible change
is one new optional field on the existing chat response.

---

## Files Created

- `backend/ai/planner_layer/__init__.py`
  Package docstring describing the layer's scope and public surface.

- `backend/ai/planner_layer/models.py`
  **Task 1 — ExecutionPlan model.**
  - `ExecutionStatus` — enum: `pending`, `running`, `completed`,
    `failed`, `skipped`.
  - `ExecutionStep` — dataclass: `agent_id`, `display_name`, `reason`,
    `status` (defaults to `pending`), `execution_order`.
  - `ExecutionPlan` — dataclass wrapping `steps: list[ExecutionStep]`,
    with `.as_list()` (steps sorted by `execution_order`, each as a
    plain dict — the exact shape the API response uses) and
    `.agent_ids` / `.is_empty()` helpers.

- `backend/ai/planner_layer/agent_planner.py`
  **Task 2 — Agent Planner** (modular keyword routing) and
  **Task 3 — Execution Order.**
  - `AGENT_CATALOG` — `agent_id -> display_name` map. IDs reuse the real
    `agent_registry.py` keys where one already exists (`analytics`,
    `inventory`, `pricing`, `listing`, `seller_coach`, and `ads`'s
    domain is represented as `marketing`); `policy` has no registered
    agent yet and is included only because the routing spec calls for
    it on listing questions (same "not implemented yet" honesty pattern
    already used elsewhere in this codebase, e.g.
    `supervisor.py`'s `unimplemented_intents`).
  - `RoutingRule` — small dataclass: `name`, `keywords`, `agent_ids`,
    `reason`. Routing table (`_ROUTING_RULES`) implements the four
    example categories from the spec:
    - **Sales** (`sales`, `revenue`, `sold`, `profit`, ...) → Analytics,
      Pricing
    - **Inventory** (`inventory`, `stock`, `restock`, `out of stock`,
      ...) → Inventory
    - **Ads** (`ads`, `advertising`, `campaign`, `ppc`, ...) → Marketing,
      Analytics
    - **Listing** (`listing`, `product page`, `description`, ...) →
      Listing, Policy
    - No match → General question → Seller Coach only
  - `AgentPlanner.build_plan(query)` unions every matching rule's
    agents (first-match order, de-duplicated) so a query touching more
    than one category gets every relevant agent, then appends
    **Seller Coach exactly once, always last**, regardless of whether a
    rule already referenced it.
  - `AgentPlanner._assign_execution_order(...)` assigns 1-based
    `execution_order` in list order — Seller Coach is guaranteed by
    `build_plan()` to already be last, so it always gets the highest
    number.
  - Deliberately independent of `orchestrator.INTENT_KEYWORDS` (own
    routing table) — see the module docstring for why: this is a
    separate, purely descriptive layer, not a second copy of the
    execution-facing router.
  - `agent_planner` — module-level singleton, same pattern as
    `agent_registry` / `guardrail_engine` / `supervisor`.

---

## Files Modified

- `backend/ai/supervisor_layer/supervisor.py`
  **Task 4 — Backend Integration.**
  - Imports `agent_planner` and aliases `planner_layer.models.ExecutionPlan`
    to `AgentExecutionPlan` on import, specifically to avoid colliding
    with this module's own, pre-existing `ExecutionPlan`/`ExecutionStep`
    classes (those back the *existing* `TaskDecomposer` →
    `orchestrator.run_workflow(plan=...)` path and are unchanged).
  - `Supervisor.__init__` now also builds a `self._agent_planner`.
  - `Supervisor.handle()` calls `self._agent_planner.build_plan(query)`
    alongside (not instead of) the existing `TaskDecomposer.build_plan()`
    call, and passes `.as_list()` through to
    `ResponseSynthesizer.from_state(...)`. This call is pure computation
    — it happens before, and has no effect on, the
    `orchestrator.run_workflow(...)` call that actually executes agents.
  - `SupervisorResult` gained one new field, `agent_execution_plan:
    list[dict]` (defaults to `[]`), added to `.as_dict()`. Purely
    additive — every existing key is unchanged.
  - `ResponseSynthesizer.from_state(...)` gained one new optional
    parameter, `agent_execution_plan` (defaults to `[]` if omitted),
    used by `Supervisor.resume()` unchanged (no original query is
    available on resume, so there is nothing to re-plan from — an
    empty plan is the honest answer there, not a guess).

- `backend/schema/chat.py`
  **Task 5 — API Response.**
  - Added `ExecutionStepSchema` (pydantic mirror of
    `planner_layer.models.ExecutionStep`, for the HTTP contract).
  - `ChatResponse` gained one new field:
    `execution_plan: list[ExecutionStepSchema] = []`. All existing
    fields (`response`, `intent`, `marketplace`, `awaiting_approval`,
    `thread_id`, `guardrail_findings`, `unimplemented_intents`) are
    unchanged — existing frontend code that doesn't read
    `execution_plan` keeps working exactly as before.

- `backend/api/routers/chat.py`
  - Both `POST /chat` and `POST /chat/approve` now pass
    `execution_plan=result.get("agent_execution_plan", [])` into the
    `ChatResponse` they construct. No other behavior in either endpoint
    changed.

---

## Integration Notes

- **Nothing executes agents in this phase.** `AgentPlanner.build_plan()`
  never calls `agent_registry.get(...)`, never builds a `ToolManager`,
  and is never awaited — it's synchronous, pure, and side-effect-free.
  The existing `orchestrator.run_workflow(...)` call in
  `Supervisor.handle()` still runs exactly as it did before this phase;
  Phase 6.1 does not gate, delay, or otherwise change when or how that
  happens. (Separately: today's `execution_plan` in the response and
  today's actual agent execution are two independent code paths that
  happen to run in the same request — a later phase is expected to make
  the planner's output actually drive execution; that wiring is
  explicitly out of scope here.)
- **New response field is additive only.** `ChatResponse.execution_plan`
  defaults to `[]`; existing frontend code (`AgentTimeline.tsx`,
  `AgentConsole.tsx`, `ChatMessageContent.tsx`, etc.) was **not**
  touched and does not read this field yet, per the "DO NOT CHANGE"
  list for this phase (Frontend, Timeline UI, Agent Console, Execution
  Cards, Reasoning Flow, Confidence Scores, Seller Coach Summary, Mock
  Data, Business Intelligence, Playwright, Marketplace APIs).
- **Naming collision, resolved by aliasing, not renaming.**
  `backend/ai/supervisor_layer/supervisor.py` already had its own
  `ExecutionPlan`/`ExecutionStep` (a flat `action`/`status` list fed
  into `SellerOSState["plan"]` for the LangGraph orchestrator — a
  different, pre-existing concern). Phase 6.1's `ExecutionPlan`/
  `ExecutionStep` in `planner_layer/models.py` are the richer,
  displayable shape the spec asks for (`agent_id`, `display_name`,
  `reason`, `status`, `execution_order`). Both are correct for their
  own module; `supervisor.py` imports the new one under the alias
  `AgentExecutionPlan` so neither definition is touched or shadowed.
- **`policy` agent_id has no backing agent yet.** Included in
  `AGENT_CATALOG` and the "listing" routing rule only because Task 2's
  routing table calls for it; `agent_registry.py` has no `PolicyAgent`
  registered today (Product Studio ships `listing`/`pricing` only). This
  is purely a planning-layer label until a real agent is registered
  under that key — no different in kind from the existing
  `unimplemented_intents` pattern already surfaced by `supervisor.py`.
- **Backward compatibility verified:**
  - `ChatResponse` round-trips with and without `execution_plan`
    supplied (defaults to `[]`).
  - `SupervisorResult.as_dict()` still returns every previously-existing
    key, unchanged, plus the one new key.
  - No changes to `orchestrator.py`, `guardrails.py`, `memory_layer/`,
    `agent_layer/` (agents/tools/registries), `connectors_layer/`,
    Playwright usage, or any frontend file.

## Example

Request: `POST /chat` with `"message": "My sales have dropped this month."`

Response now includes (in addition to all pre-existing fields):

```json
{
  "execution_plan": [
    { "agent_id": "analytics", "display_name": "Analytics Agent", "reason": "Query mentions sales/revenue performance", "status": "pending", "execution_order": 1 },
    { "agent_id": "pricing", "display_name": "Pricing Agent", "reason": "Query mentions sales/revenue performance", "status": "pending", "execution_order": 2 },
    { "agent_id": "seller_coach", "display_name": "Seller Coach", "reason": "Seller Coach always summarizes and advises after specialist agents", "status": "pending", "execution_order": 3 }
  ]
}
```

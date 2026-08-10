# Phase 7.6B — Business Context Injected Into the AI Execution Pipeline

## Goal
Every AI agent now receives the Phase 7.6A Business Context alongside the
user request and RAG-retrieved knowledge, without any agent loading mock
data individually and without duplicating any business calculation.

## Execution flow (unchanged nodes in bold, new node in **bold+italic**)

```
User Request
    ↓
**context_assembly** → **memory_layer** → **router** (Intent Router)
    ↓
***business_context*** (NEW — Phase 7.6A Business Context Builder, called once)
    ↓
**supervisor** (in-graph routing) → **agent node**
    ↓
    agent.run() → ContextBuilder.build() (RAG / "knowledge" section, unchanged)
    ↓
**guardrail → approval → publish**
    ↓
Final Response
```

RAG retrieval itself was not touched — it still happens exactly where it
did before, inside each agent's own `ContextBuilder.build()` call. Because
`business_context` now runs upstream of every agent node, its output is
already sitting in shared state by the time each agent's own RAG lookup
runs, satisfying the required order without moving or modifying the RAG
step.

## Files changed

### `backend/ai/orchestrator_layer/orchestrator.py`
- Added `business_context_node`: opens a short-lived DB session
  (`SessionLocal`, the same factory `backend/database/session.py`'s
  `get_db()` dependency uses), calls the existing
  `backend.ai.context.business_context.get_business_context()` **once**,
  and folds the result into the existing shared `context` dict under a
  new `business_context` key — no new state field, no second context
  object.
- Registered the node and rewired one edge: `router → business_context →
  supervisor` (previously `router → supervisor`). No other edges changed.
- `_run_agent_node` now reads `state["context"]["business_context"]` and
  passes it into `agent.run(business_context=...)`.
- Degrades honestly: a non-numeric/missing `seller_id` or an unexpected
  failure logs an event and continues with no business context, instead
  of failing the run — matching this file's existing error handling
  style. `get_business_context()` itself already handles "no marketplace
  connected" (Phase 7.6A); this node adds no new business logic on top
  of it.

### `backend/ai/agent_layer/base/agent.py`
- `BaseAgent.run()` gained one new optional parameter,
  `business_context: Optional[dict[str, Any]] = None`.
- When present, it's attached as its own `ContextSection` ("business_context")
  right after `ContextBuilder.build()` returns — before that context is
  flattened into `state.retrieved_context`, so every agent's prompt-context
  dict automatically includes it. This is additive only: existing callers
  that don't pass `business_context` behave exactly as before.
- Does not touch `handle_step()`, `Planner`, `Reasoner`, prompt templates,
  or `ContextBuilder`'s own "business" section (the separately computed
  human-readable snapshot used by Seller Coach today) — that logic is
  unchanged and un-duplicated.

## Not changed (in scope, but intentionally left alone)
- RAG / Chroma / retrieval / `KnowledgeTool` — untouched.
- Connectors, Playwright, mock datasets — untouched.
- Any existing business calculation (revenue, low-stock, cancellation
  rate, dashboard summary math) — untouched; still computed in exactly
  one place each.
- Agent reasoning and prompt templates — untouched.
- No new API endpoints. No UI changes.
- The Phase 7.6A `business_context.py` / `marketplace_data_service.py`
  functions — reused exactly as they were; nothing in them changed.

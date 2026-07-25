# SellerOS Agent SDK — frozen contract

Every agent in `agent_layer/` is a subclass of `BaseAgent`
(`agent_layer/base/agent.py`) and exposes exactly the same lifecycle.
This is the contract new agents must follow; it does not change per
agent, per domain, or per tier.

```
BaseAgent
    │
    ├── SellerCoachAgent      (domain: seller_coach)
    ├── ListingAgent          (domain: product_studio)
    ├── PricingAgent          (domain: product_studio)
    ├── InventoryAgent        (domain: operations)
    ├── OrdersAgent           (domain: operations)
    └── ...
```

## The five-step lifecycle (`BaseAgent.run()`)

1. **Validate request** — `ContextBuilder.build(..., include=self.context_sections)`
   assembles only the sections this agent declared it needs.
2. **Build plan** — `Planner.create_plan(self.default_plan, user_query,
   overrides=self.override_plan)`. `default_plan` is a static template;
   `override_plan` is the only per-agent hook for filling in dynamic
   values (e.g. a knowledge-search query) — it never reorders or adds
   steps.
3. **Execute tools** — `Executor` runs the plan's tool steps through
   `ToolManager.call(...)`, in order, appending each `ToolResult` to
   `state.tool_results`.
4. **Reason over results** — the plan's one non-tool `step` reaches
   `self.handle_step(step, state, context)`, which renders
   `prompt_name` against the context and calls `self.reasoner.generate(...)`.
5. **Return `AgentResult`** — `format_output(state)` normalizes
   everything into the one shape every caller (Supervisor, Orchestrator
   node, test harness) depends on. The caller never needs to know which
   concrete agent produced it.

## What every agent declares (class attributes, not methods)

| Attribute | Meaning |
|---|---|
| `name` | registry key convention: `<domain_noun>_agent` (e.g. `pricing_agent`) |
| `description` | one paragraph — feeds `registry.describe()` |
| `permissions` | `dict[str, bool]` — what this agent is allowed to do; enforced today by convention, later by the Guardrail Layer |
| `allowed_tools` | which `ToolManager.call(name, ...)` calls are legitimate |
| `prompt_name` | which `agent_layer/prompts/*.md` template `handle_step` renders |
| `default_plan` | static plan template (tool steps + one reasoning step) |
| `context_sections` | which `ContextBuilder` sections this agent needs (`None` = all) |

## What every agent overrides (methods)

- `override_plan(plan, user_query)` — fill in dynamic values only (optional).
- `handle_step(step, state, context)` — the one non-tool step; renders
  the prompt and calls the reasoner (required).
- Explicit write methods (e.g. `update_stock`, `apply_price_change`) —
  deliberately **not** part of `run()`. Mutating a marketplace is never
  a side effect of answering a question; see any existing agent's
  module docstring for why this stands in for a guardrail today.

## Registering a new agent

New agents register themselves via their domain's `register.py` (see
`agent_layer/registry/agent_registry.py`) — nothing in the Supervisor,
Orchestrator, or this SDK changes. Adding an agent is:

1. Write `<domain>/<name>_agent.py` following the contract above.
2. Add one line to `<domain>/register.py`.
3. Add one line to `orchestrator.py`'s `AGENT_NODE_TO_REGISTRY_KEY` if
   an existing graph node/intent should route to it.

No other file needs to change. That's the frozen part.

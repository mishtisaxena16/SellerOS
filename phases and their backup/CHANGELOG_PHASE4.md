# Phase 4 — Agent Transparency + AI Execution Timeline + Confidence

Scope: **frontend only**. No backend routes, schemas, connectors, Playwright
flows, or marketplace integrations were touched. No existing Phase 1–3
functionality was removed — every change is additive to `AgentConsole.tsx`
and `FloatingAI.tsx`, which still call the same `POST /chat` and
`POST /chat/approve` endpoints with the same request/response contract
(`frontend/src/api/chat.ts`, mirroring `backend/schema/chat.py`, is
unchanged).

## Why everything below is *inferred*, not invented

`ChatResponse` (`backend/schema/chat.py`) only returns:

```
response, intent, marketplace, awaiting_approval, thread_id,
guardrail_findings, unimplemented_intents
```

There is no agent name, confidence score, citation list, or step-by-step
trace coming from the backend today. Per the Phase 4 spec ("if backend
provides X, use it — otherwise infer intelligently"), every new UI surface
below is derived from the fields that already exist on `ChatResponse`,
using the *real* intent → agent routing table already defined server-side
in `backend/ai/orchestrator_layer/orchestrator.py`
(`INTENT_KEYWORDS` / `AGENT_FOR_INTENT`) and the agent keys registered in
`backend/ai/agent_layer/*/register.py`. If the backend ever starts sending
an explicit `agent_name` or `citations` field, the inference functions are
written to prefer that real data outright (see `inferAgent()` and the
`SourceList` docstring) — nothing needs to change in the calling
components.

## New files

All five are small, dependency-free, and each owns both its inference
logic (an exported pure function) and its rendering (a default-exported
component), so nothing is duplicated between `AgentConsole` and
`FloatingAI`.

- **`frontend/src/components/StatusBadge.tsx`**
  Single source of truth for "what state is this assistant turn in."
  Exports `ExchangeStatus` (`'pending' | 'completed' | 'requires_approval' |
  'blocked' | 'error'`) and `computeStatus()`, which reads
  `{ error, response, guardrailFindings, awaitingApproval }` — fields every
  `Exchange`/`Message` already carries. `computeStatus` is the shared input
  to `AgentTimeline`, `AgentBadge`, and `ConfidenceBadge`, so the four
  places status matters can never disagree with each other.
  Renders the "Completed / Requires Approval / Blocked by Guardrail /
  Error" colored badge from Phase 4 §7.

- **`frontend/src/components/AgentBadge.tsx`**
  `inferAgent(intent, status, agentName?)` — maps the primary detected
  intent to a display identity (name, emoji, color) for one of the 14
  specialized agents (Listing, Pricing, Inventory, Orders, Analytics,
  Forecasting, Profitability, Competitor, Campaign, Ads, SEO, Content,
  Seller Coach, Sustainability), falling back to Seller Coach exactly like
  `IntentRouter.select_agent()` does server-side. When `status === 'blocked'`
  it returns a synthetic **Policy Agent** identity instead, since a
  guardrail block means the specialized agent never actually ran —
  attributing the reply to it would be misleading.
  `inferResponseType(intent, status)` — maps intent to one of the eight
  response-type labels from Phase 4 §5 (Analysis, Recommendation,
  Prediction, Knowledge Retrieval, Action Plan, Troubleshooting,
  Information, Decision Support), with `Troubleshooting` forced for a
  blocked turn.
  Exports `AgentBadge` (icon + name pill) and `ResponseTypeChip`.

- **`frontend/src/components/ConfidenceBadge.tsx`**
  `computeConfidence()` — a deterministic (never random, per Phase 4 §3)
  score starting at 90 and adjusted by:
  - retrieval quality — intent count (penalty for `unknown`, small bonus
    for multiple resolved intents)
  - amount of evidence — response length
  - guardrail certainty — one penalty point per guardrail finding
  - completeness — one penalty per unimplemented intent, plus extra
    penalties for `blocked`/`requires_approval` outcomes
  Clamped to 30–98 and bucketed into High (≥85) / Medium (≥60) / Low (<60),
  matching the 95%/78%/53% examples in the spec.

- **`frontend/src/components/SourceList.tsx`**
  `inferSources(intent, marketplace)` — maps each detected intent to the
  knowledge domain it most likely drew on (Pricing Rules, Inventory
  Documents, Sales Analytics Data, Government Guidelines, etc.) and adds a
  marketplace-specific policy source (Amazon/Flipkart/Meesho Policies)
  when a marketplace is set, falling back to "SellerOS Knowledge Base"
  when nothing else matches. Renders the "Knowledge Sources" chip row from
  Phase 4 §4.

- **`frontend/src/components/AgentTimeline.tsx`**
  The per-turn execution trace from Phase 4 §1 (Understanding request →
  Selecting best agent → Running Guardrail checks → Searching Knowledge
  Fabric → Ranking retrieved knowledge → Generating response → Performing
  response validation → Ready). While `status === 'pending'` it animates
  through the steps on a fixed interval; the instant a real status lands
  it snaps to that outcome instead of continuing to fake progress:
  - `completed` — all 8 steps green, "Ready".
  - `requires_approval` — 7 steps green, final row shows "Awaiting your
    approval" in amber.
  - `blocked` — only the first 3 steps render, with "Running Guardrail
    checks" shown in red and a "Stopped — the guardrail layer blocked this
    request" note; later steps are never claimed to have happened.
  - `error` — similarly truncates at a generic mid-pipeline step with a
    "Stopped — the request failed" note, since a network/API failure
    doesn't tell us which internal stage broke.

- **`frontend/src/components/LoadingTimeline.tsx`**
  Phase 4 §6's rotating-caption loading indicator ("Thinking..." →
  "Selecting Agent..." → "Searching Knowledge..." → "Ranking
  Documents..." → "Preparing Response..."), replacing the old static
  "Thinking…" + spinner line. Used above `AgentTimeline` while a request
  is in flight.

## Modified files

- **`frontend/src/components/AgentConsole.tsx`**
  - `Exchange` gains `intent`, `marketplace`, `unimplementedIntents`
    (all already returned by `sendChatMessage`/`approveAction`, just not
    previously stored).
  - Header now shows a live "● Connected" indicator, a short session ID
    (Phase 4 §9), and the current agent badge once a response has landed.
  - Each pending turn renders `LoadingTimeline` + `AgentTimeline
    status="pending"` in place of the old plain "Thinking…" row.
  - Each completed turn renders `AgentTimeline` (final state) above the
    response, then a row of `AgentBadge` / `ResponseTypeChip` /
    `StatusBadge` / `ConfidenceBadge`, then the existing
    `ChatMessageContent` response body, then `SourceList` — all without
    touching the existing guardrail-findings banner, approval
    Approve/Reject flow, or retry-on-error UI, which are unchanged.

- **`frontend/src/components/FloatingAI.tsx`**
  - `Message` gains the same three new fields as `Exchange` above.
  - Header ("SellerOS AI") now shows Connected status, short session ID,
    and current agent inline (Phase 4 §9), replacing the old static
    "Live · connected to /chat" line.
  - AI message bubbles are restructured the same way as `AgentConsole`:
    `AgentTimeline` → agent/response-type/status/confidence badge row →
    response text → `SourceList`. User and system (error) bubbles are
    unchanged.
  - The bottom "sending" indicator now renders `LoadingTimeline` +
    `AgentTimeline status="pending"` instead of a static spinner line.

## Integration notes

- No API surface changed: both components still call the exact same
  `sendChatMessage` / `approveAction` / `getOrCreateSessionId` functions
  from `frontend/src/api/chat.ts`, unmodified.
- All new UI reuses existing design tokens from `frontend/src/index.css`
  (`--blue/green/purple/amber/red` and their `-soft` variants, `text-app`,
  `text-dim`, `text-faint`, `bg-elev`, `bg-surface`, `bg-hover`,
  `border-app`, `font-mono-app`, `.fade-in`, `.ai-pulse`) — no new CSS was
  added, so dark mode and existing theming keep working unchanged.
- `tsc --noEmit` passes with no errors under the project's strict
  TypeScript config (`strict`, `noUnusedLocals`, `noUnusedParameters`).
- Fully responsive: all new components use the same relative/`flex-wrap`
  patterns as the surrounding chat UI and were checked at the 320–384px
  widths `FloatingAI` already targets.

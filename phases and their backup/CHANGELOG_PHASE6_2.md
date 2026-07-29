# CHANGELOG — Phase 6.2: Execution Timeline UI

## Scope

Frontend-only. This phase visualizes the `execution_plan` Phase 6.1
already returns on `ChatResponse` — it does not add, change, or call
any backend logic, routing, or agent execution. No LangGraph, planner,
Seller Coach, Business Intelligence, mock data, Playwright, or
marketplace-API code was touched.

---

## Files Created

- `frontend/src/components/ExecutionStatusBadge.tsx`
  **Task 2 — Status Badges.**
  One badge per `ExecutionStepStatus` (`pending`, `running`,
  `completed`, `failed`, `skipped`), each with its own color, icon, and
  label, built from the same accent tokens (`text-accent-*` /
  `bg-accent-*-soft`) already used by `StatusBadge.tsx` /
  `ConfidenceBadge.tsx` — so it reads as part of the existing design
  system rather than a new one:
  - Pending — amber, `Clock`
  - Running — blue, `Loader2` (spinning + a subtle `animate-pulse`)
  - Completed — green, `CheckCircle2`
  - Failed — red, `XCircle`
  - Skipped — neutral (`text-faint`/`bg-hover` — no dedicated "gray"
    token exists in `index.css`, and both of these are already
    theme-aware for dark/light), `MinusCircle`
  - An unrecognized/future status falls back to the "Pending" look
    instead of crashing.

- `frontend/src/components/ExecutionTimeline.tsx`
  **Tasks 1, 3, 4, 5, 6, 8, 9 — the timeline itself.**
  - Props: `executionPlan?: ExecutionPlanStep[] | null`, optional
    `className`, optional `defaultExpanded` (defaults to `true` so the
    full plan is visible right away, matching the spec's "Expected
    Experience"; still fully collapsible afterwards).
  - **Renders `null` whenever `executionPlan` is missing or empty**
    (Task 6) — safe to render unconditionally from any caller.
  - Each row (Task 1): execution-order circle, agent icon (Task 3 —
    `agent_id → emoji` map: `analytics` 📈, `inventory` 📦, `pricing`
    💰, `marketing`/`ads` 📣, `listing` 📝, `policy` 🛡️, `seller_coach`
    🧠, unknown → 🤖), agent `display_name`, its planning `reason` as a
    truncated subtitle/tooltip, and an `ExecutionStatusBadge`.
  - **Execution order** (Task 4): steps are defensively re-sorted by
    `execution_order` before rendering (never assumes the backend order
    holds), numbered circles, and a small down-chevron between
    consecutive steps on desktop to read as a sequence.
  - **Collapsible** (Task 5): header button toggles
    `Execution Plan (N Agents)` ⇄ the full list, animated via a
    `grid-template-rows` 0fr↔1fr transition (not `display:none`), with
    the chevron rotating in sync.
  - **Responsive** (Task 8): the same rows are bordered/boxed
    "compact cards" by default (mobile), and flatten to a borderless
    vertical list (with the connecting chevrons) at `sm:` and above
    (desktop). Uses only the existing theme CSS variables, so dark mode
    is automatic — no new tokens were added.
  - **Animations** (Task 9): `fade-in` on mount (reusing the existing
    `.fade-in` keyframe from `index.css` — no new keyframes added),
    staggered per-row fade-in delay, chevron rotation and hover state
    on the collapse toggle, `transition-colors` on the status badge.
    Kept deliberately subtle/limited to those four spots, per the
    "don't overuse animations" instruction.
  - **Loading support** (Task 7): the component is a pure function of
    its `executionPlan` prop — if a future phase re-renders it with the
    same steps but updated `status` values (e.g. `pending` → `running`
    → `completed`), React updates those DOM nodes in place and
    `ExecutionStatusBadge`'s `transition-colors`/`animate-pulse` handle
    the visual change automatically. No polling, subscriptions, or
    backend calls were added here — nothing in this phase drives that
    update yet, by design.

---

## Files Modified

- `frontend/src/api/chat.ts`
  Added `ExecutionStepStatus` and `ExecutionPlanStep` types (mirroring
  `backend.schema.chat.ExecutionStepSchema` from Phase 6.1) and one new
  optional field on `ChatResponse`: `execution_plan?: ExecutionPlanStep[]`.
  Everything else in this file — `sendChatMessage`, `approveAction`,
  `getOrCreateSessionId`, every existing `ChatResponse` field — is
  unchanged.

- `frontend/src/components/AgentConsole.tsx`
  - `Exchange` gained one new optional field, `executionPlan?:
    ExecutionPlanStep[]`.
  - Both `send()` and `respondToApproval()` now also copy
    `result.execution_plan` onto the exchange — no other data flow
    changed.
  - Renders `<ExecutionTimeline executionPlan={ex.executionPlan} />`
    **above** the AI response bubble (Task 6's "Position: Above AI
    response") whenever a plan is present; renders nothing otherwise.
    Everything below it (the actual response card, badges, guardrail
    findings, approval prompt) is untouched.

- `frontend/src/components/FloatingAI.tsx`
  - `Message` gained the same new optional field, `executionPlan?:
    ExecutionPlanStep[]`.
  - `send()` and `respondToApproval()` now also copy
    `result.execution_plan` onto the message.
  - Each message is now wrapped in one small outer container so an
    `ExecutionTimeline` row can sit above an `ai` message's bubble row;
    the bubble markup itself (avatar, card, badges, response text,
    guardrail/approval UI) is unchanged, just nested one level deeper
    for this purpose.

---

## Integration Notes

- **Additive-only data flow.** `ChatResponse.execution_plan` is
  optional in the frontend type and only ever read, never required —
  a backend response without it (or an older cached one) still renders
  exactly as it did before this phase.
- **Where the timeline actually appears.** Per Task 6, it's wired into
  both surfaces the spec named: `AgentConsole.tsx` (used by every
  domain page's chat surface — Product Studio, Marketing Hub,
  Sustainability, Seller Coach) and `FloatingAI.tsx` (the floating
  assistant). No other page or component was touched.
- **Honest limitation, carried over from what Phase 6.1 actually
  ships:** today, `execution_plan` and the final `response` text arrive
  in the *same* HTTP response (`Supervisor.handle()` computes the plan
  and then awaits the full orchestrator run before returning both
  together — see Phase 6.1's changelog). So in practice the timeline
  currently appears **at the same moment as** the response, not
  strictly *before* it, even though it's positioned above it and is
  built to support that once the backend streams the plan separately.
  This phase does not change that backend behavior (out of scope —
  "Do NOT modify backend logic"); `ExecutionTimeline`'s pure,
  prop-driven design (Task 7) means no rework is needed here when that
  streaming lands — only the *timing* of when its prop updates will
  change, not the component itself.
- **No new CSS added.** Every color, spacing, radius, and animation
  used already existed in `index.css` (`text-accent-*`, `bg-accent-*`,
  `text-faint`, `bg-hover`, `bg-surface`, `bg-elev`, `border-app`,
  `.fade-in`) or is a stock Tailwind v4 utility (`transition-[grid-template-rows]`,
  `animate-spin`, `animate-pulse`, `rotate-180`). Dark/light mode work
  automatically since none of it is hardcoded.
- **Verified:** `npx tsc --noEmit` passes with zero errors in every
  file this phase touches or created (strict mode, matching the
  project's existing `tsconfig.json`) — the only compiler message is a
  pre-existing, unrelated `tsconfig.json` deprecation notice about
  `baseUrl` that was already present before this phase and is not
  caused by anything changed here.

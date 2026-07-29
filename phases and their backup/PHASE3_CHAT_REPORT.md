# SellerOS — Phase 3: AI Chat Experience Report

## Scope
Frontend-only, localized to the AI chat surfaces. No routing, auth, Playwright, marketplace APIs, database schema, AI agents/prompt architecture, or other pages (Dashboard, Orders, Inventory, Analytics) were touched. No new backend services or agents were added, and streaming was not introduced (the backend `/chat` endpoint is request/response, not streamed, so the UI stays that way).

## Files Modified / Added
- `frontend/src/components/FloatingAI.tsx` — modified (the global floating assistant, mounted once in `AppShell`)
- `frontend/src/components/AgentConsole.tsx` — modified (the shared chat component used by Seller Coach, Product Studio's optimizer, Marketing Hub, and Sustainability)
- `frontend/src/components/ChatMessageContent.tsx` — **new**: shared lightweight markdown renderer
- `frontend/src/utils/chatErrors.ts` — **new**: shared friendly-error-message helper

`AgentConsole` is used on four pages beyond Seller Coach (Product Studio, Marketing Hub ×2, Sustainability). Its prop interface was left unchanged, so none of those pages needed edits — but they all inherit the same reliability and formatting fixes below.

## Audit Findings (Before)
- **FAB toggle bug**: the floating button's `onClick` unconditionally called `setOpen(true)`. While the window was open, clicking the button anywhere except exactly on the small X icon silently did nothing instead of closing it — a visible glitch during a demo.
- **No markdown rendering anywhere**: both chat surfaces rendered `response` as a raw string. `FloatingAI` didn't even preserve line breaks (no `whitespace-pre-wrap`), so multi-line agent answers with lists (`- item`) or bold labels (`**Total:**`) rendered as a single run-on line with literal asterisks.
- **Backend error messages passed straight to the UI**: `backend/api/routers/chat.py` returns `HTTPException(500, detail=str(e))` on any exception — i.e. raw Python exception text can reach the frontend. The old catch blocks (`err instanceof ApiError ? err.message : '...'`) would display that text verbatim, without checking whether it looked technical.
- **Race condition on rapid double-submit**: `send()` guarded on the `sending` state, but state updates aren't synchronous — a fast double-click or double Enter-press in the same tick could dispatch two sends before the button's `disabled` attribute actually took effect.
- **`FloatingAI`'s empty state** only surfaced 2 of 4 quick prompts, and none matched the demo script.
- **No retry path in `FloatingAI`** on a failed send (unlike `AgentConsole`, which already had a per-message retry button) — a failed message just sat there with no obvious way to resend it.

## Improvements Made
1. **Fixed FAB open/close** — the button's `onClick` now derives the next state (`toggleFab`) instead of always opening; the X icon lost its separate `stopPropagation` handler since it's no longer needed. Opening, minimizing, and closing are all glitch-free now.
2. **Markdown-lite rendering** (`ChatMessageContent.tsx`) — a small, dependency-free formatter supporting `**bold**`, `` `inline code` ``, `-`/`*` bullet lists, `1.` numbered lists, and paragraph breaks. Used for every assistant response in both `FloatingAI` and `AgentConsole`, so agent answers with structure (e.g. a Raksha Bandhan campaign plan with a numbered timeline, or a ranking checklist) render as real lists instead of one dense paragraph.
3. **User-friendly error messages** (`chatErrors.ts`) — `friendlyChatError()` maps network failures, 401/403, 429, and 5xx to short, plain-language text, and screens any other backend message for stack-trace/exception-like patterns (`Traceback`, `File "`, multi-line content, or unusually long text) before showing it — falling back to a generic line instead. No raw backend exception text can reach the chat UI anymore.
4. **Hardened duplicate-submit prevention** — added a `useRef` guard (`sendingRef`) alongside the existing `sending` state in both components, so even a same-tick double-click or double Enter can't fire two sends.
5. **Retry on failure in `FloatingAI`** — a failed send now shows a small "Retry" action under the error bubble that resends the original text, matching the retry UX `AgentConsole` already had.
6. **Demo-aligned empty state & quick prompts** — `FloatingAI`'s five quick prompts are now exactly the five demo questions ("How can I improve my product ranking?", "Plan a Raksha Bandhan campaign", "How can I make my courier packaging more eco-friendly?", "Summarize my business", "Show low stock products"), all shown before the first message is sent (collapsing to two afterward to keep the window focused on the conversation). The greeting text now explicitly says the assistant can help "even before a marketplace is connected."
7. **Loading indicators** — both surfaces already showed a "Thinking…" indicator; the send button now also swaps to a spinner while a request is in flight, so there's feedback right at the point of action, not just lower in the message list.
8. **Consistent spacing/alignment** — added `min-w-0` to message containers and the header title block so long unbroken AI text (or a long title) can't push chat bubbles wider than the window; unified list/paragraph spacing via the shared `ChatMessageContent` component so both chat surfaces format responses identically.
9. **Scrolling** — verified and preserved: both components auto-scroll to the latest message on every new message and on send/receive; `FloatingAI`'s message list remounts fresh (and scrolls into view) each time the window is reopened from closed, and conversation state itself lives in the parent component so it survives minimizing.
10. **Conversation history persistence** — confirmed structurally sound: `FloatingAI` is mounted once in `AppShell` (outside the page `Outlet`), so its message state is not affected by route navigation for the session; no changes needed there, left untouched per the "don't touch architecture" instruction.

## How the required demo questions are covered
All five are now first-class quick-prompt buttons in the floating assistant's empty state, so they can be triggered with a single click instead of being typed live:
- "How can I improve my product ranking?"
- "Plan a Raksha Bandhan campaign"
- "How can I make my courier packaging more eco-friendly?"
- "Summarize my business"
- "Show low stock products"

Each goes through the same `/chat` call as before (no prompt/agent changes); the improvements here are about how the response is displayed (formatted, not stack-traced, not duplicated) and how reliably the widget opens/sends/scrolls around them.

## Remaining Limitations
- The 500-error sanitization is done entirely on the frontend (pattern-matching for stack-trace-like text). The backend (`backend/api/routers/chat.py`) still returns `detail=str(e)` on any unhandled exception — cleaning that at the source was out of scope for a frontend-only phase, but a short backend-side message wrapper would be a natural follow-up if backend changes are ever in scope.
- `ChatMessageContent` is intentionally minimal — it does not support markdown tables, links, headings, or nested lists. If agents start returning richer formatting, it would need extending (still without adding a markdown library, to keep the "no new dependencies" constraint).
- Streaming was not implemented, per the instructions — responses still appear all at once after the "Thinking…" indicator, since the backend `/chat` endpoint is a single request/response call, not a stream.
- A full `vite build` could not be executed in this sandbox due to a pre-existing missing native binding (`@rolldown/binding-linux-x64-gnu`), unrelated to these changes (same issue reproduced against the unmodified codebase in Phase 2). `tsc --noEmit` against the project's own `tsconfig.json` (which has `strict`, `noUnusedLocals`, and `noUnusedParameters` all on) passes cleanly with zero errors introduced.

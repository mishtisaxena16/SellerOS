// ============================================================================
// SellerOS — Phase 7.7C: AI Session & UI State Reset
// ============================================================================
// A small, frontend-only signal that "Reset Demo" also broadcasts to every
// mounted AI surface (FloatingAI, and anything sharing its execution-results
// rendering) so each can clear its own local React state and regenerate a
// fresh demo session id — with no backend call, no RAG re-index, and no
// change to stored knowledge. This is intentionally separate from
// demo/demoState.ts / demo/demoReset.ts (Phase 7.7A/7.7B): those own the
// Orders/Inventory/Listings/Business Intelligence/seller/scenario dataset,
// not per-component AI chat/UI state, which only ever lives in memory inside
// the components themselves (FloatingAI's messages, execution results,
// open/minimized state, etc.) — there's nothing dataset-shaped to store here,
// only an event + a fresh id for whichever component asks for one.
// ============================================================================

/** Generates a brand-new, purely-client-side AI session identifier. Same
 * fallback pattern FloatingAI.tsx already used for its own session id. */
export function generateAiSessionId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `ai-session-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

type AiSessionResetListener = (sessionId: string) => void
const listeners = new Set<AiSessionResetListener>()

/** Subscribe to AI session resets. Returns an unsubscribe function — safe
 * to call from a React effect. */
export function subscribeToAiSessionReset(listener: AiSessionResetListener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

/**
 * Resets the frontend AI session: generates a fresh session id and notifies
 * every subscriber so it can clear its own conversation history, pending
 * messages, loading/typing state, execution timeline, result cards, and
 * seller-coach summary — restoring the "just opened SellerOS for the first
 * time" state. No API call, no RAG re-index, no stored-knowledge change;
 * this only touches in-memory UI state already owned by each component.
 */
export function resetAiSession(): string {
  const newSessionId = generateAiSessionId()
  listeners.forEach((listener) => listener(newSessionId))
  return newSessionId
}

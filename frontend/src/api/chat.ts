import { apiRequest } from './client'

// Mirrors backend.schema.chat exactly.
export interface ChatResponse {
  response: string
  intent: string[]
  marketplace: string | null
  awaiting_approval: boolean
  thread_id: string | null
  guardrail_findings: string[]
  unimplemented_intents: string[]
}

export function sendChatMessage(message: string, sessionId: string) {
  return apiRequest<ChatResponse>('/chat', {
    method: 'POST',
    body: { message, session_id: sessionId },
  })
}

export function approveAction(threadId: string, approved: boolean, sessionId?: string) {
  return apiRequest<ChatResponse>('/chat/approve', {
    method: 'POST',
    body: { thread_id: threadId, approved, session_id: sessionId },
  })
}

// One session id per (browser tab, page). Pages that want an isolated
// conversation (Product Studio's optimizer vs. Seller Coach vs. the
// floating assistant) pass a distinct `key` so supervisor.handle()'s
// per-session memory doesn't blend unrelated contexts together.
// Defaults to the shared floating-assistant session for backwards
// compatibility with existing callers.
export function getOrCreateSessionId(key: string = 'default'): string {
  const storageKey = `sellerOS.chatSessionId.${key}`
  let id = window.sessionStorage.getItem(storageKey)
  if (!id) {
    id = (crypto as { randomUUID?: () => string }).randomUUID
      ? crypto.randomUUID()
      : `sess-${Date.now()}-${Math.random().toString(36).slice(2)}`
    window.sessionStorage.setItem(storageKey, id)
  }
  return id
}

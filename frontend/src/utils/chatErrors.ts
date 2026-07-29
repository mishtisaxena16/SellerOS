import { ApiError } from '../api/client'

// Turns a failed /chat or /chat/approve call into a short, user-facing
// message — used by every chat surface (FloatingAI, AgentConsole) so a
// backend 500 never puts a raw Python exception or stack trace in front
// of someone during a demo. Backend messages that read as clean, short
// text (e.g. "No marketplace connected") still pass through as-is; only
// technical-looking output gets swapped for a generic, friendly line.
export function friendlyChatError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 0) {
      return "Can't reach the AI assistant right now. Check your connection and try again."
    }
    if (err.status === 401 || err.status === 403) {
      return 'Your session has expired — please sign in again to keep chatting.'
    }
    if (err.status === 429) {
      return "You're sending messages a little fast — give it a moment and try again."
    }
    if (err.status >= 500) {
      return 'The AI assistant hit a snag processing that. Try rephrasing, or ask again in a moment.'
    }

    const message = err.message ?? ''
    const looksTechnical =
      /traceback|exception|stack|File "|at \w+[.:]\w+|^\s*\{|^\s*\[/i.test(message) ||
      message.includes('\n') ||
      message.length > 220

    if (message && !looksTechnical) return message
    return 'Something went wrong on that request. Please try again.'
  }
  return 'Something went wrong reaching the AI assistant. Please try again.'
}

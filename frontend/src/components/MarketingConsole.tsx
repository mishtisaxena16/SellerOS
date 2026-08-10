import { useCallback, useRef, useState } from 'react'
import { Loader2, Send, Sparkles, type LucideIcon } from 'lucide-react'
import ChatMessageContent from './ChatMessageContent'
import { sendChatMessage, type ChatMessage } from '../api/chat'
import { friendlyChatError } from '../utils/chatErrors'

// =========================================================
// MarketingConsole
//
// A focused chat surface for a single Marketing Hub panel
// (Campaign Strategy / Ads / SEO / Content). This is the plain
// "describe what you want, get real copy/strategy back" console
// the Marketing Hub screenshot shows — icon + title + description,
// an empty-state hint, a couple of quick-start prompts, and a
// single input+send row. It talks to the same real /chat endpoint
// every other agent surface uses (via sendChatMessage) so replies
// come from the actual marketing agents, not invented copy.
//
// Deliberately does NOT render an execution timeline, agent result
// cards, or a seller-coach-style summary — those belong to the
// multi-agent execution console (AgentConsole/ExecutionResultsPanel),
// which is a different surface with a different job. Marketing Hub
// just wants strategy and copy back from a single conversation.
// =========================================================

interface QuickPrompt {
  label: string
  prompt: string
}

interface MarketingConsoleProps {
  title: string
  description: string
  icon: LucideIcon
  iconColor: string
  sessionKey: string
  placeholder: string
  emptyHint?: string
  quickPrompts?: QuickPrompt[]
}

export default function MarketingConsole({
  title,
  description,
  icon: Icon,
  iconColor,
  sessionKey,
  placeholder,
  emptyHint,
  quickPrompts,
}: MarketingConsoleProps) {
  // One stable session id per panel (per mount) — keeps each tab's
  // conversation with the marketing agents independent of the others.
  const sessionIdRef = useRef(sessionKey)

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const send = useCallback(
    async (content: string) => {
      const trimmed = content.trim()
      if (!trimmed || sending) return

      const userMessage: ChatMessage = {
        id: `local-${Date.now()}`,
        role: 'user',
        content: trimmed,
        createdAt: new Date().toISOString(),
      }
      setMessages(prev => [...prev, userMessage])
      setInput('')
      setSending(true)
      setError(null)

      try {
        const response = await sendChatMessage({ sessionId: sessionIdRef.current, content: trimmed })
        setMessages(prev => [
          ...prev,
          {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: response.response,
            createdAt: new Date().toISOString(),
          },
        ])
      } catch (err) {
        setError(friendlyChatError(err))
      } finally {
        setSending(false)
      }
    },
    [sending]
  )

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      send(input)
    },
    [input, send]
  )

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-start gap-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${iconColor}`}>
          <Icon size={17} />
        </div>
        <div>
          <div className="text-[14px] font-semibold text-app">{title}</div>
          <div className="text-[12.5px] text-dim">{description}</div>
        </div>
      </div>

      <div className="rounded-lg border border-app bg-surface min-h-[200px] max-h-[360px] overflow-y-auto p-4 space-y-2.5">
        {messages.length === 0 ? (
          emptyHint ? (
            <div className="h-full min-h-[168px] flex items-center justify-center text-center">
              <p className="text-[12.5px] text-faint max-w-sm">{emptyHint}</p>
            </div>
          ) : null
        ) : (
          messages.map(message => (
            <div
              key={message.id}
              className={`text-[12.5px] leading-relaxed rounded-lg px-3 py-2 ${
                message.role === 'user' ? 'bg-accent-blue-soft text-app ml-6' : 'bg-elev text-app mr-1'
              }`}
            >
              <ChatMessageContent text={message.content} />
            </div>
          ))
        )}
        {sending && (
          <div className="flex items-center gap-1.5 text-[11.5px] text-faint px-0.5">
            <Loader2 size={12} className="animate-spin" />
            Thinking…
          </div>
        )}
        {error && <div className="text-[11.5px] text-accent-red px-0.5">{error}</div>}
      </div>

      {quickPrompts && quickPrompts.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {quickPrompts.map(qp => (
            <button
              key={qp.label}
              type="button"
              disabled={sending}
              onClick={() => send(qp.prompt)}
              className="flex items-center gap-1.5 text-[12px] font-medium text-dim border border-app rounded-lg px-3 py-1.5 hover:bg-hover hover:text-app transition-colors disabled:opacity-50"
            >
              <Sparkles size={11} className="text-accent-blue" />
              {qp.label}
            </button>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder={placeholder}
          disabled={sending}
          className="flex-1 min-w-0 text-[13px] bg-surface border border-app rounded-lg px-3 py-2.5 text-app placeholder:text-faint outline-none focus:border-app-hover disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          aria-label="Send message"
          className="w-10 h-10 flex-shrink-0 rounded-lg bg-accent-blue text-white flex items-center justify-center disabled:opacity-40 hover:opacity-90 transition-opacity"
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  )
}

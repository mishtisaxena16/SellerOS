import { useEffect, useRef, useState } from 'react'
import { Sparkles, X, Send, Minimize2, AlertTriangle, Check, Loader2, RotateCcw } from 'lucide-react'
import { sendChatMessage, approveAction, getOrCreateSessionId } from '../api/chat'
import type { ExecutionPlanStep } from '../api/chat'
import { friendlyChatError } from '../utils/chatErrors'
import ChatMessageContent from './ChatMessageContent'
import AgentTimeline from './AgentTimeline'
import ExecutionTimeline from './ExecutionTimeline'
import AgentBadge, { ResponseTypeChip, inferAgent, inferResponseType } from './AgentBadge'
import ConfidenceBadge, { computeConfidence } from './ConfidenceBadge'
import SourceList, { inferSources } from './SourceList'
import StatusBadge, { computeStatus } from './StatusBadge'
import LoadingTimeline from './LoadingTimeline'

interface Message {
  role: 'user' | 'ai' | 'system'
  text: string
  intent?: string[]
  marketplace?: string | null
  guardrailFindings?: string[]
  unimplementedIntents?: string[]
  awaitingApproval?: boolean
  threadId?: string | null
  resolved?: 'approved' | 'rejected'
  // Only set on a failed-send system message — lets the retry button
  // resend the exact user text that failed, instead of making them retype it.
  retryText?: string
  // Phase 6.1's execution_plan, shown above the response by
  // ExecutionTimeline (Phase 6.2, Task 6).
  executionPlan?: ExecutionPlanStep[]
}

// Demo-aligned prompts: these double as the "must work cleanly" questions
// for the live walkthrough, so the empty state itself doubles as a rehearsal
// of the demo script. Kept to five — enough to be useful, not so many the
// widget feels cluttered at 320-384px wide.
const QUICK_PROMPTS = [
  'How can I improve my product ranking?',
  'Plan a Raksha Bandhan campaign',
  'How can I make my courier packaging more eco-friendly?',
  'Summarize my business',
  'Show low stock products',
]

export default function FloatingAI() {
  const [open, setOpen] = useState(false)
  const [minimized, setMinimized] = useState(false)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'ai',
      text: "Hi! I'm your SellerOS AI assistant. Ask me about rankings, campaigns, packaging, your business numbers, or inventory — I can help even before a marketplace is connected.",
    },
  ])
  const scrollRef = useRef<HTMLDivElement>(null)
  const sessionId = useRef(getOrCreateSessionId())
  // A ref mirror of `sending` so double-clicks or double Enter-presses that
  // land in the same tick (before React re-renders the disabled button)
  // can't both slip through — state alone isn't synchronous enough for that.
  const sendingRef = useRef(false)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  const send = async (text: string) => {
    const msg = text.trim()
    if (!msg || sendingRef.current) return
    sendingRef.current = true
    setMessages(prev => [...prev, { role: 'user', text: msg }])
    setInput('')
    setSending(true)
    try {
      const result = await sendChatMessage(msg, sessionId.current)
      setMessages(prev => [
        ...prev,
        {
          role: 'ai',
          text: result.response,
          intent: result.intent,
          marketplace: result.marketplace,
          guardrailFindings: result.guardrail_findings,
          unimplementedIntents: result.unimplemented_intents,
          awaitingApproval: result.awaiting_approval,
          threadId: result.thread_id,
          executionPlan: result.execution_plan,
        },
      ])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', text: friendlyChatError(err), retryText: msg }])
    } finally {
      setSending(false)
      sendingRef.current = false
    }
  }

  const respondToApproval = async (index: number, approved: boolean) => {
    const target = messages[index]
    if (!target.threadId || sendingRef.current) return
    sendingRef.current = true
    setSending(true)
    setMessages(prev => prev.map((m, i) => (i === index ? { ...m, resolved: approved ? 'approved' : 'rejected' } : m)))
    try {
      const result = await approveAction(target.threadId, approved, sessionId.current)
      setMessages(prev => [
        ...prev,
        {
          role: 'ai',
          text: result.response,
          intent: result.intent,
          marketplace: result.marketplace,
          guardrailFindings: result.guardrail_findings,
          unimplementedIntents: result.unimplemented_intents,
          awaitingApproval: result.awaiting_approval,
          threadId: result.thread_id,
          executionPlan: result.execution_plan,
        },
      ])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', text: friendlyChatError(err) }])
    } finally {
      setSending(false)
      sendingRef.current = false
    }
  }

  // Single source of truth for what the FAB does next, based on current
  // state rather than always "open" — previously the button's own onClick
  // unconditionally called setOpen(true), so clicking it while the window
  // was already open (anywhere but exactly on the X icon) silently did
  // nothing instead of closing the widget.
  const toggleFab = () => {
    if (open && !minimized) {
      setOpen(false)
    } else {
      setOpen(true)
      setMinimized(false)
    }
  }

  const hasStarted = messages.length > 1
  const lastAgentMessage = [...messages].reverse().find(m => m.role === 'ai')
  const lastStatus = lastAgentMessage ? computeStatus({ response: lastAgentMessage.text, guardrailFindings: lastAgentMessage.guardrailFindings, awaitingApproval: lastAgentMessage.awaitingApproval }) : 'completed'
  const currentAgentInfo = inferAgent(lastAgentMessage?.intent, lastStatus)
  const shortSessionId = sessionId.current.replace(/-/g, '').slice(0, 8)

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {/* Chat window */}
      {open && !minimized && (
        <div className="fade-in w-80 sm:w-96 bg-elev rounded-2xl shadow-app border border-app overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-primary to-purple-500 flex-shrink-0">
            <div className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
              <Sparkles size={14} className="text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[13px] font-semibold text-white">SellerOS AI</div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="w-1.5 h-1.5 rounded-full bg-green-300 ai-pulse" />
                <span className="text-[11px] text-white/70">Connected</span>
                <span className="text-[11px] text-white/40">·</span>
                <span className="text-[11px] text-white/70 font-mono-app" title={sessionId.current}>{shortSessionId}</span>
                {hasStarted && (
                  <>
                    <span className="text-[11px] text-white/40">·</span>
                    <span className="text-[11px] text-white/85 truncate">{currentAgentInfo.emoji} {currentAgentInfo.name}</span>
                  </>
                )}
              </div>
            </div>
            <button type="button" onClick={() => setMinimized(true)} aria-label="Minimize chat" className="text-white/60 hover:text-white transition-colors flex-shrink-0">
              <Minimize2 size={14} />
            </button>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close chat" className="text-white/60 hover:text-white transition-colors flex-shrink-0">
              <X size={14} />
            </button>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="h-80 overflow-y-auto p-4 space-y-3 bg-app" aria-live="polite">
            {messages.map((m, i) => (
              <div key={i} className="space-y-1.5">
                {m.role === 'ai' && !!m.executionPlan?.length && (
                  <div className="pl-8">
                    <ExecutionTimeline executionPlan={m.executionPlan} />
                  </div>
                )}
                <div className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {m.role === 'ai' && (
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                    <Sparkles size={10} className="text-white" />
                  </div>
                )}
                {m.role === 'system' && (
                  <div className="w-6 h-6 rounded-full bg-accent-red-soft flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                    <AlertTriangle size={11} className="text-accent-red" />
                  </div>
                )}
                <div className="max-w-[88%] min-w-0">
                  {m.role === 'ai' ? (
                    <div className="px-3 py-2 rounded-xl bg-elev shadow-sm border border-app">
                      <AgentTimeline status={computeStatus({ response: m.text, guardrailFindings: m.guardrailFindings, awaitingApproval: m.awaitingApproval })} />
                      {(() => {
                        const status = computeStatus({ response: m.text, guardrailFindings: m.guardrailFindings, awaitingApproval: m.awaitingApproval })
                        const agent = inferAgent(m.intent, status)
                        const responseType = inferResponseType(m.intent, status)
                        const confidence = computeConfidence({
                          responseLength: m.text.length,
                          intentCount: m.intent?.length ?? 0,
                          guardrailFindingsCount: m.guardrailFindings?.length ?? 0,
                          unimplementedCount: m.unimplementedIntents?.length ?? 0,
                          status,
                        })
                        const sources = inferSources(m.intent, m.marketplace)
                        return (
                          <>
                            <div className="flex items-center flex-wrap gap-1 my-1.5">
                              <AgentBadge agent={agent} />
                              <ResponseTypeChip type={responseType} />
                              <StatusBadge status={status} />
                              <ConfidenceBadge confidence={confidence} />
                            </div>
                            <div className="text-[12.5px] leading-relaxed text-dim">
                              <ChatMessageContent text={m.text} />
                            </div>
                            <SourceList sources={sources} />
                          </>
                        )
                      })()}
                    </div>
                  ) : (
                    <div className={`px-3 py-2 rounded-xl text-[12.5px] leading-relaxed ${
                      m.role === 'system'
                        ? 'bg-accent-red-soft text-accent-red border border-app'
                        : 'bg-primary text-white'
                    }`}>
                      {m.text}
                    </div>
                  )}

                  {m.role === 'system' && m.retryText && (
                    <button
                      type="button"
                      onClick={() => send(m.retryText!)}
                      disabled={sending}
                      className="mt-1 text-[11px] font-medium text-accent-blue flex items-center gap-1 disabled:opacity-50"
                    >
                      <RotateCcw size={11} /> Retry
                    </button>
                  )}

                  {/* Guardrail findings */}
                  {!!m.guardrailFindings?.length && (
                    <div className="mt-1.5 px-2.5 py-1.5 rounded-lg bg-accent-amber-soft border border-app text-[11px] text-accent-amber flex items-start gap-1.5">
                      <AlertTriangle size={12} className="flex-shrink-0 mt-0.5" />
                      <span>{m.guardrailFindings.join(' · ')}</span>
                    </div>
                  )}

                  {/* Human-in-the-loop approval prompt */}
                  {m.awaitingApproval && m.threadId && !m.resolved && (
                    <div className="mt-2 p-2.5 rounded-lg border border-app bg-surface">
                      <div className="text-[11px] text-faint mb-2">This action needs your approval before it runs.</div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          disabled={sending}
                          onClick={() => respondToApproval(i, true)}
                          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-accent-green-soft text-accent-green text-[12px] font-medium rounded-md transition-colors disabled:opacity-50"
                        >
                          <Check size={12} /> Approve
                        </button>
                        <button
                          type="button"
                          disabled={sending}
                          onClick={() => respondToApproval(i, false)}
                          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-accent-red-soft text-accent-red text-[12px] font-medium rounded-md transition-colors disabled:opacity-50"
                        >
                          <X size={12} /> Reject
                        </button>
                      </div>
                    </div>
                  )}
                  {m.resolved && (
                    <div className={`mt-1.5 text-[11px] ${m.resolved === 'approved' ? 'text-accent-green' : 'text-accent-red'}`}>
                      {m.resolved === 'approved' ? '✓ Approved' : '✕ Rejected'}
                    </div>
                  )}
                </div>
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                  <Sparkles size={10} className="text-white" />
                </div>
                <div className="px-3 py-2 rounded-xl bg-elev shadow-sm border border-app">
                  <LoadingTimeline className="mb-2" />
                  <AgentTimeline status="pending" />
                </div>
              </div>
            )}
          </div>

          {/* Quick prompts — full set shown until the first message is sent,
              then collapsed to the first two so the window stays mostly
              about the conversation rather than the suggestions. */}
          <div className="px-3 py-2 flex gap-1.5 flex-wrap border-t border-app flex-shrink-0">
            {(hasStarted ? QUICK_PROMPTS.slice(0, 2) : QUICK_PROMPTS).map(q => (
              <button key={q} type="button" onClick={() => send(q)} disabled={sending} className="text-[11px] px-2 py-1 bg-hover hover:text-accent-blue text-dim rounded-md transition-colors truncate max-w-[160px] border border-app disabled:opacity-50">
                {q}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="flex items-center gap-2 px-3 py-3 border-t border-app flex-shrink-0">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send(input)}
              placeholder="Ask anything…"
              aria-label="Ask the AI assistant"
              disabled={sending}
              className="input-app flex-1 text-[13px] px-3 py-2 disabled:opacity-60"
            />
            <button
              type="button"
              onClick={() => send(input)}
              disabled={sending || !input.trim()}
              aria-label="Send message"
              className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white hover:bg-primary-hover transition-colors flex-shrink-0 disabled:opacity-50"
            >
              {sending ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
            </button>
          </div>
        </div>
      )}

      {/* FAB */}
      <button
        type="button"
        onClick={toggleFab}
        aria-label={open && !minimized ? 'Close AI assistant' : 'Open AI assistant'}
        className={`w-14 h-14 rounded-2xl shadow-xl flex items-center justify-center transition-all duration-200 ${
          open && !minimized ? 'bg-gray-800' : 'bg-gradient-to-br from-primary to-purple-500'
        } hover:scale-105 active:scale-95`}
      >
        {open && !minimized
          ? <X size={20} className="text-white" />
          : <Sparkles size={22} className="text-white" />
        }
      </button>
    </div>
  )
}

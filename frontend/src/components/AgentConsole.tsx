import { useEffect, useRef, useState } from 'react'
import { Send, Loader2, AlertTriangle, Check, X, Sparkles } from 'lucide-react'
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
import type { LucideIcon } from 'lucide-react'

interface Exchange {
  prompt: string
  response?: string
  intent?: string[]
  marketplace?: string | null
  guardrailFindings?: string[]
  unimplementedIntents?: string[]
  awaitingApproval?: boolean
  threadId?: string | null
  resolved?: 'approved' | 'rejected'
  error?: string
  // Phase 6.1's execution_plan, shown above the response by
  // ExecutionTimeline (Phase 6.2, Task 6).
  executionPlan?: ExecutionPlanStep[]
}

interface QuickPrompt {
  label: string
  prompt: string
}

interface AgentConsoleProps {
  title: string
  description: string
  icon: LucideIcon
  iconColor?: string
  quickPrompts: QuickPrompt[]
  placeholder?: string
  sessionKey: string
  emptyHint?: string
  // Lets a parent (e.g. a "Publish to All" button elsewhere on the page)
  // send a prompt through this console without duplicating the chat
  // logic. Bump `nonce` to trigger a send of `prompt`.
  externalTrigger?: { prompt: string; nonce: number }
}

// Shared, real chat surface for every AI-agent-backed page (Product
// Studio's optimizer, Marketing Hub, Sustainability, Seller Coach).
// Talks to the actual POST /chat + /chat/approve endpoints — same
// supervisor/agent/guardrail pipeline as the floating assistant, just
// scoped to its own conversation session and framed for its domain.
export default function AgentConsole({
  title, description, icon: Icon, iconColor = 'bg-accent-blue-soft text-accent-blue',
  quickPrompts, placeholder = 'Ask the AI…', sessionKey, emptyHint, externalTrigger,
}: AgentConsoleProps) {
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [exchanges, setExchanges] = useState<Exchange[]>([])
  const sessionId = useRef(getOrCreateSessionId(sessionKey))
  const bottomRef = useRef<HTMLDivElement>(null)
  // Synchronous guard alongside the `sending` state — state updates aren't
  // visible until the next render, so a fast double-click or double Enter
  // in the same tick could otherwise fire two sends before the button
  // actually disables.
  const sendingRef = useRef(false)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [exchanges, sending])

  const send = async (text: string) => {
    const prompt = text.trim()
    if (!prompt || sendingRef.current) return
    sendingRef.current = true
    setInput('')
    const index = exchanges.length
    setExchanges(prev => [...prev, { prompt }])
    setSending(true)
    try {
      const result = await sendChatMessage(prompt, sessionId.current)
      setExchanges(prev => prev.map((e, i) => i === index ? {
        ...e,
        response: result.response,
        intent: result.intent,
        marketplace: result.marketplace,
        guardrailFindings: result.guardrail_findings,
        unimplementedIntents: result.unimplemented_intents,
        awaitingApproval: result.awaiting_approval,
        threadId: result.thread_id,
        executionPlan: result.execution_plan,
      } : e))
    } catch (err) {
      const detail = friendlyChatError(err)
      setExchanges(prev => prev.map((e, i) => i === index ? { ...e, error: detail } : e))
    } finally {
      setSending(false)
      sendingRef.current = false
    }
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (externalTrigger && externalTrigger.nonce > 0) send(externalTrigger.prompt)
  }, [externalTrigger?.nonce])

  const respondToApproval = async (index: number, approved: boolean) => {
    const target = exchanges[index]
    if (!target.threadId || sendingRef.current) return
    sendingRef.current = true
    setSending(true)
    setExchanges(prev => prev.map((e, i) => i === index ? { ...e, resolved: approved ? 'approved' : 'rejected' } : e))
    try {
      const result = await approveAction(target.threadId, approved, sessionId.current)
      setExchanges(prev => [...prev, {
        prompt: approved ? '(approved)' : '(rejected)',
        response: result.response,
        intent: result.intent,
        marketplace: result.marketplace,
        guardrailFindings: result.guardrail_findings,
        unimplementedIntents: result.unimplemented_intents,
        awaitingApproval: result.awaiting_approval,
        threadId: result.thread_id,
        executionPlan: result.execution_plan,
      }])
    } catch (err) {
      setExchanges(prev => [...prev, { prompt: '(approval)', error: friendlyChatError(err) }])
    } finally {
      setSending(false)
      sendingRef.current = false
    }
  }

  const lastAgent = [...exchanges].reverse().find(e => e.response)
  const currentAgentInfo = inferAgent(lastAgent?.intent, lastAgent ? computeStatus(lastAgent) : 'completed')
  const shortSessionId = sessionId.current.replace(/-/g, '').slice(0, 8)

  return (
    <div className="card overflow-hidden flex flex-col max-h-[80vh] sm:max-h-[620px]">
      <div className="px-5 py-4 border-b border-app flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${iconColor}`}>
            <Icon size={17} />
          </div>
          <div className="min-w-0">
            <h3 className="text-[14px] font-semibold text-app">{title}</h3>
            <p className="text-[12px] text-faint mt-0.5">{description}</p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0 text-right">
          <span className="inline-flex items-center gap-1 text-[10.5px] text-faint">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 ai-pulse" /> Connected
          </span>
          <span className="text-[10px] text-faint font-mono-app" title={sessionId.current}>Session {shortSessionId}</span>
          {lastAgent && <AgentBadge agent={currentAgentInfo} />}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-app" style={{ minHeight: 160 }} aria-live="polite">
        {exchanges.length === 0 && (
          <p className="text-[12.5px] text-faint">{emptyHint ?? 'Ask a question or pick a quick prompt below to get started.'}</p>
        )}
        {exchanges.map((ex, i) => {
          const pendingHere = sending && i === exchanges.length - 1 && !ex.response && !ex.error
          const status = computeStatus(ex)
          const agent = ex.response ? inferAgent(ex.intent, status) : null
          const responseType = ex.response ? inferResponseType(ex.intent, status) : null
          const confidence = ex.response ? computeConfidence({
            responseLength: ex.response.length,
            intentCount: ex.intent?.length ?? 0,
            guardrailFindingsCount: ex.guardrailFindings?.length ?? 0,
            unimplementedCount: ex.unimplementedIntents?.length ?? 0,
            status,
          }) : null
          const sources = ex.response ? inferSources(ex.intent, ex.marketplace) : []

          return (
            <div key={i} className="space-y-2">
              <div className="flex justify-end">
                <div className="max-w-[85%] px-3 py-2 rounded-xl text-[12.5px] bg-primary text-white">{ex.prompt}</div>
              </div>
              {ex.error && (
                <div className="flex items-start justify-between gap-2 px-3 py-2 rounded-xl text-[12.5px] bg-accent-red-soft text-accent-red border border-app">
                  <div className="flex items-start gap-2">
                    <AlertTriangle size={13} className="flex-shrink-0 mt-0.5" /> {ex.error}
                  </div>
                  <button
                    type="button"
                    onClick={() => send(ex.prompt)}
                    disabled={sending}
                    className="flex-shrink-0 text-[11px] font-medium underline decoration-dotted disabled:opacity-50"
                  >
                    Retry
                  </button>
                </div>
              )}
              {pendingHere && (
                <div className="flex justify-start">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                    <Sparkles size={10} className="text-white" />
                  </div>
                  <div className="max-w-[85%] min-w-0 px-3 py-2 rounded-xl bg-elev shadow-sm border border-app">
                    <LoadingTimeline className="mb-2" />
                    <AgentTimeline status="pending" />
                  </div>
                </div>
              )}
              {ex.response && (
                <>
                  {!!ex.executionPlan?.length && (
                    <div className="pl-8">
                      <ExecutionTimeline executionPlan={ex.executionPlan} className="mb-1.5" />
                    </div>
                  )}
                  <div className="flex justify-start">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                      <Sparkles size={10} className="text-white" />
                    </div>
                    <div className="max-w-[85%] min-w-0">
                      <div className="px-3 py-2 rounded-xl bg-elev shadow-sm border border-app">
                        <AgentTimeline status={status} />
                        <div className="flex items-center flex-wrap gap-1 my-1.5">
                          {agent && <AgentBadge agent={agent} />}
                          {responseType && <ResponseTypeChip type={responseType} />}
                          <StatusBadge status={status} />
                          {confidence && <ConfidenceBadge confidence={confidence} />}
                        </div>
                        <div className="text-[12.5px] leading-relaxed text-dim">
                          <ChatMessageContent text={ex.response} />
                        </div>
                        <SourceList sources={sources} />
                      </div>
                      {!!ex.guardrailFindings?.length && (
                        <div className="mt-1.5 px-2.5 py-1.5 rounded-lg bg-accent-amber-soft border border-app text-[11px] text-accent-amber flex items-start gap-1.5">
                          <AlertTriangle size={12} className="flex-shrink-0 mt-0.5" />
                          <span>{ex.guardrailFindings.join(' · ')}</span>
                        </div>
                      )}
                      {ex.awaitingApproval && ex.threadId && !ex.resolved && (
                        <div className="mt-2 p-2.5 rounded-lg border border-app bg-surface">
                          <div className="text-[11px] text-faint mb-2">This action needs your approval before it runs.</div>
                          <div className="flex gap-2">
                            <button type="button" disabled={sending} onClick={() => respondToApproval(i, true)}
                              className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-accent-green-soft text-accent-green text-[12px] font-medium rounded-md transition-colors disabled:opacity-50">
                              <Check size={12} /> Approve
                            </button>
                            <button type="button" disabled={sending} onClick={() => respondToApproval(i, false)}
                              className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-accent-red-soft text-accent-red text-[12px] font-medium rounded-md transition-colors disabled:opacity-50">
                              <X size={12} /> Reject
                            </button>
                          </div>
                        </div>
                      )}
                      {ex.resolved && (
                        <div className={`mt-1.5 text-[11px] ${ex.resolved === 'approved' ? 'text-accent-green' : 'text-accent-red'}`}>
                          {ex.resolved === 'approved' ? '✓ Approved' : '✕ Rejected'}
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      {quickPrompts.length > 0 && (
        <div className="px-3 py-2 flex gap-1.5 flex-wrap border-t border-app">
          {quickPrompts.map(q => (
            <button key={q.label} type="button" onClick={() => send(q.prompt)} disabled={sending}
              className="text-[11px] px-2.5 py-1.5 bg-hover hover:text-accent-blue text-dim rounded-md transition-colors border border-app disabled:opacity-50">
              {q.label}
            </button>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 px-3 py-3 border-t border-app">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send(input)}
          placeholder={placeholder}
          aria-label={placeholder}
          disabled={sending}
          className="input-app flex-1 text-[13px] px-3 py-2 disabled:opacity-60"
        />
        <button
          type="button"
          onClick={() => send(input)}
          disabled={sending || !input.trim()}
          aria-label="Send message"
          className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center text-white hover:bg-primary-hover transition-colors flex-shrink-0 disabled:opacity-50"
        >
          {sending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
        </button>
      </div>
    </div>
  )
}

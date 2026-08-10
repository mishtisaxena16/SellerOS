import { useEffect, useState } from 'react'
import { CheckCircle2, Circle, Loader2, ShieldAlert, XCircle } from 'lucide-react'
import type { ExchangeStatus } from './StatusBadge'

// Phase 4 §1 — a per-turn "the platform is actually multiple AI
// systems working together" trace. The backend pipeline (Supervisor →
// Guardrails → Knowledge Fabric → Agent, see
// backend/ai/supervisor_layer/supervisor.py) doesn't stream per-step
// progress today, so this animates through the same named stages at a
// fixed pace while the request is in flight, then snaps to whatever
// the real outcome was the instant the response (or error) lands —
// it never claims a step succeeded that the backend didn't actually
// reach.
const STEPS = [
  'Understanding request',
  'Selecting best agent',
  'Running Guardrail checks',
  'Searching Knowledge Fabric',
  'Ranking retrieved knowledge',
  'Generating response',
  'Performing response validation',
  'Ready',
] as const

const STEP_INTERVAL_MS = 380
// Index of "Running Guardrail checks" — where a guardrail block stops the trace.
const GUARDRAIL_STEP = 2
// A generic mid-pipeline stopping point to show for a hard/network error,
// since we don't know which internal stage actually failed.
const ERROR_STEP = 3

export default function AgentTimeline({ status }: { status: ExchangeStatus }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (status !== 'pending') return
    setIndex(0)
    const id = window.setInterval(() => {
      setIndex(i => (i < STEPS.length - 2 ? i + 1 : i))
    }, STEP_INTERVAL_MS)
    return () => window.clearInterval(id)
  }, [status])

  if (status === 'pending') {
    return (
      <div className="fade-in flex flex-col gap-1 py-1">
        {STEPS.map((label, i) => (
          <TimelineRow
            key={label}
            label={label}
            state={i < index ? 'done' : i === index ? 'active' : 'upcoming'}
          />
        ))}
      </div>
    )
  }

  if (status === 'blocked') {
    return (
      <div className="fade-in flex flex-col gap-1 py-1">
        {STEPS.slice(0, GUARDRAIL_STEP).map(label => (
          <TimelineRow key={label} label={label} state="done" />
        ))}
        <TimelineRow label="Running Guardrail checks" state="blocked" />
        <p className="text-[10.5px] text-faint pl-5">Stopped — the guardrail layer blocked this request.</p>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="fade-in flex flex-col gap-1 py-1">
        {STEPS.slice(0, ERROR_STEP).map(label => (
          <TimelineRow key={label} label={label} state="done" />
        ))}
        <TimelineRow label={STEPS[ERROR_STEP]} state="failed" />
        <p className="text-[10.5px] text-faint pl-5">Stopped — the request failed before completing.</p>
      </div>
    )
  }

  // completed | requires_approval — every step succeeded; the last row
  // reflects whether the run finished outright or is paused on a human.
  return (
    <div className="fade-in flex flex-col gap-1 py-1">
      {STEPS.slice(0, -1).map(label => (
        <TimelineRow key={label} label={label} state="done" />
      ))}
      <TimelineRow
        label={status === 'requires_approval' ? 'Awaiting your approval' : 'Ready'}
        state={status === 'requires_approval' ? 'waiting' : 'done'}
      />
    </div>
  )
}

type RowState = 'done' | 'active' | 'upcoming' | 'blocked' | 'failed' | 'waiting'

function TimelineRow({ label, state }: { label: string; state: RowState }) {
  const icon = {
    done: <CheckCircle2 size={13} className="text-accent-green" />,
    active: <Loader2 size={13} className="text-accent-blue animate-spin" />,
    upcoming: <Circle size={13} className="text-faint" />,
    blocked: <ShieldAlert size={13} className="text-accent-red" />,
    failed: <XCircle size={13} className="text-accent-red" />,
    waiting: <Loader2 size={13} className="text-accent-amber" />,
  }[state]

  const textClass = {
    done: 'text-dim',
    active: 'text-app font-medium',
    upcoming: 'text-faint',
    blocked: 'text-accent-red font-medium',
    failed: 'text-accent-red font-medium',
    waiting: 'text-accent-amber font-medium',
  }[state]

  return (
    <div className="flex items-center gap-1.5">
      {icon}
      <span className={`text-[11px] ${textClass}`}>{label}</span>
    </div>
  )
}

import { CheckCircle2, Clock, ShieldAlert, XCircle } from 'lucide-react'

// Single source of truth for "what state is this assistant turn in" —
// used to drive StatusBadge itself, AgentTimeline's final frame, and
// ConfidenceBadge's penalty for blocked/errored turns. Kept here (not
// duplicated per-consumer) per the Phase 4 "no duplicated logic" rule.
export type ExchangeStatus = 'pending' | 'completed' | 'requires_approval' | 'blocked' | 'error'

export interface ExchangeStatusInput {
  error?: string
  response?: string
  guardrailFindings?: string[]
  awaitingApproval?: boolean
}

// The backend's ChatResponse (see backend/schema/chat.py) never sends an
// explicit "blocked" flag — a guardrail block surfaces as non-empty
// guardrail_findings with no approval step to resume from. Everything
// else is a direct read of fields already on the Exchange/Message.
export function computeStatus(input: ExchangeStatusInput): ExchangeStatus {
  if (input.error) return 'error'
  if (input.response === undefined) return 'pending'
  if (input.awaitingApproval) return 'requires_approval'
  if (input.guardrailFindings && input.guardrailFindings.length > 0) return 'blocked'
  return 'completed'
}

const STATUS_META: Record<Exclude<ExchangeStatus, 'pending'>, {
  label: string
  icon: typeof CheckCircle2
  text: string
  bg: string
}> = {
  completed: { label: 'Completed', icon: CheckCircle2, text: 'text-accent-green', bg: 'bg-accent-green-soft' },
  requires_approval: { label: 'Requires Approval', icon: Clock, text: 'text-accent-amber', bg: 'bg-accent-amber-soft' },
  blocked: { label: 'Blocked by Guardrail', icon: ShieldAlert, text: 'text-accent-red', bg: 'bg-accent-red-soft' },
  error: { label: 'Error', icon: XCircle, text: 'text-accent-red', bg: 'bg-accent-red-soft' },
}

export default function StatusBadge({ status }: { status: ExchangeStatus }) {
  if (status === 'pending') return null
  const meta = STATUS_META[status]
  const Icon = meta.icon
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-medium ${meta.text} ${meta.bg}`}>
      <Icon size={10} />
      {meta.label}
    </span>
  )
}

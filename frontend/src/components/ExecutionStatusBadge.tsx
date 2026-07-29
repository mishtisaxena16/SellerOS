import { CheckCircle2, Clock, Loader2, MinusCircle, XCircle } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { ExecutionStepStatus } from '../api/chat'

// Phase 6.2, Task 2 — one badge per ExecutionStepStatus (see
// backend/ai/planner_layer/models.py's ExecutionStatus, mirrored in
// api/chat.ts's ExecutionStepStatus). Same visual language as the
// existing StatusBadge.tsx/ConfidenceBadge.tsx (text/bg pair from the
// shared accent tokens in index.css) so this reads as part of the same
// design system, not a new one.
interface StatusMeta {
  label: string
  icon: LucideIcon
  text: string
  bg: string
  spin?: boolean
  pulse?: boolean
}

const STATUS_META: Record<ExecutionStepStatus, StatusMeta> = {
  pending: { label: 'Pending', icon: Clock, text: 'text-accent-amber', bg: 'bg-accent-amber-soft' },
  running: { label: 'Running', icon: Loader2, text: 'text-accent-blue', bg: 'bg-accent-blue-soft', spin: true, pulse: true },
  completed: { label: 'Completed', icon: CheckCircle2, text: 'text-accent-green', bg: 'bg-accent-green-soft' },
  failed: { label: 'Failed', icon: XCircle, text: 'text-accent-red', bg: 'bg-accent-red-soft' },
  // No dedicated "gray" accent token exists in index.css — text-faint /
  // bg-hover (both already theme-aware for dark/light) read as neutral
  // without needing a new CSS variable for this one status.
  skipped: { label: 'Skipped', icon: MinusCircle, text: 'text-faint', bg: 'bg-hover' },
}

export default function ExecutionStatusBadge({ status }: { status: ExecutionStepStatus }) {
  // Defensive fallback: a status this component doesn't recognize yet
  // (e.g. a future value added server-side before the frontend catches
  // up) renders as "Pending" rather than crashing.
  const meta = STATUS_META[status] ?? STATUS_META.pending
  const Icon = meta.icon
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-medium flex-shrink-0 transition-colors duration-300 ${meta.text} ${meta.bg} ${meta.pulse ? 'animate-pulse' : ''}`}
      title={meta.label}
    >
      <Icon size={10} className={meta.spin ? 'animate-spin' : ''} />
      {meta.label}
    </span>
  )
}

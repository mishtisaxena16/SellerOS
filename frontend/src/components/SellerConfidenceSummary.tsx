import { ShieldCheck } from 'lucide-react'
import AgentBadge, { type AgentInfo } from './AgentBadge'
import StatusBadge, { type ExchangeStatus } from './StatusBadge'
import ConfidenceIndicator from './ConfidenceIndicator'

// ============================================================================
// Phase 6.4C — Confidence Aggregation
// ============================================================================
// Reusable, presentation-only component that rolls up confidence across the
// agents involved in a Seller Coach turn: an overall confidence figure, the
// overall execution status, and a per-agent confidence breakdown. It only
// renders what it's given — no computation, no fetching, no coupling to the
// planner/coordinator. Reuses existing badges (AgentBadge, StatusBadge,
// ConfidenceIndicator) instead of introducing new ones, so it reads as part
// of the same design language. Does not touch AgentConsole, FloatingAI, the
// backend planner, the coordinator, the connector layer, any API, or
// Playwright — a parent can wire this up later by passing in real data.
// ============================================================================

/** One agent's confidence contribution to the overall turn. */
export interface AgentConfidenceEntry {
  /** Reuses the existing AgentInfo shape from AgentBadge for a consistent
   *  agent identity (name, emoji, color) across the app. */
  agent: AgentInfo
  /** 0–100. */
  confidence: number
}

interface SellerConfidenceSummaryProps {
  /** 0–100 aggregate confidence across all agents involved in the turn. */
  overallConfidence: number
  /** Reuses the existing ExchangeStatus used by StatusBadge elsewhere. */
  overallStatus: ExchangeStatus
  /** Per-agent confidence breakdown. */
  agentConfidences: AgentConfidenceEntry[]
  emptyMessage?: string
  className?: string
}

export default function SellerConfidenceSummary({
  overallConfidence,
  overallStatus,
  agentConfidences,
  emptyMessage = 'No per-agent confidence to show yet.',
  className = '',
}: SellerConfidenceSummaryProps) {
  return (
    <div className={`card p-5 fade-in ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-accent-blue-soft flex items-center justify-center text-accent-blue flex-shrink-0">
          <ShieldCheck size={14} />
        </div>
        <h3 className="text-[14px] font-semibold text-app">Confidence Summary</h3>
      </div>

      <div className="space-y-4">
        {/* Overall confidence + overall execution status */}
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex-1 min-w-[160px]">
            <ConfidenceIndicator confidence={overallConfidence} />
          </div>
          <div className="pt-[1.5px]">
            <div className="text-[11px] text-dim mb-1.5 text-right">Execution status</div>
            <div className="flex justify-end">
              <StatusBadge status={overallStatus} />
            </div>
          </div>
        </div>

        {/* Per-agent confidence breakdown */}
        <div>
          <div className="text-[11.5px] font-semibold text-app mb-2">Agent confidence</div>
          {agentConfidences.length === 0 ? (
            <div className="text-[12px] text-faint">{emptyMessage}</div>
          ) : (
            <ul className="space-y-2">
              {agentConfidences.map((entry, i) => (
                <li key={`${entry.agent.key}-${i}`} className="flex items-center justify-between gap-3 p-2.5 rounded-lg bg-surface">
                  <AgentBadge agent={entry.agent} />
                  <ConfidenceIndicator confidence={entry.confidence} compact />
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}

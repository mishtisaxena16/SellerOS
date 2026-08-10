import { ArrowRight } from 'lucide-react'
import AgentBadge, { type AgentInfo } from './AgentBadge'

// ============================================================================
// Phase 6.4B — Priority Recommendations
// ============================================================================
// Reusable model + UI for a single Seller Coach recommendation (priority,
// responsible agent, title, description, suggested action), plus a thin
// list wrapper so callers can render many of these at once without
// re-implementing the mapping/spacing themselves. This file only adds new,
// self-contained components — it does not read live data itself and does
// not touch AgentConsole, FloatingAI, routing, backend logic, the connector
// layer, any API, or Playwright. A parent page can wire it up later by
// fetching/deriving `Recommendation[]` and passing it in as a prop.
// ============================================================================

export type RecommendationPriority = 'High' | 'Medium' | 'Low'

/** A single actionable recommendation surfaced by (or on behalf of) an agent. */
export interface Recommendation {
  id: string
  priority: RecommendationPriority
  /** Which agent is responsible for/behind this recommendation. Reuses the
   *  existing AgentInfo shape from AgentBadge so the identity (name, emoji,
   *  color) stays consistent with the rest of the app. */
  agent: AgentInfo
  title: string
  description: string
  suggestedAction: string
}

const PRIORITY_CLASSES: Record<RecommendationPriority, string> = {
  High: 'text-accent-red bg-accent-red-soft',
  Medium: 'text-accent-amber bg-accent-amber-soft',
  Low: 'text-accent-green bg-accent-green-soft',
}

interface RecommendationCardProps {
  recommendation: Recommendation
  /** Optional stagger delay (ms) for the fade-in, used by RecommendationCardList. */
  delay?: number
  className?: string
}

export default function RecommendationCard({ recommendation, delay = 0, className = '' }: RecommendationCardProps) {
  return (
    <div
      className={`card p-4 fade-in ${className}`}
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'backwards' }}
    >
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className={`badge ${PRIORITY_CLASSES[recommendation.priority]}`}>{recommendation.priority}</span>
        <AgentBadge agent={recommendation.agent} />
      </div>

      <div className="text-[13.5px] font-semibold text-app mb-1">{recommendation.title}</div>
      <p className="text-[12.5px] text-dim leading-relaxed mb-3">{recommendation.description}</p>

      <div className="flex items-start gap-2 p-2.5 rounded-lg bg-surface">
        <ArrowRight size={13} className="text-accent-blue flex-shrink-0 mt-0.5" />
        <span className="text-[12px] text-app">
          <span className="text-faint">Suggested action: </span>
          {recommendation.suggestedAction}
        </span>
      </div>
    </div>
  )
}

interface RecommendationCardListProps {
  recommendations: Recommendation[]
  emptyMessage?: string
  className?: string
}

/** Renders multiple RecommendationCards with consistent spacing and a
 *  staggered fade-in, so callers don't have to re-implement the .map(). */
export function RecommendationCardList({
  recommendations,
  emptyMessage = 'No recommendations right now.',
  className = '',
}: RecommendationCardListProps) {
  if (recommendations.length === 0) {
    return <div className="text-[12.5px] text-faint">{emptyMessage}</div>
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {recommendations.map((recommendation, i) => (
        <RecommendationCard key={recommendation.id} recommendation={recommendation} delay={i * 40} />
      ))}
    </div>
  )
}

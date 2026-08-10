import { ArrowRight } from 'lucide-react'
import type { Recommendation, ActionPriority } from '../data/mockBusinessData'

const PRIORITY_CLASSES: Record<ActionPriority, string> = {
  Low: 'text-accent-green bg-accent-green-soft',
  Medium: 'text-accent-blue bg-accent-blue-soft',
  High: 'text-accent-amber bg-accent-amber-soft',
  Critical: 'text-accent-red bg-accent-red-soft',
}

interface RecommendationCardProps {
  recommendation: Recommendation
}

export default function RecommendationCard({ recommendation }: RecommendationCardProps) {
  return (
    <div className="p-4 bg-surface rounded-lg flex items-center justify-between gap-4 fade-in">
      <div className="min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <span className={`badge ${PRIORITY_CLASSES[recommendation.priority]}`}>{recommendation.priority}</span>
          <span className="text-[13px] font-semibold text-app truncate">{recommendation.title}</span>
        </div>
        <div className="text-[11.5px] text-dim flex items-center gap-1.5 flex-wrap">
          <span>{recommendation.expectedImpact}</span>
          <span className="text-faint">·</span>
          <span className="text-accent-green font-medium">{recommendation.estimatedImprovement}</span>
          <span className="text-faint">·</span>
          <span>{recommendation.confidence}% confidence</span>
        </div>
      </div>
      <ArrowRight size={16} className="text-faint flex-shrink-0" />
    </div>
  )
}

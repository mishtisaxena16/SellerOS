import { X, ArrowUpRight, ArrowDownRight, Minus, Sparkles, Lightbulb, ShieldCheck, BookOpen } from 'lucide-react'
import type { AIInsight, ActionPriority } from '../data/mockBusinessData'

const PRIORITY_CLASSES: Record<ActionPriority, string> = {
  Low: 'text-accent-green bg-accent-green-soft',
  Medium: 'text-accent-blue bg-accent-blue-soft',
  High: 'text-accent-amber bg-accent-amber-soft',
  Critical: 'text-accent-red bg-accent-red-soft',
}

interface InsightPanelProps {
  insight: AIInsight | null
  onClose: () => void
}

export default function InsightPanel({ insight, onClose }: InsightPanelProps) {
  if (!insight) return null

  const TrendIcon = insight.trend === 'up' ? ArrowUpRight : insight.trend === 'down' ? ArrowDownRight : Minus
  const trendColor = insight.trend === 'up' ? 'text-accent-green' : insight.trend === 'down' ? 'text-accent-red' : 'text-dim'

  return (
    <div className="fixed inset-0 z-50 flex items-stretch justify-end">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full max-w-md h-full bg-elev border-l border-app shadow-app overflow-y-auto fade-in">
        <div className="sticky top-0 bg-elev border-b border-app px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-accent-blue-soft flex items-center justify-center text-accent-blue">
              <Sparkles size={14} />
            </div>
            <h3 className="text-[14px] font-semibold text-app">AI Insight</h3>
          </div>
          <button onClick={onClose} className="text-dim hover:text-app p-1 rounded-lg bg-hover" aria-label="Close">
            <X size={16} />
          </button>
        </div>

        <div className="p-5 space-y-5">
          <div>
            <div className="text-[12px] text-dim mb-1">{insight.metricLabel}</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-app">{insight.metricValue}</span>
              <span className={`flex items-center gap-0.5 text-[12.5px] font-semibold ${trendColor}`}>
                <TrendIcon size={14} />
                {insight.changePercent > 0 ? '+' : ''}{insight.changePercent}%
              </span>
            </div>
          </div>

          <span className={`badge ${PRIORITY_CLASSES[insight.priority]}`}>
            <ShieldCheck size={11} /> {insight.priority} priority
          </span>

          <div>
            <h4 className="text-[12px] font-semibold text-dim uppercase tracking-wide mb-2">Why this changed</h4>
            <ul className="space-y-1.5">
              {insight.analysis.map((line, i) => (
                <li key={i} className="text-[13px] text-app flex items-start gap-2">
                  <span className="text-accent-blue mt-1">•</span>{line}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-[12px] font-semibold text-dim uppercase tracking-wide mb-2">Business impact</h4>
            <p className="text-[13px] text-app leading-relaxed">{insight.impact}</p>
          </div>

          <div>
            <h4 className="text-[12px] font-semibold text-dim uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <Lightbulb size={13} /> Recommendations
            </h4>
            <ul className="space-y-1.5">
              {insight.recommendations.map((line, i) => (
                <li key={i} className="text-[13px] text-app bg-surface rounded-lg px-3 py-2">{line}</li>
              ))}
            </ul>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <h4 className="text-[12px] font-semibold text-dim uppercase tracking-wide">Confidence</h4>
              <span className="text-[12.5px] font-semibold text-app">{insight.confidence}%</span>
            </div>
            <div className="h-1.5 bg-surface rounded-full overflow-hidden">
              <div className="h-full bg-accent-blue rounded-full" style={{ width: `${insight.confidence}%` }} />
            </div>
          </div>

          <div>
            <h4 className="text-[12px] font-semibold text-dim uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <BookOpen size={13} /> Knowledge sources
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {insight.sources.map((s, i) => (
                <span key={i} className="text-[11px] text-dim bg-surface rounded-full px-2.5 py-1">{s}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

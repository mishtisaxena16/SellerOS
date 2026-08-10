// Phase 6.3A, Task 2 — standalone, reusable confidence display.
//
// Deliberately NOT wired to the existing ConfidenceBadge.tsx /
// computeConfidence() (Phase 4). This component only *renders* a
// confidence number it's given — it doesn't compute one, doesn't know
// about ChatResponse/ExchangeStatus, and isn't imported anywhere yet.
// That keeps Phase 6.3A's "no integration yet" boundary clean: wiring
// this into AgentConsole/FloatingAI, or reconciling it with
// ConfidenceBadge, is later-phase work.

export type ConfidenceLevel = 'High' | 'Medium' | 'Low'

export interface ConfidenceIndicatorProps {
  /** 0–100. Values outside that range are clamped for display. */
  confidence: number
  /** Compact inline form (percentage + label, small bar) for use inside
   * headers/collapsed rows. Default is the full form with a labeled
   * progress bar, suited to an expanded detail section. */
  compact?: boolean
  className?: string
}

// 90+ High · 75–89 Medium · below 75 Low, per spec.
export function getConfidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence >= 90) return 'High'
  if (confidence >= 75) return 'Medium'
  return 'Low'
}

const LEVEL_CLASSES: Record<ConfidenceLevel, { text: string; bg: string; bar: string }> = {
  High: { text: 'text-accent-green', bg: 'bg-accent-green-soft', bar: 'bg-accent-green' },
  Medium: { text: 'text-accent-amber', bg: 'bg-accent-amber-soft', bar: 'bg-accent-amber' },
  Low: { text: 'text-accent-red', bg: 'bg-accent-red-soft', bar: 'bg-accent-red' },
}

export default function ConfidenceIndicator({ confidence, compact = false, className = '' }: ConfidenceIndicatorProps) {
  const value = Math.max(0, Math.min(100, Math.round(confidence)))
  const level = getConfidenceLevel(value)
  const classes = LEVEL_CLASSES[level]

  if (compact) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 ${className}`}
        title={`Confidence ${value}% (${level})`}
      >
        <span className="relative w-10 h-1.5 rounded-full bg-hover overflow-hidden flex-shrink-0">
          <span
            className={`absolute inset-y-0 left-0 rounded-full transition-[width] duration-500 ease-out ${classes.bar}`}
            style={{ width: `${value}%` }}
          />
        </span>
        <span className={`text-[11px] font-medium ${classes.text}`}>
          {value}% · {level}
        </span>
      </span>
    )
  }

  return (
    <div className={`fade-in ${className}`}>
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <span className="text-[11px] font-medium text-dim">Confidence</span>
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-medium ${classes.text} ${classes.bg}`}
        >
          {value}% · {level}
        </span>
      </div>
      <div
        className="relative w-full h-2 rounded-full bg-hover overflow-hidden"
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Confidence level"
      >
        <div
          className={`absolute inset-y-0 left-0 rounded-full transition-[width] duration-500 ease-out ${classes.bar}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}

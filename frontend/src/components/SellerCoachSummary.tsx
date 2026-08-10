import { GraduationCap, Sparkles, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react'

// ============================================================================
// Phase 6.4A — Seller Coach Summary
// ============================================================================
// Reusable models + UI for a compact "how's my business doing" summary card,
// meant to sit near the Seller Coach conversation (or anywhere else a short
// health/strengths/issues snapshot is useful). This file only adds a new,
// self-contained component — it does not read live data itself and does not
// touch AgentConsole, FloatingAI, any page, or any backend/API/connector
// code. A parent page can wire it up later by fetching/deriving a
// `SellerCoachSummaryData` object and passing it in as a prop.
// ============================================================================

/** 0–100 overall business health score plus a short human-readable label. */
export interface SellerCoachHealth {
  score: number
  label: string
}

/** A single strength called out for the seller (e.g. "Returns trending down"). */
export interface SellerCoachStrength {
  id: string
  title: string
  detail?: string
}

/** A single issue/risk called out for the seller, with an optional severity. */
export interface SellerCoachIssue {
  id: string
  title: string
  detail?: string
  severity?: 'warning' | 'critical'
}

/** Full shape consumed by <SellerCoachSummary />. */
export interface SellerCoachSummaryData {
  health: SellerCoachHealth
  aiSummary: string
  strengths: SellerCoachStrength[]
  issues: SellerCoachIssue[]
}

function healthColor(score: number): string {
  if (score >= 85) return 'var(--green)'
  if (score >= 70) return 'var(--amber)'
  return 'var(--red)'
}

interface SellerCoachSummaryProps {
  /** The summary to render. Pass `null` while there is nothing to show yet. */
  data: SellerCoachSummaryData | null
  /** Shows a skeleton placeholder instead of `data`. */
  loading?: boolean
  /** Shows an inline error state (with an optional retry) instead of `data`. */
  error?: string | null
  /** Called when the person clicks "Retry" while `error` is set. */
  onRetry?: () => void
  /** Optional className passthrough so callers can control spacing/width. */
  className?: string
}

export default function SellerCoachSummary({
  data,
  loading = false,
  error = null,
  onRetry,
  className = '',
}: SellerCoachSummaryProps) {
  return (
    <div className={`card p-5 fade-in ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-accent-blue-soft flex items-center justify-center text-accent-blue flex-shrink-0">
          <GraduationCap size={14} />
        </div>
        <h3 className="text-[14px] font-semibold text-app">Seller Coach Summary</h3>
      </div>

      {loading ? (
        <div className="space-y-3 animate-pulse">
          <div className="flex items-center gap-4">
            <span className="h-16 w-16 rounded-full bg-hover inline-block flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <span className="h-3 w-2/3 rounded-md bg-hover inline-block" />
              <span className="h-3 w-1/2 rounded-md bg-hover inline-block" />
            </div>
          </div>
          <span className="h-3 w-full rounded-md bg-hover inline-block" />
          <span className="h-3 w-5/6 rounded-md bg-hover inline-block" />
        </div>
      ) : error ? (
        <div className="flex flex-wrap items-center gap-2 text-[12px] text-accent-red">
          <AlertTriangle size={13} className="flex-shrink-0" />
          <span>{error}</span>
          {onRetry && (
            <button onClick={onRetry} className="inline-flex items-center gap-1 text-accent-blue hover:underline">
              <RefreshCw size={11} /> Retry
            </button>
          )}
        </div>
      ) : !data ? (
        <div className="text-[12.5px] text-faint">No summary available yet.</div>
      ) : (
        <div className="space-y-5">
          {/* Overall health */}
          <div className="flex items-center gap-4 flex-wrap">
            <div className="relative w-16 h-16 flex-shrink-0">
              <svg viewBox="0 0 66 66" className="w-16 h-16 -rotate-90">
                <circle cx="33" cy="33" r="27" fill="none" stroke="var(--border)" strokeWidth="6" />
                <circle
                  cx="33" cy="33" r="27" fill="none"
                  stroke={healthColor(data.health.score)} strokeWidth="6" strokeLinecap="round"
                  strokeDasharray={2 * Math.PI * 27}
                  strokeDashoffset={2 * Math.PI * 27 - (data.health.score / 100) * 2 * Math.PI * 27}
                  className="score-ring"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-[15px] font-bold text-app leading-none">{data.health.score}</span>
              </div>
            </div>
            <div className="min-w-[160px]">
              <div className="text-[11px] text-faint mb-0.5">Overall business health</div>
              <div className="text-[14px] font-semibold" style={{ color: healthColor(data.health.score) }}>
                {data.health.label}
              </div>
            </div>
          </div>

          {/* AI summary */}
          <div className="flex items-start gap-2 p-3 rounded-lg bg-surface">
            <Sparkles size={14} className="text-accent-blue flex-shrink-0 mt-0.5" />
            <p className="text-[12.5px] text-dim leading-relaxed">{data.aiSummary}</p>
          </div>

          {/* Strengths + issues */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <div className="text-[11.5px] font-semibold text-app mb-2 flex items-center gap-1.5">
                <CheckCircle2 size={13} className="text-accent-green" />
                Top strengths
              </div>
              {data.strengths.length === 0 ? (
                <div className="text-[12px] text-faint">Nothing notable yet.</div>
              ) : (
                <ul className="space-y-2">
                  {data.strengths.map(s => (
                    <li key={s.id} className="text-[12px]">
                      <span className="text-app font-medium">{s.title}</span>
                      {s.detail && <span className="text-faint"> — {s.detail}</span>}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div>
              <div className="text-[11.5px] font-semibold text-app mb-2 flex items-center gap-1.5">
                <AlertTriangle size={13} className="text-accent-amber" />
                Top issues
              </div>
              {data.issues.length === 0 ? (
                <div className="text-[12px] text-faint">No issues flagged.</div>
              ) : (
                <ul className="space-y-2">
                  {data.issues.map(i => (
                    <li key={i.id} className="text-[12px]">
                      <span className={i.severity === 'critical' ? 'text-accent-red font-medium' : 'text-accent-amber font-medium'}>
                        {i.title}
                      </span>
                      {i.detail && <span className="text-faint"> — {i.detail}</span>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

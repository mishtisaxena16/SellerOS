import type { BusinessHealth } from '../data/mockBusinessData'

function scoreColor(score: number): string {
  if (score >= 85) return 'var(--green)'
  if (score >= 70) return 'var(--amber)'
  return 'var(--red)'
}

export default function BusinessHealthCard({ health }: { health: BusinessHealth }) {
  const radius = 46
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (health.score / 100) * circumference
  const ringColor = scoreColor(health.score)

  return (
    <div className="card p-5 fade-in">
      <h3 className="text-[14px] font-semibold text-app mb-4">Business Health</h3>
      <div className="flex items-center gap-6 flex-wrap">
        <div className="relative w-28 h-28 flex-shrink-0">
          <svg viewBox="0 0 110 110" className="w-28 h-28 -rotate-90">
            <circle cx="55" cy="55" r={radius} fill="none" stroke="var(--border)" strokeWidth="8" />
            <circle
              cx="55" cy="55" r={radius} fill="none"
              stroke={ringColor} strokeWidth="8" strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className="score-ring"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-bold text-app">{health.score}</span>
            <span className="text-[10px] text-faint">/ 100</span>
          </div>
        </div>

        <div className="flex-1 min-w-[180px]">
          <div className="text-[13px] font-semibold mb-3" style={{ color: ringColor }}>{health.label}</div>
          <div className="space-y-2.5">
            {health.breakdown.map(item => (
              <div key={item.label}>
                <div className="flex justify-between text-[11.5px] mb-1">
                  <span className="text-dim">{item.label}</span>
                  <span className="text-app font-medium">{item.score}</span>
                </div>
                <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${item.score}%`, backgroundColor: scoreColor(item.score) }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

import { AlertTriangle, ChevronRight } from 'lucide-react'
import type { BusinessWarning } from '../data/mockBusinessData'

interface WarningBannerProps {
  warnings: BusinessWarning[]
  onSelect: (warning: BusinessWarning) => void
}

export default function WarningBanner({ warnings, onSelect }: WarningBannerProps) {
  if (warnings.length === 0) return null

  return (
    <div className="space-y-2">
      {warnings.map((warning, i) => (
        <button
          key={warning.id}
          type="button"
          onClick={() => onSelect(warning)}
          className={`w-full flex items-center justify-between gap-3 p-3 rounded-lg text-left fade-in ${
            warning.severity === 'critical' ? 'bg-accent-red-soft' : 'bg-accent-amber-soft'
          }`}
          style={{ animationDelay: `${i * 40}ms`, animationFillMode: 'backwards' }}
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <AlertTriangle
              size={15}
              className={warning.severity === 'critical' ? 'text-accent-red flex-shrink-0' : 'text-accent-amber flex-shrink-0'}
            />
            <span className={`text-[13px] font-medium truncate ${warning.severity === 'critical' ? 'text-accent-red' : 'text-accent-amber'}`}>
              {warning.message}
            </span>
          </div>
          <ChevronRight size={15} className="text-faint flex-shrink-0" />
        </button>
      ))}
    </div>
  )
}

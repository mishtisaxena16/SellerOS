import { useNavigate } from 'react-router-dom'
import { SearchCheck, LineChart, PackageSearch, TrendingUp, FileBarChart2 } from 'lucide-react'
import type { QuickAction } from '../data/mockBusinessData'

const ICONS: Record<string, typeof SearchCheck> = {
  'analyze-listings': SearchCheck,
  'optimize-pricing': LineChart,
  'review-inventory': PackageSearch,
  'forecast-demand': TrendingUp,
  'generate-report': FileBarChart2,
}

export default function ActionCenter({ actions }: { actions: QuickAction[] }) {
  const navigate = useNavigate()

  return (
    <div className="card p-5 fade-in">
      <h3 className="text-[14px] font-semibold text-app mb-4">Quick Actions</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {actions.map(action => {
          const Icon = ICONS[action.id] ?? SearchCheck
          return (
            <button
              key={action.id}
              type="button"
              onClick={() => navigate(action.route)}
              className="p-3.5 bg-surface rounded-lg text-left card-hover flex flex-col gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--blue)]"
            >
              <div className="w-8 h-8 rounded-lg bg-accent-blue-soft text-accent-blue flex items-center justify-center">
                <Icon size={16} />
              </div>
              <div>
                <div className="text-[12.5px] font-semibold text-app">{action.label}</div>
                <div className="text-[11px] text-faint mt-0.5">{action.description}</div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

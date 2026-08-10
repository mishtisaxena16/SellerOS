import { Sparkles, TrendingUp } from 'lucide-react'
import type { BusinessSummary as BusinessSummaryData } from '../data/mockBusinessData'

export default function BusinessSummary({ summary }: { summary: BusinessSummaryData }) {
  return (
    <div className="card p-5 fade-in bg-accent-blue-soft/0">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-7 h-7 rounded-lg bg-accent-blue-soft flex items-center justify-center text-accent-blue">
          <Sparkles size={14} />
        </div>
        <h3 className="text-[14px] font-semibold text-app">Today's Summary</h3>
      </div>
      <div className="flex flex-wrap gap-2 mb-3">
        {summary.headline.map((line, i) => (
          <span key={i} className="text-[12px] text-app bg-surface rounded-full px-3 py-1.5">{line}</span>
        ))}
      </div>
      <div className="flex items-center gap-1.5 text-[12.5px]">
        <TrendingUp size={14} className="text-accent-green" />
        <span className="text-dim">Highest opportunity:</span>
        <span className="text-app font-semibold">{summary.highestOpportunity}</span>
      </div>
    </div>
  )
}

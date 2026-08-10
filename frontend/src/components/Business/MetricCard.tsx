import {
  IndianRupee, ShoppingBag, Wallet, Boxes, RotateCcw,
  Percent, Megaphone, MousePointerClick, Target, ArrowUpRight, ArrowDownRight, Minus,
} from 'lucide-react'
import type { MetricCardData } from '../data/mockBusinessData'

const ICONS: Record<MetricCardData['icon'], typeof IndianRupee> = {
  revenue: IndianRupee,
  orders: ShoppingBag,
  profit: Wallet,
  inventory: Boxes,
  returns: RotateCcw,
  conversion: Percent,
  adspend: Megaphone,
  ctr: MousePointerClick,
  roas: Target,
}

const COLOR_CLASSES: Record<MetricCardData['color'], string> = {
  blue: 'text-accent-blue bg-accent-blue-soft',
  green: 'text-accent-green bg-accent-green-soft',
  purple: 'text-accent-purple bg-accent-purple-soft',
  amber: 'text-accent-amber bg-accent-amber-soft',
  red: 'text-accent-red bg-accent-red-soft',
  pink: 'text-accent-pink bg-accent-purple-soft',
}

interface MetricCardProps {
  data: MetricCardData
  onClick: (data: MetricCardData) => void
  delay?: number
}

export default function MetricCard({ data, onClick, delay = 0 }: MetricCardProps) {
  const Icon = ICONS[data.icon]
  const TrendIcon = data.trend === 'up' ? ArrowUpRight : data.trend === 'down' ? ArrowDownRight : Minus
  const trendColor = data.trend === 'up' ? 'text-accent-green' : data.trend === 'down' ? 'text-accent-red' : 'text-dim'

  return (
    <button
      type="button"
      onClick={() => onClick(data)}
      className="card card-interactive card-hover p-4 text-left w-full fade-in focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--blue)]"
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'backwards' }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${COLOR_CLASSES[data.color]}`}>
          <Icon size={16} />
        </div>
        <span className={`flex items-center gap-0.5 text-[11.5px] font-semibold ${trendColor}`}>
          <TrendIcon size={13} />
          {data.changePercent > 0 ? '+' : ''}{data.changePercent}%
        </span>
      </div>
      <div className="text-xl font-bold text-app mb-0.5">{data.value}</div>
      <div className="text-[12px] text-dim">{data.label}</div>
      <div className="text-[10.5px] text-faint mt-2 flex items-center gap-1">
        AI Insight available
      </div>
    </button>
  )
}

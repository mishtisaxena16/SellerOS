import { useMemo } from 'react'
import { BarChart3, Loader2 } from 'lucide-react'
import type { OrderRecord } from '../api/orders'

interface TrendChartCardProps {
  title: string
  orders: OrderRecord[]
  loading: boolean
  metric: 'revenue' | 'orders'
  days?: number
}

// A dependency-free SVG bar chart, computed from real order_date +
// total_amount values already fetched for this page — no recharts
// dependency, no invented data. When there's nothing to plot yet
// (loading, or zero orders), this renders a grey skeleton / empty
// state instead of either a fake trend line or no chart at all —
// keeps the "premium analytics" look without fabricating numbers.
export default function TrendChartCard({ title, orders, loading, metric, days = 14 }: TrendChartCardProps) {
  const buckets = useMemo(() => {
    // Bucket keys must be built in UTC, not local-midnight-then-converted:
    // order_date is sliced straight off the backend's UTC ISO string below,
    // so for any timezone ahead of UTC (e.g. IST, UTC+5:30), a local
    // midnight Date converted via toISOString() lands on the *previous*
    // UTC day — shifting every bucket back a day and silently dropping
    // today's orders (they'd fall on a UTC date past the last bucket).
    const now = new Date()
    const dayKeys: string[] = []
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - i))
      dayKeys.push(d.toISOString().slice(0, 10))
    }
    const totals: Record<string, number> = Object.fromEntries(dayKeys.map(k => [k, 0]))
    for (const o of orders) {
      if (!o.order_date) continue
      const key = o.order_date.slice(0, 10)
      if (!(key in totals)) continue
      totals[key] += metric === 'revenue' ? (o.total_amount ?? 0) : 1
    }
    return dayKeys.map(k => ({ key: k, value: totals[k] }))
  }, [orders, metric, days])

  const hasData = !loading && orders.length > 0
  const max = Math.max(1, ...buckets.map(b => b.value))

  return (
    <div className="card p-5">
      <h3 className="text-[14px] font-semibold text-app mb-1 flex items-center gap-2"><BarChart3 size={15} /> {title}</h3>
      <p className="text-[12px] text-faint mb-4">
        {hasData ? `Last ${days} days, from your synced orders` : 'Waiting for order data'}
      </p>

      {loading ? (
        <div className="flex items-end gap-1.5 h-32">
          {Array.from({ length: days }).map((_, i) => (
            <div key={i} className="flex-1 bg-surface rounded-t animate-pulse" style={{ height: `${20 + (i % 5) * 12}%` }} />
          ))}
        </div>
      ) : !hasData ? (
        <div className="flex flex-col items-center justify-center h-32 gap-2 text-faint">
          <BarChart3 size={20} className="opacity-40" />
          <span className="text-[12px]">No orders synced yet — this fills in once orders start coming through.</span>
        </div>
      ) : (
        <div className="flex items-end gap-1.5 h-32">
          {buckets.map(b => (
            <div key={b.key} className="flex-1 flex flex-col items-center justify-end h-full group relative">
              <div
                className={`w-full rounded-t transition-all ${b.value > 0 ? 'bg-accent-blue' : 'bg-surface'}`}
                style={{ height: `${b.value > 0 ? Math.max(4, (b.value / max) * 100) : 4}%` }}
                role="img"
                aria-label={`${b.key}: ${metric === 'revenue' ? `₹${b.value.toLocaleString('en-IN')}` : `${b.value} orders`}`}
              />
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 hidden group-hover:block text-[10.5px] bg-app text-white px-1.5 py-0.5 rounded whitespace-nowrap z-10">
                {metric === 'revenue' ? `₹${b.value.toLocaleString('en-IN')}` : `${b.value} orders`}
              </div>
            </div>
          ))}
        </div>
      )}
      {loading && (
        <div className="flex items-center gap-1.5 mt-2 text-[11px] text-faint"><Loader2 size={11} className="animate-spin" /> Loading…</div>
      )}
    </div>
  )
}

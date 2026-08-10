import { useMemo } from 'react'
import { BarChart3, Loader2 } from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { OrderRecord } from '../api/orders'

interface TrendChartCardProps {
  title: string
  orders: OrderRecord[]
  loading: boolean
  metric: 'revenue' | 'orders'
  days?: number
  isMockData?: boolean
}

const DAY_LABEL = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', timeZone: 'UTC' })

function formatCurrency(value: number) {
  return `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

export default function TrendChartCard({
  title,
  orders,
  loading,
  metric,
  days = 14,
  isMockData = false,
}: TrendChartCardProps) {
  const chartData = useMemo(() => {
    const validDateKeys = orders
      .map(order => order.order_date?.slice(0, 10))
      .filter((date): date is string => Boolean(date))
    const endKey = validDateKeys.length > 0
      ? validDateKeys.reduce((latest, date) => (date > latest ? date : latest))
      : new Date().toISOString().slice(0, 10)
    const [year, month, day] = endKey.split('-').map(Number)
    const dayKeys: string[] = []

    for (let offset = days - 1; offset >= 0; offset--) {
      const date = new Date(Date.UTC(year, month - 1, day - offset))
      dayKeys.push(date.toISOString().slice(0, 10))
    }

    const totals = Object.fromEntries(dayKeys.map(date => [date, 0])) as Record<string, number>
    for (const order of orders) {
      const date = order.order_date?.slice(0, 10)
      if (!date || !(date in totals)) continue
      totals[date] += metric === 'revenue' ? (order.total_amount ?? 0) : 1
    }

    return dayKeys.map(date => ({
      date,
      label: DAY_LABEL.format(new Date(`${date}T00:00:00Z`)),
      value: Math.round(totals[date] * 100) / 100,
    }))
  }, [orders, metric, days])

  const hasData = !loading && orders.length > 0
  const valueLabel = metric === 'revenue' ? 'Revenue' : 'Orders'
  const tooltipFormatter = (value: number | string | undefined) => {
    const numericValue = Number(value ?? 0)
    return metric === 'revenue' ? formatCurrency(numericValue) : numericValue.toLocaleString('en-IN')
  }

  return (
    <section className="card p-5" aria-label={title}>
      <h3 className="text-[14px] font-semibold text-app mb-1 flex items-center gap-2"><BarChart3 size={15} /> {title}</h3>
      <p className="text-[12px] text-faint mb-4">
        {hasData ? `Last ${days} days · ${isMockData ? 'Demo order history' : 'Synced order history'}` : 'Waiting for order data'}
      </p>

      {loading ? (
        <div className="flex items-end gap-1.5 h-52">
          {Array.from({ length: days }).map((_, index) => (
            <div key={index} className="flex-1 bg-surface rounded-t animate-pulse" style={{ height: `${20 + (index % 5) * 12}%` }} />
          ))}
        </div>
      ) : !hasData ? (
        <div className="flex flex-col items-center justify-center h-52 gap-2 text-faint">
          <BarChart3 size={20} className="opacity-40" />
          <span className="text-[12px] text-center">No orders available to plot yet.</span>
        </div>
      ) : (
        <div className="h-52" role="img" aria-label={`${title} chart for the last ${days} days`}>
          <ResponsiveContainer width="100%" height="100%">
            {metric === 'revenue' ? (
              <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 4 }}>
                <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 3" />
                <XAxis dataKey="label" tick={{ fill: 'var(--text-faint)', fontSize: 10 }} axisLine={false} tickLine={false} minTickGap={20} />
                <YAxis tickFormatter={value => `₹${Number(value) >= 1000 ? `${(Number(value) / 1000).toFixed(1)}k` : value}`} tick={{ fill: 'var(--text-faint)', fontSize: 10 }} axisLine={false} tickLine={false} width={42} />
                <Tooltip
                  labelFormatter={(_, payload) => payload?.[0]?.payload?.date ?? ''}
                  formatter={value => [tooltipFormatter(value), valueLabel]}
                  contentStyle={{ backgroundColor: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', fontSize: 12 }}
                  labelStyle={{ color: 'var(--text-dim)' }}
                />
                <Line type="monotone" dataKey="value" stroke="var(--blue)" strokeWidth={2.5} dot={{ r: 3, fill: 'var(--blue)', strokeWidth: 0 }} activeDot={{ r: 5 }} />
              </LineChart>
            ) : (
              <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 3" />
                <XAxis dataKey="label" tick={{ fill: 'var(--text-faint)', fontSize: 10 }} axisLine={false} tickLine={false} minTickGap={20} />
                <YAxis allowDecimals={false} tick={{ fill: 'var(--text-faint)', fontSize: 10 }} axisLine={false} tickLine={false} width={26} />
                <Tooltip
                  labelFormatter={(_, payload) => payload?.[0]?.payload?.date ?? ''}
                  formatter={value => [tooltipFormatter(value), valueLabel]}
                  contentStyle={{ backgroundColor: 'var(--bg-elev)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', fontSize: 12 }}
                  labelStyle={{ color: 'var(--text-dim)' }}
                />
                <Bar dataKey="value" fill="var(--green)" radius={[5, 5, 0, 0]} maxBarSize={28} />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
      {loading && <div className="flex items-center gap-1.5 mt-2 text-[11px] text-faint"><Loader2 size={11} className="animate-spin" /> Loading…</div>}
    </section>
  )
}

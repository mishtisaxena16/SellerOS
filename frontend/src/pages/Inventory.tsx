import { useEffect, useMemo, useState } from 'react'
import { Search, AlertTriangle, Package, TrendingDown, RefreshCw, Loader2 } from 'lucide-react'
import { usePlatform, PLATFORM_LABELS } from '../context/PlatformContext'
import { getInventory, type InventoryItem } from '../api/inventory'
import { ApiError } from '../api/client'
import EmptyMarketplaceState from '../components/EmptyMarketplaceState'

// Backend returns a low stock threshold implicitly (available_quantity),
// there's no reorder point/qty modeled yet — we derive a simple threshold
// client-side so the "Low Stock" concept still means something useful
// until the backend exposes real reorder rules.
const LOW_STOCK_THRESHOLD = 20

const getStockStatus = (qty: number) => {
  if (qty === 0) return { label: 'Out of Stock', color: 'bg-accent-red-soft text-accent-red' }
  if (qty < LOW_STOCK_THRESHOLD) return { label: 'Low Stock', color: 'bg-accent-amber-soft text-accent-amber' }
  return { label: 'In Stock', color: 'bg-accent-green-soft text-accent-green' }
}

const getStockBarColor = (qty: number) => {
  if (qty === 0) return 'bg-accent-red'
  if (qty < LOW_STOCK_THRESHOLD) return 'bg-accent-amber'
  return 'bg-accent-green'
}

export default function Inventory() {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'low' | 'out'>('all')
  const { selected } = usePlatform()

  const [items, setItems] = useState<InventoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<{ status: number; message: string } | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getInventory(selected)
      .then(res => {
        if (cancelled) return
        if (!res.success) {
          setError({ status: 200, message: res.message || 'Inventory could not be fetched.' })
          setItems([])
        } else {
          setItems(res.items)
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const apiErr = err instanceof ApiError ? err : null
        setError({ status: apiErr?.status ?? 0, message: apiErr?.message ?? 'Could not reach the SellerOS API.' })
        setItems([])
      })
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }, [selected])

  const filtered = useMemo(() => items.filter(item => {
    const matchSearch = item.sku.toLowerCase().includes(search.toLowerCase())
    const matchFilter =
      filter === 'all' ||
      (filter === 'low' && item.available_quantity > 0 && item.available_quantity < LOW_STOCK_THRESHOLD) ||
      (filter === 'out' && item.available_quantity === 0)
    return matchSearch && matchFilter
  }), [items, search, filter])

  const outOfStock = items.filter(i => i.available_quantity === 0).length
  const lowStock = items.filter(i => i.available_quantity > 0 && i.available_quantity < LOW_STOCK_THRESHOLD).length
  const healthy = items.filter(i => i.available_quantity >= LOW_STOCK_THRESHOLD).length

  // No marketplace connected at all — the backend returns a 409 for this.
  if (error && error.status === 409) {
    return <EmptyMarketplaceState message={error.message} />
  }

  return (
    <div className="p-6 fade-in">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h2 className="text-xl font-bold text-app">Inventory Management</h2>
          <p className="text-[13px] text-dim mt-0.5">
            {loading ? 'Loading…' : `${items.length} SKUs ${selected === 'all' ? '' : `on ${PLATFORM_LABELS[selected]}`}`}
          </p>
        </div>
      </div>

      {error && error.status !== 409 && (
        <div className="mb-4 p-3 rounded-lg bg-accent-red-soft text-accent-red text-[13px] flex items-center gap-2">
          <AlertTriangle size={14} /> {error.message}
        </div>
      )}

      {loading ? (
        <div className="card p-12 flex items-center justify-center gap-2 text-dim text-[13px]">
          <Loader2 size={16} className="animate-spin" /> Loading inventory…
        </div>
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Total SKUs', value: items.length, icon: Package, color: 'bg-accent-blue-soft text-accent-blue' },
              { label: 'Healthy Stock', value: healthy, icon: RefreshCw, color: 'bg-accent-green-soft text-accent-green' },
              { label: 'Low Stock', value: lowStock, icon: TrendingDown, color: 'bg-accent-amber-soft text-accent-amber' },
              { label: 'Out of Stock', value: outOfStock, icon: AlertTriangle, color: 'bg-accent-red-soft text-accent-red' },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="card p-4 flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
                  <Icon size={18} />
                </div>
                <div>
                  <div className="text-xl font-bold text-app">{value}</div>
                  <div className="text-[12px] text-dim">{label}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <div className="relative flex-1 max-w-sm">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search by SKU..."
                className="input-app w-full pl-9 pr-4 py-2 text-[13px]"
              />
            </div>
            <div className="flex items-center gap-1.5">
              {([['all','All'],['low','Low Stock'],['out','Out of Stock']] as const).map(([v, l]) => (
                <button key={v} onClick={() => setFilter(v)}
                  className={`px-3 py-2 text-[12.5px] font-medium rounded-lg transition-colors ${
                    filter === v ? 'btn-primary-app' : 'card border-app text-dim bg-hover'
                  }`}>
                  {l}
                </button>
              ))}
            </div>
          </div>

          {/* Table */}
          <div className="card overflow-hidden overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-app">
                  {['SKU', 'Platform', 'Available', 'Reserved', 'Warehouse', 'Status'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => {
                  const status = getStockStatus(item.available_quantity)
                  const barColor = getStockBarColor(item.available_quantity)
                  const pct = Math.min((item.available_quantity / (LOW_STOCK_THRESHOLD * 2)) * 100, 100)
                  return (
                    <tr key={item.sku} className="border-b border-app bg-hover transition-colors">
                      <td className="px-4 py-3.5">
                        <span className="text-[12px] font-mono-app font-medium text-app">{item.sku}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="badge bg-surface text-dim">{PLATFORM_LABELS[item.platform as keyof typeof PLATFORM_LABELS] ?? item.platform}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-1.5 bg-surface rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
                          </div>
                          <span className={`text-[12.5px] font-semibold ${item.available_quantity === 0 ? 'text-accent-red' : item.available_quantity < LOW_STOCK_THRESHOLD ? 'text-accent-amber' : 'text-app'}`}>
                            {item.available_quantity}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-[12px] text-dim">{item.reserved_quantity}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-[12px] text-dim">{item.warehouse ?? '—'}</span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className={`badge ${status.color}`}>{status.label}</span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="text-center py-12 text-faint text-[13px]">No items match your search.</div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

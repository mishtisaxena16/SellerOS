import { useEffect, useMemo, useState } from 'react'
import { Search, Package, Truck, CheckCircle, Clock, RotateCcw, ChevronRight, AlertTriangle, Loader2 } from 'lucide-react'
import { usePlatform, PLATFORM_LABELS } from '../context/PlatformContext'
import { getOrders, type OrderRecord } from '../api/orders'
import { ApiError } from '../api/client'
import EmptyMarketplaceState from '../components/EmptyMarketplaceState'

// Backend order.status is a free-text string straight from each
// marketplace connector (varies by platform), so we bucket the common
// ones for the summary strip and fall back to a generic look for
// anything we don't recognize instead of hiding it.
const STATUS_CONFIG: Record<string, { label: string; color: string; icon: typeof Clock }> = {
  pending: { label: 'Pending', color: 'bg-accent-blue-soft text-accent-blue', icon: Clock },
  unshipped: { label: 'Unshipped', color: 'bg-accent-blue-soft text-accent-blue', icon: Clock },
  processing: { label: 'Processing', color: 'bg-accent-amber-soft text-accent-amber', icon: Package },
  shipped: { label: 'Shipped', color: 'bg-accent-purple-soft text-accent-purple', icon: Truck },
  delivered: { label: 'Delivered', color: 'bg-accent-green-soft text-accent-green', icon: CheckCircle },
  returned: { label: 'Returned', color: 'bg-accent-red-soft text-accent-red', icon: RotateCcw },
  cancelled: { label: 'Cancelled', color: 'bg-accent-red-soft text-accent-red', icon: RotateCcw },
}
const DEFAULT_STATUS = { label: 'Other', color: 'bg-surface text-dim', icon: Package }
const cfgFor = (status: string) => STATUS_CONFIG[status.toLowerCase()] ?? DEFAULT_STATUS

const mktColor: Record<string, string> = {
  amazon: 'bg-accent-amber-soft text-accent-amber',
  flipkart: 'bg-accent-blue-soft text-accent-blue',
  meesho: 'bg-accent-purple-soft text-accent-purple',
}

export default function Orders() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedOrder, setSelectedOrder] = useState<OrderRecord | null>(null)
  const { selected } = usePlatform()

  const [orders, setOrders] = useState<OrderRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<{ status: number; message: string } | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setSelectedOrder(null)
    getOrders(selected)
      .then(res => {
        if (cancelled) return
        if (!res.success) {
          setError({ status: 200, message: res.message || 'Orders could not be fetched.' })
          setOrders([])
        } else {
          setOrders(res.orders)
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const apiErr = err instanceof ApiError ? err : null
        setError({ status: apiErr?.status ?? 0, message: apiErr?.message ?? 'Could not reach the SellerOS API.' })
        setOrders([])
      })
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }, [selected])

  const filtered = useMemo(() => orders.filter(o => {
    const matchSearch = o.order_id.toLowerCase().includes(search.toLowerCase())
    const matchStatus = statusFilter === 'all' || o.status.toLowerCase() === statusFilter
    return matchSearch && matchStatus
  }), [orders, search, statusFilter])

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    orders.forEach(o => {
      const key = o.status.toLowerCase()
      counts[key] = (counts[key] || 0) + 1
    })
    return counts
  }, [orders])

  if (error && error.status === 409) {
    return <EmptyMarketplaceState message={error.message} />
  }

  return (
    <div className="p-6 fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-app">Orders</h2>
          <p className="text-[13px] text-dim mt-0.5">
            {loading ? 'Loading…' : `${orders.length} orders ${selected === 'all' ? '' : `on ${PLATFORM_LABELS[selected]}`}`}
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
          <Loader2 size={16} className="animate-spin" /> Loading orders…
        </div>
      ) : (
        <>
          {/* Status summary */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
            {Object.entries(statusCounts).map(([key, count]) => {
              const cfg = cfgFor(key)
              const Icon = cfg.icon
              return (
                <button
                  key={key}
                  onClick={() => setStatusFilter(statusFilter === key ? 'all' : key)}
                  className={`card p-4 text-left transition-all ${statusFilter === key ? 'border-app-hover' : ''}`}
                  style={statusFilter === key ? { borderColor: 'var(--blue)' } : undefined}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 ${cfg.color}`}>
                    <Icon size={15} />
                  </div>
                  <div className="text-xl font-bold text-app">{count}</div>
                  <div className="text-[12px] text-dim capitalize">{cfg.label !== 'Other' ? cfg.label : key}</div>
                </button>
              )
            })}
            {Object.keys(statusCounts).length === 0 && (
              <div className="col-span-full text-[13px] text-faint">No orders yet for this marketplace.</div>
            )}
          </div>

          <div className="flex flex-col lg:flex-row gap-5">
            {/* Table */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-4">
                <div className="relative flex-1 max-w-sm">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
                  <input
                    value={search} onChange={e => setSearch(e.target.value)}
                    placeholder="Search by order ID..."
                    className="input-app w-full pl-9 pr-4 py-2 text-[13px]"
                  />
                </div>
                <span className="text-[12.5px] text-faint">{filtered.length} results</span>
              </div>

              <div className="card overflow-hidden overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-app">
                      {['Order ID', 'Items', 'Amount', 'Platform', 'Status', 'Date', ''].map(h => (
                        <th key={h} className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map(order => {
                      const cfg = cfgFor(order.status)
                      return (
                        <tr key={order.order_id} className="border-b border-app bg-hover transition-colors cursor-pointer" onClick={() => setSelectedOrder(selectedOrder?.order_id === order.order_id ? null : order)}>
                          <td className="px-4 py-3.5">
                            <span className="text-[12.5px] font-mono-app font-medium text-accent-blue">{order.order_id}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <div className="text-[12.5px] text-dim">{order.items.length} item{order.items.length === 1 ? '' : 's'}</div>
                            <div className="text-[11px] text-faint truncate max-w-[160px]">{order.items.map(it => it.sku).join(', ') || '—'}</div>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className="text-[13px] font-semibold text-app">
                              {order.total_amount != null ? `₹${order.total_amount.toLocaleString('en-IN')}` : '—'}
                            </span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className={`badge ${mktColor[order.platform] ?? 'bg-surface text-dim'}`}>{PLATFORM_LABELS[order.platform as keyof typeof PLATFORM_LABELS] ?? order.platform}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className={`badge ${cfg.color}`}>{cfg.label !== 'Other' ? cfg.label : order.status}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className="text-[12px] text-dim">{order.order_date ? new Date(order.order_date).toLocaleDateString('en-IN') : '—'}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <ChevronRight size={14} className="text-faint" />
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
                {filtered.length === 0 && (
                  <div className="text-center py-12 text-faint text-[13px]">No orders match your search.</div>
                )}
              </div>
            </div>

            {/* Detail panel */}
            {selectedOrder && (
              <div className="w-full lg:w-72 flex-shrink-0 card p-5 fade-in">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-[13.5px] font-semibold text-app">{selectedOrder.order_id}</h3>
                  <span className={`badge ${cfgFor(selectedOrder.status).color}`}>
                    {cfgFor(selectedOrder.status).label !== 'Other' ? cfgFor(selectedOrder.status).label : selectedOrder.status}
                  </span>
                </div>
                <div className="space-y-3 text-[12.5px]">
                  <div className="p-3 bg-surface rounded-lg">
                    <div className="text-faint text-[11px] mb-1">Items</div>
                    {selectedOrder.items.map(it => (
                      <div key={it.sku} className="flex justify-between text-dim">
                        <span>{it.sku} × {it.quantity}</span>
                        <span>{it.unit_price != null ? `₹${it.unit_price.toLocaleString('en-IN')}` : '—'}</span>
                      </div>
                    ))}
                  </div>
                  <div className="p-3 bg-surface rounded-lg">
                    <div className="text-faint text-[11px] mb-1">Order Details</div>
                    <div className="flex justify-between"><span className="text-dim">Amount</span><span className="font-semibold text-app">{selectedOrder.total_amount != null ? `₹${selectedOrder.total_amount.toLocaleString('en-IN')}` : '—'}</span></div>
                    <div className="flex justify-between mt-1"><span className="text-dim">Platform</span><span className={`badge ${mktColor[selectedOrder.platform] ?? 'bg-surface text-dim'}`}>{PLATFORM_LABELS[selectedOrder.platform as keyof typeof PLATFORM_LABELS] ?? selectedOrder.platform}</span></div>
                    <div className="flex justify-between mt-1"><span className="text-dim">Date</span><span className="text-dim">{selectedOrder.order_date ? new Date(selectedOrder.order_date).toLocaleDateString('en-IN') : '—'}</span></div>
                    {selectedOrder.customer_state && (
                      <div className="flex justify-between mt-1"><span className="text-dim">State</span><span className="text-dim">{selectedOrder.customer_state}</span></div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

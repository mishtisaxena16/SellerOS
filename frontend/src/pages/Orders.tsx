import { useEffect, useMemo, useState } from 'react'
import { Search, Package, Truck, CheckCircle, Clock, RotateCcw, ChevronRight, ChevronLeft, AlertTriangle, Loader2, ArrowUpDown, Info } from 'lucide-react'
import { usePlatform, PLATFORM_LABELS } from '../context/PlatformContext'
import { useOrdersData, type OrderViewRow } from '../hooks/useOrdersData'
import EmptyMarketplaceState from '../components/EmptyMarketplaceState'

// Shipping status drives the summary strip + row badge, same bucket set
// the page always used (delivered/shipped/processing/cancelled/returned),
// just now sourced from the unified OrderViewRow instead of the raw
// backend string.
const STATUS_CONFIG: Record<string, { label: string; color: string; icon: typeof Clock }> = {
  processing: { label: 'Processing', color: 'bg-accent-amber-soft text-accent-amber', icon: Package },
  shipped: { label: 'Shipped', color: 'bg-accent-purple-soft text-accent-purple', icon: Truck },
  delivered: { label: 'Delivered', color: 'bg-accent-green-soft text-accent-green', icon: CheckCircle },
  returned: { label: 'Returned', color: 'bg-accent-red-soft text-accent-red', icon: RotateCcw },
  cancelled: { label: 'Cancelled', color: 'bg-accent-red-soft text-accent-red', icon: RotateCcw },
}
const DEFAULT_STATUS = { label: 'Other', color: 'bg-surface text-dim', icon: Package }
const cfgFor = (status: string) => STATUS_CONFIG[status.toLowerCase()] ?? DEFAULT_STATUS

const paymentColor = (status: OrderViewRow['paymentStatus']) =>
  status === 'Paid' ? 'bg-accent-green-soft text-accent-green' : 'bg-accent-red-soft text-accent-red'

const mktColor: Record<string, string> = {
  Amazon: 'bg-accent-amber-soft text-accent-amber',
  Flipkart: 'bg-accent-blue-soft text-accent-blue',
  Meesho: 'bg-accent-purple-soft text-accent-purple',
}

type SortKey = 'orderDate' | 'orderValue'
const PAGE_SIZE = 20

export default function Orders() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedOrder, setSelectedOrder] = useState<OrderViewRow | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>('orderDate')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const { selected } = usePlatform()

  const { rows: orders, loading, error, usingMockData } = useOrdersData(selected)

  // Reset to page 1 whenever the visible set could change shape.
  useEffect(() => { setPage(1) }, [search, statusFilter, sortKey, sortDir, selected])
  useEffect(() => { setSelectedOrder(null) }, [selected])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    const matches = orders.filter(o => {
      const matchSearch = !q ||
        o.id.toLowerCase().includes(q) ||
        o.orderNumber.toLowerCase().includes(q) ||
        o.customerName.toLowerCase().includes(q) ||
        o.product.toLowerCase().includes(q)
      const matchStatus = statusFilter === 'all' || o.shippingStatus.toLowerCase() === statusFilter
      return matchSearch && matchStatus
    })
    const sorted = [...matches].sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1
      if (sortKey === 'orderValue') return (a.orderValue - b.orderValue) * dir
      return (a.orderDate < b.orderDate ? -1 : a.orderDate > b.orderDate ? 1 : 0) * dir
    })
    return sorted
  }, [orders, search, statusFilter, sortKey, sortDir])

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    orders.forEach(o => {
      const key = o.shippingStatus.toLowerCase()
      counts[key] = (counts[key] || 0) + 1
    })
    return counts
  }, [orders])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const pageRows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setSortDir('desc') }
  }

  if (error && error.status === 409 && !usingMockData) {
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

      {usingMockData && !loading && (
        <div className="mb-4 p-3 rounded-lg bg-accent-blue-soft text-accent-blue text-[13px] flex items-center gap-2">
          <Info size={14} /> Showing historical demo orders for ABC Fashion Store — connect a marketplace to see live orders instead.
        </div>
      )}

      {error && !usingMockData && (
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
                    placeholder="Search by order ID, customer, or product..."
                    className="input-app w-full pl-9 pr-4 py-2 text-[13px]"
                  />
                </div>
                <span className="text-[12.5px] text-faint whitespace-nowrap">{filtered.length} results</span>
              </div>

              <div className="card overflow-hidden overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-app">
                      {['Order ID', 'Customer', 'Product', 'Qty', 'Marketplace', 'Delivery', 'Payment', 'Shipping'].map(h => (
                        <th key={h} className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">{h}</th>
                      ))}
                      <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">
                        <button className="inline-flex items-center gap-1 hover:text-app" onClick={() => toggleSort('orderDate')}>
                          Date <ArrowUpDown size={11} className={sortKey === 'orderDate' ? 'text-accent-blue' : ''} />
                        </button>
                      </th>
                      <th className="text-left px-4 py-3 text-[11.5px] font-semibold text-faint uppercase tracking-wide whitespace-nowrap">
                        <button className="inline-flex items-center gap-1 hover:text-app" onClick={() => toggleSort('orderValue')}>
                          Value <ArrowUpDown size={11} className={sortKey === 'orderValue' ? 'text-accent-blue' : ''} />
                        </button>
                      </th>
                      <th className="px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody>
                    {pageRows.map(order => {
                      const cfg = cfgFor(order.shippingStatus)
                      return (
                        <tr key={order.id} className="border-b border-app bg-hover transition-colors cursor-pointer" onClick={() => setSelectedOrder(selectedOrder?.id === order.id ? null : order)}>
                          <td className="px-4 py-3.5">
                            <span className="text-[12.5px] font-mono-app font-medium text-accent-blue">{order.id}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <div className="text-[12.5px] text-app">{order.customerName}</div>
                            <div className="text-[11px] text-faint">{order.customerLocation}</div>
                          </td>
                          <td className="px-4 py-3.5">
                            <div className="text-[12.5px] text-dim truncate max-w-[180px]">{order.product}</div>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className="text-[12.5px] text-dim">{order.quantity}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className={`badge ${mktColor[order.marketplace] ?? 'bg-surface text-dim'}`}>{order.marketplace}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className="text-[12px] text-dim">{order.deliveryStatus}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className={`badge ${paymentColor(order.paymentStatus)}`}>{order.paymentStatus}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className={`badge ${cfg.color}`}>{order.shippingStatus}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className="text-[12px] text-dim whitespace-nowrap">{order.orderDate ? new Date(order.orderDate).toLocaleDateString('en-IN') : '—'}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className="text-[13px] font-semibold text-app whitespace-nowrap">₹{order.orderValue.toLocaleString('en-IN')}</span>
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

              {filtered.length > PAGE_SIZE && (
                <div className="flex items-center justify-between mt-3">
                  <span className="text-[12px] text-faint">
                    Page {page} of {pageCount}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="card border-app bg-hover px-2.5 py-1.5 text-dim disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft size={14} />
                    </button>
                    <button
                      onClick={() => setPage(p => Math.min(pageCount, p + 1))}
                      disabled={page === pageCount}
                      className="card border-app bg-hover px-2.5 py-1.5 text-dim disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Detail panel */}
            {selectedOrder && (
              <div className="w-full lg:w-72 flex-shrink-0 card p-5 fade-in">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-[13.5px] font-semibold text-app">{selectedOrder.id}</h3>
                  <span className={`badge ${cfgFor(selectedOrder.shippingStatus).color}`}>
                    {selectedOrder.shippingStatus}
                  </span>
                </div>
                <div className="space-y-3 text-[12.5px]">
                  <div className="p-3 bg-surface rounded-lg">
                    <div className="text-faint text-[11px] mb-1">Customer</div>
                    <div className="text-app font-medium">{selectedOrder.customerName}</div>
                    <div className="text-dim text-[11.5px]">{selectedOrder.customerLocation}</div>
                  </div>
                  <div className="p-3 bg-surface rounded-lg">
                    <div className="text-faint text-[11px] mb-1">Items</div>
                    {selectedOrder.items.map((it, i) => (
                      <div key={`${it.sku}-${i}`} className="flex justify-between text-dim">
                        <span>{it.name} × {it.quantity}</span>
                        <span>₹{it.unitPrice.toLocaleString('en-IN')}</span>
                      </div>
                    ))}
                  </div>
                  <div className="p-3 bg-surface rounded-lg">
                    <div className="text-faint text-[11px] mb-1">Order Details</div>
                    <div className="flex justify-between"><span className="text-dim">Amount</span><span className="font-semibold text-app">₹{selectedOrder.orderValue.toLocaleString('en-IN')}</span></div>
                    <div className="flex justify-between mt-1"><span className="text-dim">Marketplace</span><span className={`badge ${mktColor[selectedOrder.marketplace] ?? 'bg-surface text-dim'}`}>{selectedOrder.marketplace}</span></div>
                    <div className="flex justify-between mt-1"><span className="text-dim">Payment</span><span className={`badge ${paymentColor(selectedOrder.paymentStatus)}`}>{selectedOrder.paymentStatus}</span></div>
                    <div className="flex justify-between mt-1"><span className="text-dim">Delivery</span><span className="text-dim">{selectedOrder.deliveryStatus}</span></div>
                    <div className="flex justify-between mt-1"><span className="text-dim">Date</span><span className="text-dim">{selectedOrder.orderDate ? new Date(selectedOrder.orderDate).toLocaleDateString('en-IN') : '—'}</span></div>
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

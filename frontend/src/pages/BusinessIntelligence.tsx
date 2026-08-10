import { useEffect, useMemo, useState } from 'react'
import { TrendingUp, Package, Truck, Clock, AlertCircle, Loader2, PieChart, RotateCcw, BarChart3 } from 'lucide-react'
import { usePlatform, PLATFORM_LABELS } from '../context/PlatformContext'
import { getOrders, type OrderRecord } from '../api/orders'
import { getInventory, type InventoryItem } from '../api/inventory'
import { useAnalyticsData } from '../hooks/useAnalyticsData'
import EmptyMarketplaceState from '../components/EmptyMarketplaceState'
import TrendChartCard from '../components/TrendChartCard'
import { mockOrderRows } from '../mock/ordersView'

function getMockOrdersForTrend(selected: 'all' | 'amazon' | 'flipkart' | 'meesho'): OrderRecord[] {
  // The demo dataset represents an Amazon seller. It is shown for the All
  // Platforms and Amazon views, but never misrepresented as Flipkart/Meesho data.
  if (selected !== 'all' && selected !== 'amazon') return []

  return mockOrderRows.map(order => ({
    platform: 'amazon',
    order_id: order.id,
    status: order.shippingStatus,
    items: order.items.map(item => ({ sku: item.sku, quantity: item.quantity, unit_price: item.unitPrice })),
    total_amount: order.orderValue,
    currency: 'INR',
    order_date: order.orderDate,
    customer_state: order.customerLocation,
    raw: {},
  }))
}

const CANCELLED_STATUSES = new Set(['cancelled', 'canceled', 'returned', 'rejected'])

export default function BusinessIntelligence() {
  const { selected, connectedPlatforms } = usePlatform()
  const [orders, setOrders] = useState<OrderRecord[]>([])
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [pageLoading, setPageLoading] = useState(true)
  const [usingMockOrders, setUsingMockOrders] = useState(false)
  // Tracks orders/inventory fetch failures separately from the analytics
  // error surfaced by useAnalyticsData below. Previously these were
  // swallowed silently — a failed /orders or /inventory call just left the
  // arrays empty, so every section derived from them (trend charts, status
  // breakdown, SKU lists) quietly rendered its "no orders yet" empty state
  // instead of telling the user their data actually failed to load.
  const [derivedDataError, setDerivedDataError] = useState(false)

  // Sales/business metrics come from the shared analytics hook — it tries
  // the live backend first and falls back to the Phase 7.1 mock dataset
  // (itself derived from orders, products, and inventory — see
  // mock/businessIntelligenceView.ts) whenever live analytics aren't
  // available for this platform, same as Dashboard.tsx.
  const { data: analytics, loading: analyticsLoading, error: analyticsError } = useAnalyticsData(selected)
  const loading = pageLoading || analyticsLoading

  useEffect(() => {
    let cancelled = false
    setPageLoading(true)
    setDerivedDataError(false)
    // Reset — not just on success — so switching the platform filter and
    // then hitting a fetch error doesn't leave the previous platform's
    // data on screen looking like it belongs to the newly selected one.
    setOrders([])
    setInventory([])
    setUsingMockOrders(false)

    Promise.allSettled([
      getOrders(selected),
      getInventory(selected),
    ]).then(([ordersRes, inventoryRes]) => {
      if (cancelled) return
      const fallbackOrders = getMockOrdersForTrend(selected)
      if (ordersRes.status === 'fulfilled' && ordersRes.value.success && ordersRes.value.orders.length > 0) {
        setOrders(ordersRes.value.orders)
      } else if (fallbackOrders.length > 0) {
        // Demo analytics uses the same deterministic order dataset as the
        // mock KPI cards, so trends and totals stay consistent.
        setOrders(fallbackOrders)
        setUsingMockOrders(true)
      }
      if (inventoryRes.status === 'fulfilled' && inventoryRes.value.success) setInventory(inventoryRes.value.items)

      const ordersFailed = (ordersRes.status === 'rejected' || (ordersRes.status === 'fulfilled' && !ordersRes.value.success)) && fallbackOrders.length === 0
      const inventoryFailed = inventoryRes.status === 'rejected' || (inventoryRes.status === 'fulfilled' && !inventoryRes.value.success)
      if (ordersFailed || inventoryFailed) setDerivedDataError(true)
    }).finally(() => !cancelled && setPageLoading(false))

    return () => { cancelled = true }
  }, [selected])

  // --- Everything below is computed client-side from the same orders/
  // inventory data Orders and Inventory pages already show — no new
  // backend endpoint, just real arithmetic instead of invented charts.

  const statusBreakdown = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const o of orders) counts[o.status] = (counts[o.status] ?? 0) + 1
    return Object.entries(counts).sort((a, b) => b[1] - a[1])
  }, [orders])

  const cancellationRate = useMemo(() => {
    if (orders.length === 0) return null
    const cancelled = orders.filter(o => CANCELLED_STATUSES.has(o.status.toLowerCase())).length
    return (cancelled / orders.length) * 100
  }, [orders])

  const platformSplit = useMemo(() => {
    if (selected !== 'all' || connectedPlatforms.length < 2 || orders.length === 0) return []
    const byPlatform: Record<string, { count: number; revenue: number }> = {}
    for (const o of orders) {
      const p = byPlatform[o.platform] ?? { count: 0, revenue: 0 }
      p.count += 1
      p.revenue += o.total_amount ?? 0
      byPlatform[o.platform] = p
    }
    const totalRevenue = Object.values(byPlatform).reduce((s, p) => s + p.revenue, 0)
    return Object.entries(byPlatform)
      .map(([platform, v]) => ({ platform, ...v, share: totalRevenue > 0 ? (v.revenue / totalRevenue) * 100 : 0 }))
      .sort((a, b) => b.revenue - a.revenue)
  }, [orders, selected, connectedPlatforms])

  const topSkus = useMemo(() => {
    const bySku: Record<string, number> = {}
    for (const o of orders) {
      for (const item of o.items) {
        bySku[item.sku] = (bySku[item.sku] ?? 0) + item.quantity
      }
    }
    return Object.entries(bySku).sort((a, b) => b[1] - a[1]).slice(0, 5)
  }, [orders])

  // SKUs present in inventory that never showed up in any fetched order
  // line item — a signal worth a look, not a certified "dead stock"
  // verdict, since it's only as complete as what /orders returned.
  const noRecentSalesSkus = useMemo(() => {
    if (inventory.length === 0 || orders.length === 0) return []
    const soldSkus = new Set(orders.flatMap(o => o.items.map(i => i.sku)))
    return inventory.filter(i => i.available_quantity > 0 && !soldSkus.has(i.sku)).slice(0, 5)
  }, [inventory, orders])

  if (analyticsError?.status === 409) {
    return <EmptyMarketplaceState message={analyticsError.message} />
  }

  const sales = analytics.salesMetrics
  const business = analytics.businessMetrics
  const platformLabel = selected !== 'all'
    ? PLATFORM_LABELS[selected as keyof typeof PLATFORM_LABELS] ?? selected
    : undefined

  return (
    <div className="p-6 fade-in space-y-6">
      <div>
        <h2 className="text-xl font-bold text-app">Business Intelligence</h2>
        <p className="text-[13px] text-dim mt-0.5">
          {loading ? 'Loading…' : `Live metrics ${platformLabel ? `for ${platformLabel}` : ''}`}
        </p>
      </div>

      {analyticsError && analyticsError.status !== 409 && (
        <div className="p-3 rounded-lg bg-accent-red-soft text-accent-red text-[13px] flex items-center gap-2">
          <AlertCircle size={14} /> {analyticsError.message}
        </div>
      )}

      {!loading && derivedDataError && (
        <div className="p-3 rounded-lg bg-accent-red-soft text-accent-red text-[13px] flex items-center gap-2">
          <AlertCircle size={14} /> Some order or inventory data couldn't be loaded, so trends, status breakdown, and SKU sections below may be incomplete.
        </div>
      )}

      {loading ? (
        <div className="card p-12 flex items-center justify-center gap-2 text-dim text-[13px]">
          <Loader2 size={16} className="animate-spin" /> Loading analytics…
        </div>
      ) : (
        <>
          {/* Sales metrics */}
          <div className="card p-5">
            <h3 className="text-[14px] font-semibold text-app mb-1">Sales Metrics</h3>
            {sales ? (
              <>
                <p className="text-[12px] text-faint mb-4">{sales.timeframe} · {sales.currency}</p>
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="flex items-center gap-2 mb-2 text-accent-blue"><TrendingUp size={16} /><span className="text-[12px] text-dim">Total Revenue</span></div>
                    <div className="text-xl font-bold text-app">₹{sales.totalRevenue.toLocaleString('en-IN')}</div>
                  </div>
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="flex items-center gap-2 mb-2 text-accent-green"><Package size={16} /><span className="text-[12px] text-dim">Total Orders</span></div>
                    <div className="text-xl font-bold text-app">{sales.totalOrders}</div>
                  </div>
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="flex items-center gap-2 mb-2 text-accent-amber"><TrendingUp size={16} /><span className="text-[12px] text-dim">Avg. Order Value</span></div>
                    <div className="text-xl font-bold text-app">₹{sales.averageOrderValue.toLocaleString('en-IN')}</div>
                  </div>
                </div>
              </>
            ) : (
              <p className="text-[13px] text-faint">{analytics.salesMetricsMessage ?? 'Not available for this marketplace yet.'}</p>
            )}
          </div>

          {/* Business metrics */}
          <div className="card p-5">
            <h3 className="text-[14px] font-semibold text-app mb-1">Fulfillment</h3>
            {business ? (
              <>
                <p className="text-[12px] text-faint mb-4">{sales?.timeframe ?? 'All available data'}</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="flex items-center gap-2 mb-2 text-accent-purple"><Truck size={16} /><span className="text-[12px] text-dim">Shipped Orders</span></div>
                    <div className="text-xl font-bold text-app">{business.shippedOrders}</div>
                  </div>
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="flex items-center gap-2 mb-2 text-accent-blue"><Clock size={16} /><span className="text-[12px] text-dim">Pending Orders</span></div>
                    <div className="text-xl font-bold text-app">{business.pendingOrders}</div>
                  </div>
                </div>
              </>
            ) : (
              <p className="text-[13px] text-faint">{analytics.businessMetricsMessage ?? 'Not available for this marketplace yet.'}</p>
            )}
          </div>

          {/* Revenue & orders trend — real per-day totals computed from the
              same /orders data below (order_date + total_amount), not a
              recharts dependency or an invented series. Renders a grey
              skeleton while loading and an honest empty state at zero
              orders, instead of removing the chart outright. */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <TrendChartCard title="Revenue Trend" orders={orders} loading={loading} metric="revenue" isMockData={usingMockOrders} />
            <TrendChartCard title="Orders Trend" orders={orders} loading={loading} metric="orders" isMockData={usingMockOrders} />
          </div>

          {/* Order status breakdown + cancellation rate — real, computed
              from the same /orders data the Orders page shows. */}
          {orders.length > 0 && (
            <div className="card p-5">
              <h3 className="text-[14px] font-semibold text-app mb-1">Order Status Breakdown</h3>
              <p className="text-[12px] text-faint mb-4">Across {orders.length} order{orders.length === 1 ? '' : 's'} currently synced{selected !== 'all' ? ` for ${PLATFORM_LABELS[selected]}` : ''}</p>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
                {statusBreakdown.map(([status, count]) => (
                  <div key={status} className="p-3 bg-surface rounded-lg">
                    <div className="text-[11.5px] text-dim capitalize">{status}</div>
                    <div className="text-lg font-bold text-app">{count}</div>
                  </div>
                ))}
              </div>
              {cancellationRate !== null && (
                <div className="flex items-center gap-2 text-[12.5px]">
                  <RotateCcw size={14} className={cancellationRate > 10 ? 'text-accent-red' : 'text-accent-green'} />
                  <span className="text-dim">Cancellation / return rate:</span>
                  <span className={`font-semibold ${cancellationRate > 10 ? 'text-accent-red' : 'text-accent-green'}`}>{cancellationRate.toFixed(1)}%</span>
                </div>
              )}
            </div>
          )}

          {/* Marketplace revenue split — only meaningful with "All
              marketplaces" selected and more than one actually connected. */}
          {platformSplit.length > 0 && (
            <div className="card p-5">
              <h3 className="text-[14px] font-semibold text-app mb-1 flex items-center gap-2"><PieChart size={15} /> Marketplace Split</h3>
              <p className="text-[12px] text-faint mb-4">Share of revenue by marketplace, from your synced orders</p>
              <div className="space-y-3">
                {platformSplit.map(p => (
                  <div key={p.platform}>
                    <div className="flex justify-between text-[12.5px] mb-1">
                      <span className="text-app font-medium">{PLATFORM_LABELS[p.platform as keyof typeof PLATFORM_LABELS] ?? p.platform}</span>
                      <span className="text-dim">₹{p.revenue.toLocaleString('en-IN')} · {p.count} orders · {p.share.toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                      <div className="h-full bg-accent-blue rounded-full" style={{ width: `${p.share}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top SKUs + slow-moving stock signal — both derived from
              cross-referencing orders and inventory, not a new endpoint. */}
          {(topSkus.length > 0 || noRecentSalesSkus.length > 0) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {topSkus.length > 0 && (
                <div className="card p-5">
                  <h3 className="text-[14px] font-semibold text-app mb-1 flex items-center gap-2"><BarChart3 size={15} /> Top SKUs by Units Sold</h3>
                  <p className="text-[12px] text-faint mb-4">From line items in your synced orders</p>
                  <div className="space-y-2.5">
                    {topSkus.map(([sku, qty]) => (
                      <div key={sku} className="flex items-center justify-between">
                        <span className="text-[12.5px] font-mono-app text-app truncate">{sku}</span>
                        <span className="text-[12px] text-dim whitespace-nowrap">{qty} units</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {noRecentSalesSkus.length > 0 && (
                <div className="card p-5">
                  <h3 className="text-[14px] font-semibold text-app mb-1">In Stock, No Orders Yet</h3>
                  <p className="text-[12px] text-faint mb-4">
                    In stock but absent from any line item in your currently synced orders — worth a
                    look, though this reflects only the order data returned right now, not full sales history.
                  </p>
                  <div className="space-y-2.5">
                    {noRecentSalesSkus.map(item => (
                      <div key={item.sku} className="flex items-center justify-between">
                        <span className="text-[12.5px] font-mono-app text-app truncate">{item.sku}</span>
                        <span className="text-[12px] text-dim whitespace-nowrap">{item.available_quantity} in stock</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!sales && !business && (
            <div className="card p-5 flex items-start gap-3">
              <AlertCircle size={16} className="text-accent-amber flex-shrink-0 mt-0.5" />
              <p className="text-[12.5px] text-dim">
                Sales and business metrics are currently only wired up for Amazon on the backend
                (<span className="font-mono-app text-[11.5px]">SALES_METRICS_FETCHERS</span> / <span className="font-mono-app text-[11.5px]">BUSINESS_METRICS_FETCHERS</span> in
                <span className="font-mono-app text-[11.5px]"> marketplace_connector.py</span> only register an Amazon fetcher). Flipkart and Meesho analytics
                need that fetcher added before this page can show real numbers for them.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

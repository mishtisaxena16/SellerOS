import { useEffect, useMemo, useState } from 'react'
import { TrendingUp, Package, Truck, Clock, AlertCircle, Loader2, PieChart, RotateCcw, BarChart3, Tag } from 'lucide-react'
import { usePlatform, PLATFORM_LABELS } from '../context/PlatformContext'
import { getAnalytics, type AnalyticsResponse } from '../api/analytics'
import { getOrders, type OrderRecord } from '../api/orders'
import { getInventory, type InventoryItem } from '../api/inventory'
import { ApiError } from '../api/client'
import EmptyMarketplaceState from '../components/EmptyMarketplaceState'
import TrendChartCard from '../components/TrendChartCard'
import { getMockBusinessSnapshot, type AIInsight } from '../data/mockBusinessData'
import BusinessSummary from '../components/BusinessSummary'
import BusinessHealthCard from '../components/BusinessHealthCard'
import WarningBanner from '../components/WarningBanner'
import MetricCard from '../components/MetricCard'
import InsightPanel from '../components/InsightPanel'
import RecommendationCard from '../components/RecommendationCard'
import ActionCenter from '../components/ActionCenter'

const CANCELLED_STATUSES = new Set(['cancelled', 'canceled', 'returned', 'rejected'])

export default function BusinessIntelligence() {
  const { selected, connectedPlatforms } = usePlatform()
  const [data, setData] = useState<AnalyticsResponse | null>(null)
  const [orders, setOrders] = useState<OrderRecord[]>([])
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<{ status: number; message: string } | null>(null)
  // Tracks orders/inventory fetch failures separately from the analytics
  // error above. Previously these were swallowed silently — a failed
  // /orders or /inventory call just left the arrays empty, so every
  // section derived from them (trend charts, status breakdown, SKU lists)
  // quietly rendered its "no orders yet" empty state instead of telling
  // the user their data actually failed to load.
  const [derivedDataError, setDerivedDataError] = useState(false)

  // Phase 5 — AI Business Intelligence layer. Pulled from an isolated mock
  // data module (see src/data/mockBusinessData.ts) so it can be swapped for
  // a real endpoint later without touching any component below.
  const businessSnapshot = useMemo(() => getMockBusinessSnapshot(), [])
  const [selectedInsight, setSelectedInsight] = useState<AIInsight | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setDerivedDataError(false)
    // Reset — not just on success — so switching the platform filter and
    // then hitting a fetch error doesn't leave the previous platform's
    // metrics on screen looking like they belong to the newly selected one.
    setData(null)
    setOrders([])
    setInventory([])

    Promise.allSettled([
      getAnalytics(selected),
      getOrders(selected),
      getInventory(selected),
    ]).then(([analyticsRes, ordersRes, inventoryRes]) => {
      if (cancelled) return
      if (analyticsRes.status === 'fulfilled') setData(analyticsRes.value)
      if (ordersRes.status === 'fulfilled' && ordersRes.value.success) setOrders(ordersRes.value.orders)
      if (inventoryRes.status === 'fulfilled' && inventoryRes.value.success) setInventory(inventoryRes.value.items)

      // The 409 "no marketplace connected" empty state only needs one
      // rejection to trigger, and analytics is the most reliable source of it.
      if (analyticsRes.status === 'rejected') {
        const err = analyticsRes.reason
        const apiErr = err instanceof ApiError ? err : null
        setError({ status: apiErr?.status ?? 0, message: apiErr?.message ?? 'Could not reach the SellerOS API.' })
      }

      const ordersFailed = ordersRes.status === 'rejected' || (ordersRes.status === 'fulfilled' && !ordersRes.value.success)
      const inventoryFailed = inventoryRes.status === 'rejected' || (inventoryRes.status === 'fulfilled' && !inventoryRes.value.success)
      if (ordersFailed || inventoryFailed) setDerivedDataError(true)
    }).finally(() => !cancelled && setLoading(false))

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

  if (error?.status === 409) {
    return <EmptyMarketplaceState message={error.message} />
  }

  const sales = data?.sales_metrics
  const business = data?.business_metrics
  const platformLabel = data?.platform
    ? PLATFORM_LABELS[data.platform as keyof typeof PLATFORM_LABELS] ?? data.platform
    : undefined

  return (
    <div className="p-6 fade-in space-y-6">
      <div>
        <h2 className="text-xl font-bold text-app">Business Intelligence</h2>
        <p className="text-[13px] text-dim mt-0.5">
          {loading ? 'Loading…' : `Live metrics ${platformLabel ? `for ${platformLabel}` : ''}`}
        </p>
      </div>

      {/* ================================================================
          Phase 5 — AI Business Intelligence
          Everything in this block reads from the isolated mock data layer
          (src/data/mockBusinessData.ts). It sits above the live marketplace
          metrics below, which are untouched and still backend-driven.
          ================================================================ */}
      <BusinessSummary summary={businessSnapshot.summary} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <BusinessHealthCard health={businessSnapshot.health} />
        </div>
        <div className="card p-5">
          <h3 className="text-[14px] font-semibold text-app mb-3">Smart Warnings</h3>
          <WarningBanner warnings={businessSnapshot.warnings} onSelect={(w) => setSelectedInsight(w.insight)} />
        </div>
      </div>

      <div>
        <h3 className="text-[14px] font-semibold text-app mb-3">AI-Powered Metrics</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
          {businessSnapshot.metrics.map((metric, i) => (
            <MetricCard key={metric.id} data={metric} onClick={(d) => setSelectedInsight(d.insight)} delay={i * 30} />
          ))}
        </div>
      </div>

      <div className="card p-5">
        <h3 className="text-[14px] font-semibold text-app mb-1">AI Recommendation Center</h3>
        <p className="text-[12px] text-faint mb-4">Prioritized actions with estimated impact and confidence</p>
        <div className="space-y-2.5">
          {businessSnapshot.recommendations.map(rec => (
            <RecommendationCard key={rec.id} recommendation={rec} />
          ))}
        </div>
      </div>

      <ActionCenter actions={businessSnapshot.quickActions} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="card p-5">
          <h3 className="text-[14px] font-semibold text-app mb-1 flex items-center gap-2"><Tag size={15} /> Top Categories</h3>
          <p className="text-[12px] text-faint mb-4">Demo data — revenue by category</p>
          <div className="space-y-2.5">
            {businessSnapshot.topCategories.map(cat => (
              <div key={cat.label} className="flex items-center justify-between">
                <span className="text-[12.5px] text-app">{cat.label}</span>
                <span className="text-[12px] text-dim">₹{cat.value.toLocaleString('en-IN')}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card p-5">
          <h3 className="text-[14px] font-semibold text-app mb-1 flex items-center gap-2"><BarChart3 size={15} /> Top Products</h3>
          <p className="text-[12px] text-faint mb-4">Demo data — units sold</p>
          <div className="space-y-2.5">
            {businessSnapshot.topProducts.map(p => (
              <div key={p.label} className="flex items-center justify-between">
                <span className="text-[12.5px] text-app truncate">{p.label}</span>
                <span className="text-[12px] text-dim whitespace-nowrap">{p.value} units</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <InsightPanel insight={selectedInsight} onClose={() => setSelectedInsight(null)} />

      <div className="border-t border-app pt-6">
        <h2 className="text-[15px] font-semibold text-app">Live Marketplace Data</h2>
        <p className="text-[12px] text-faint mt-0.5">Real numbers synced from your connected marketplace(s)</p>
      </div>

      {error && error.status !== 409 && (
        <div className="p-3 rounded-lg bg-accent-red-soft text-accent-red text-[13px] flex items-center gap-2">
          <AlertCircle size={14} /> {error.message}
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
                    <div className="text-xl font-bold text-app">₹{sales.total_revenue.toLocaleString('en-IN')}</div>
                  </div>
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="flex items-center gap-2 mb-2 text-accent-green"><Package size={16} /><span className="text-[12px] text-dim">Total Orders</span></div>
                    <div className="text-xl font-bold text-app">{sales.total_orders}</div>
                  </div>
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="flex items-center gap-2 mb-2 text-accent-amber"><TrendingUp size={16} /><span className="text-[12px] text-dim">Avg. Order Value</span></div>
                    <div className="text-xl font-bold text-app">₹{sales.average_order_value.toLocaleString('en-IN')}</div>
                  </div>
                </div>
                {sales.note && <p className="text-[11px] text-faint mt-3">{sales.note}</p>}
              </>
            ) : (
              <p className="text-[13px] text-faint">{data?.sales_metrics_message ?? 'Not available for this marketplace yet.'}</p>
            )}
          </div>

          {/* Business metrics */}
          <div className="card p-5">
            <h3 className="text-[14px] font-semibold text-app mb-1">Fulfillment</h3>
            {business ? (
              <>
                <p className="text-[12px] text-faint mb-4">{business.timeframe}</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="flex items-center gap-2 mb-2 text-accent-purple"><Truck size={16} /><span className="text-[12px] text-dim">Shipped Orders</span></div>
                    <div className="text-xl font-bold text-app">{business.shipped_orders}</div>
                  </div>
                  <div className="p-4 bg-surface rounded-lg">
                    <div className="flex items-center gap-2 mb-2 text-accent-blue"><Clock size={16} /><span className="text-[12px] text-dim">Pending Orders</span></div>
                    <div className="text-xl font-bold text-app">{business.pending_orders}</div>
                  </div>
                </div>
                {business.note && <p className="text-[11px] text-faint mt-3">{business.note}</p>}
              </>
            ) : (
              <p className="text-[13px] text-faint">{data?.business_metrics_message ?? 'Not available for this marketplace yet.'}</p>
            )}
          </div>

          {/* Revenue & orders trend — real per-day totals computed from the
              same /orders data below (order_date + total_amount), not a
              recharts dependency or an invented series. Renders a grey
              skeleton while loading and an honest empty state at zero
              orders, instead of removing the chart outright. */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <TrendChartCard title="Revenue Trend" orders={orders} loading={loading} metric="revenue" />
            <TrendChartCard title="Orders Trend" orders={orders} loading={loading} metric="orders" />
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

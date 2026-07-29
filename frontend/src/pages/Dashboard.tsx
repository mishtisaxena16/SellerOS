import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  TrendingUp, Package, ShoppingBag, RotateCcw, Sparkles, ArrowRight,
  AlertCircle, PlugZap, Wand2, MessageCircle, Loader2, Clock, Check, Circle,
  Store, Boxes, Activity, Award, Lightbulb, XCircle, CheckCircle2, Truck,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { usePlatform, PLATFORM_LABELS } from '../context/PlatformContext'
import { getDashboardSummary, type DashboardSummary } from '../api/dashboard'
import { getAnalytics, type AnalyticsResponse } from '../api/analytics'
import { getInventory, type InventoryItem } from '../api/inventory'
import { getOrders, type OrderRecord } from '../api/orders'
import { ApiError } from '../api/client'
import TrendChartCard from '../components/TrendChartCard'

const LOW_STOCK_THRESHOLD = 20

// Same status vocabulary as Business Intelligence's cancellation-rate calc —
// kept in sync deliberately so "cancelled" means the same thing on both pages.
const CANCELLED_STATUSES = new Set(['cancelled', 'canceled', 'returned', 'rejected'])
const PENDING_STATUSES = new Set(['pending', 'unshipped', 'processing'])

const PLATFORM_DOT_COLOR: Record<string, string> = {
  amazon: '#FF9900',
  flipkart: '#2874F0',
  meesho: '#9B2F8A',
}

function KPICard({
  label, value, icon: Icon, color, hint, delay = 0,
}: {
  label: string; value: string; icon: any; color: string; hint?: string; delay?: number
}) {
  return (
    <div className="card p-5 fade-in" style={{ animationDelay: `${delay}ms`, animationFillMode: 'backwards' }}>
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${color}`}>
        <Icon size={18} />
      </div>
      <div className="text-2xl font-bold text-app mb-0.5">{value}</div>
      <div className="text-[12.5px] text-dim">{label}</div>
      {hint && <div className="text-[11px] text-faint mt-1">{hint}</div>}
    </div>
  )
}

// Skeleton placeholders sized to match the real widgets they stand in for,
// so the layout doesn't jump once data arrives — each dashboard section
// gets its own loading state instead of one big spinner blocking everything.
function KPISkeleton() {
  return (
    <div className="card p-5">
      <div className="w-9 h-9 rounded-lg bg-surface animate-pulse mb-3" />
      <div className="h-6 w-16 bg-surface rounded animate-pulse mb-2" />
      <div className="h-3 w-24 bg-surface rounded animate-pulse" />
    </div>
  )
}

function SectionSkeleton({ title, lines = 4 }: { title?: string; lines?: number }) {
  return (
    <div className="card p-5">
      {title
        ? <h3 className="text-[14px] font-semibold text-app mb-4">{title}</h3>
        : <div className="h-4 w-32 bg-surface rounded animate-pulse mb-4" />}
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <div key={i} className="h-3 bg-surface rounded animate-pulse" style={{ width: `${74 - i * 9}%` }} />
        ))}
      </div>
    </div>
  )
}

// Lightweight progress nudge, not a gate — every step here is either already
// done or reachable from elsewhere in the app. It's informational, so it never
// blocks navigation the way onboarding's "Continue" button briefly did.
function GettingStarted({ userType, hasMarketplace }: { userType: 'new' | 'existing' | null; hasMarketplace: boolean }) {
  const steps = [
    { label: 'Create account', done: true },
    { label: 'Choose seller type', done: userType !== null },
    { label: 'Connect a marketplace', done: hasMarketplace },
    { label: 'Import listings', done: false },
  ]
  return (
    <div className="card p-5">
      <div className="text-[13px] font-semibold text-app mb-3">Getting started</div>
      <div className="flex flex-col gap-2.5">
        {steps.map(s => (
          <div key={s.label} className={`flex items-center gap-2.5 text-[13px] ${s.done ? 'text-app' : 'text-faint'}`}>
            {s.done
              ? <Check size={15} className="text-accent-green flex-shrink-0" />
              : <Circle size={15} className="text-faint flex-shrink-0" strokeWidth={1.5} />}
            {s.label}
          </div>
        ))}
      </div>
    </div>
  )
}

// Shown to brand-new sellers instead of forcing the onboarding flow —
// they can start exploring SellerOS before connecting anything.
//
// userType only changes *emphasis* here (copy + tile order), not *what data renders* —
// that's still gated on connectedPlatforms in Dashboard() below, because "do I have
// real inventory/order data to show" is a capability question, not an identity one.
// An "existing" seller who skipped connecting still sees the same empty KPI row an
// "existing" seller who chose "new" would; only the messaging around it differs.
function WelcomeState({ firstName, userType }: { firstName: string; userType: 'new' | 'existing' | null }) {
  const connectAction = {
    to: '/onboarding', icon: PlugZap, color: 'bg-accent-blue-soft text-accent-blue',
    title: 'Connect your first marketplace',
    desc: 'Link Amazon, Flipkart, or Meesho to start seeing real inventory, orders, and analytics here.',
  }
  const exploreActions = [
    {
      to: '/product-studio', icon: Wand2, color: 'bg-accent-purple-soft text-accent-purple',
      title: 'Explore Product Studio',
      desc: 'See how SellerOS helps you write and optimize listings before you connect a store.',
    },
    {
      to: '/seller-coach', icon: MessageCircle, color: 'bg-accent-green-soft text-accent-green',
      title: 'Chat with Seller Coach',
      desc: 'Ask questions about growing your marketplace business — no setup required.',
    },
  ]
  // Existing sellers who haven't connected yet (e.g. skipped) get the connect action
  // first — they told us they already sell somewhere, so that's the fastest path to
  // real data. New/unset sellers see the exploration options first instead.
  const actions = userType === 'existing' ? [connectAction, ...exploreActions] : [...exploreActions, connectAction]
  const heading = userType === 'existing'
    ? `👋 Welcome back, ${firstName} — let's connect your store`
    : `👋 Welcome to SellerOS, ${firstName}!`
  const subheading = userType === 'existing'
    ? "You mentioned you're already selling online — connect a marketplace to see your real numbers here."
    : "Here are a few ways to get started — pick whichever's useful first."
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card p-6 lg:col-span-2">
          <h2 className="text-xl font-bold text-app">{heading}</h2>
          <p className="text-[13.5px] text-dim mt-1.5">{subheading}</p>
        </div>
        <GettingStarted userType={userType} hasMarketplace={false} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {actions.map(a => (
          <Link key={a.to} to={a.to} className="card p-5 flex flex-col gap-3 border-app-hover transition-colors">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${a.color}`}>
              <a.icon size={18} />
            </div>
            <div>
              <div className="text-[13.5px] font-semibold text-app mb-1">{a.title}</div>
              <div className="text-[12px] text-dim leading-relaxed">{a.desc}</div>
            </div>
            <span className="text-[12px] text-accent-blue font-medium flex items-center gap-1 mt-auto">
              Go <ArrowRight size={12} />
            </span>
          </Link>
        ))}
      </div>
      <div>
        <div className="text-[13px] font-semibold text-app mb-3">Your dashboard</div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard label="Connected Marketplaces" value="0" icon={PlugZap} color="bg-surface text-faint" hint="None yet" />
          <KPICard label="Inventory Items" value="0" icon={Package} color="bg-surface text-faint" hint="Connect to sync" />
          <KPICard label="Pending Orders" value="0" icon={ShoppingBag} color="bg-surface text-faint" hint="Connect to sync" />
          <KPICard label="AI Assistant" value="Ready" icon={Sparkles} color="bg-accent-blue-soft text-accent-blue" hint="Try the chat bubble" />
        </div>
      </div>
    </div>
  )
}

function statusVisual(status: string) {
  const s = status.toLowerCase()
  if (CANCELLED_STATUSES.has(s)) return { Icon: XCircle, color: 'text-accent-red' }
  if (s === 'shipped' || s === 'delivered') return { Icon: Truck, color: 'text-accent-purple' }
  if (PENDING_STATUSES.has(s)) return { Icon: Clock, color: 'text-accent-amber' }
  return { Icon: CheckCircle2, color: 'text-accent-green' }
}

export default function Dashboard() {
  const { user, userType } = useAuth()
  const { selected, connectedPlatforms, loading: platformLoading } = usePlatform()
  const firstName = user?.business_name?.split(' ')[0] || user?.business_name || 'there'

  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null)
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [orders, setOrders] = useState<OrderRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // Tracks orders/inventory fetch failures separately from the summary error
  // above — mirrors Business Intelligence's pattern so a failed /orders or
  // /inventory call surfaces honestly instead of silently rendering every
  // derived section (trends, top products, stock alerts) as "no data yet".
  const [derivedDataError, setDerivedDataError] = useState(false)

  const hasMarketplace = connectedPlatforms.length > 0

  useEffect(() => {
    if (platformLoading) return
    if (!hasMarketplace) { setLoading(false); return }

    let cancelled = false
    setLoading(true)
    setError(null)
    setDerivedDataError(false)

    Promise.allSettled([
      getDashboardSummary(),
      getAnalytics(selected),
      getInventory(selected),
      getOrders(selected),
    ]).then(([summaryRes, analyticsRes, inventoryRes, ordersRes]) => {
      if (cancelled) return
      if (summaryRes.status === 'fulfilled') setSummary(summaryRes.value)
      if (analyticsRes.status === 'fulfilled') setAnalytics(analyticsRes.value)
      if (inventoryRes.status === 'fulfilled' && inventoryRes.value.success) setInventory(inventoryRes.value.items)
      if (ordersRes.status === 'fulfilled' && ordersRes.value.success) setOrders(ordersRes.value.orders)

      if (summaryRes.status === 'rejected') {
        const err = summaryRes.reason
        setError(err instanceof ApiError ? err.message : 'Could not load dashboard data.')
      }

      const ordersFailed = ordersRes.status === 'rejected' || (ordersRes.status === 'fulfilled' && !ordersRes.value.success)
      const inventoryFailed = inventoryRes.status === 'rejected' || (inventoryRes.status === 'fulfilled' && !inventoryRes.value.success)
      if (ordersFailed || inventoryFailed) setDerivedDataError(true)
    }).finally(() => !cancelled && setLoading(false))

    return () => { cancelled = true }
  }, [selected, hasMarketplace, platformLoading])

  const lowStockItems = useMemo(
    () => inventory
      .filter(i => i.available_quantity > 0 && i.available_quantity < LOW_STOCK_THRESHOLD)
      .sort((a, b) => a.available_quantity - b.available_quantity),
    [inventory]
  )
  const outOfStockCount = useMemo(() => inventory.filter(i => i.available_quantity === 0).length, [inventory])
  const healthyStockCount = useMemo(
    () => inventory.filter(i => i.available_quantity >= LOW_STOCK_THRESHOLD).length,
    [inventory]
  )
  const recentOrders = useMemo(() => orders.slice(0, 6), [orders])

  // --- Everything below is arithmetic over the same /orders and /inventory
  // data already fetched above — no new endpoints, just honest client-side
  // aggregation, and it only ever runs on data that actually loaded.

  const totalOrdersComputed = orders.length
  const totalRevenueComputed = useMemo(
    () => orders.reduce((sum, o) => sum + (o.total_amount ?? 0), 0),
    [orders]
  )
  const cancelledOrdersCount = useMemo(
    () => orders.filter(o => CANCELLED_STATUSES.has(o.status.toLowerCase())).length,
    [orders]
  )
  const pendingOrdersComputed = useMemo(
    () => orders.filter(o => PENDING_STATUSES.has(o.status.toLowerCase())).length,
    [orders]
  )
  const cancellationRate = orders.length > 0 ? (cancelledOrdersCount / orders.length) * 100 : null
  const avgOrderValue = analytics?.sales_metrics?.average_order_value
    ?? (totalOrdersComputed > 0 ? totalRevenueComputed / totalOrdersComputed : null)

  const marketplaceOverview = useMemo(() => {
    const byPlatform: Record<string, { count: number; revenue: number }> = {}
    for (const o of orders) {
      const p = byPlatform[o.platform] ?? { count: 0, revenue: 0 }
      p.count += 1
      p.revenue += o.total_amount ?? 0
      byPlatform[o.platform] = p
    }
    const totalRevenue = Object.values(byPlatform).reduce((s, p) => s + p.revenue, 0)
    return connectedPlatforms.map(platform => {
      const stats = byPlatform[platform] ?? { count: 0, revenue: 0 }
      return {
        platform,
        ...stats,
        share: totalRevenue > 0 ? (stats.revenue / totalRevenue) * 100 : 0,
      }
    }).sort((a, b) => b.revenue - a.revenue)
  }, [orders, connectedPlatforms])

  const topProducts = useMemo(() => {
    const bySku: Record<string, number> = {}
    for (const o of orders) {
      for (const item of o.items) {
        bySku[item.sku] = (bySku[item.sku] ?? 0) + item.quantity
      }
    }
    return Object.entries(bySku).sort((a, b) => b[1] - a[1]).slice(0, 5)
  }, [orders])

  const insights = useMemo(() => {
    const items: { icon: any; text: string; tone: string }[] = []
    if (avgOrderValue != null && totalOrdersComputed > 0) {
      items.push({
        icon: TrendingUp, tone: 'text-accent-blue',
        text: `Average order value is ₹${avgOrderValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}.`,
      })
    }
    if (cancellationRate != null) {
      items.push({
        icon: cancellationRate > 10 ? AlertCircle : CheckCircle2,
        tone: cancellationRate > 10 ? 'text-accent-red' : 'text-accent-green',
        text: `Cancellation / return rate is ${cancellationRate.toFixed(1)}%${cancellationRate > 10 ? ' — worth a look.' : '.'}`,
      })
    }
    const leader = marketplaceOverview.find(p => p.revenue > 0)
    if (leader && marketplaceOverview.length > 1) {
      items.push({
        icon: Store, tone: 'text-accent-purple',
        text: `${PLATFORM_LABELS[leader.platform as keyof typeof PLATFORM_LABELS] ?? leader.platform} leads with ₹${leader.revenue.toLocaleString('en-IN')} in synced revenue.`,
      })
    }
    if (lowStockItems.length > 0) {
      items.push({
        icon: Package, tone: 'text-accent-amber',
        text: `${lowStockItems.length} SKU${lowStockItems.length === 1 ? '' : 's'} running low on stock.`,
      })
    }
    if (outOfStockCount > 0) {
      items.push({
        icon: XCircle, tone: 'text-accent-red',
        text: `${outOfStockCount} SKU${outOfStockCount === 1 ? '' : 's'} completely out of stock.`,
      })
    }
    return items.slice(0, 4)
  }, [avgOrderValue, totalOrdersComputed, cancellationRate, marketplaceOverview, lowStockItems, outOfStockCount])

  if (platformLoading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <Loader2 size={18} className="animate-spin text-dim" />
      </div>
    )
  }

  if (!hasMarketplace) {
    return <div className="p-6 fade-in"><WelcomeState firstName={firstName} userType={userType} /></div>
  }

  return (
    <div className="p-6 space-y-6 fade-in">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-app">Good to see you, {firstName} 👋</h2>
          <p className="text-[13px] text-dim mt-0.5">
            {selected === 'all'
              ? "Here's what's happening across all your connected stores."
              : `Showing ${PLATFORM_LABELS[selected]} only.`}
          </p>
        </div>
      </div>

      {error && (
        <div className="card p-4 flex items-center gap-2 text-[13px] text-accent-red">
          <AlertCircle size={14} /> {error}
        </div>
      )}
      {!loading && derivedDataError && (
        <div className="card p-4 flex items-center gap-2 text-[13px] text-accent-red">
          <AlertCircle size={14} /> Some order or inventory data couldn't be loaded, so a few sections below may be incomplete.
        </div>
      )}

      {/* KPI row: Total Revenue, Total Orders, Pending Orders, Cancelled Orders —
          every value here prefers the live /analytics or /dashboard/summary figure
          and only falls back to a client-side computation over /orders when the
          backend has none for this platform, always labelled honestly via the hint. */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
          <>
            <KPISkeleton /><KPISkeleton /><KPISkeleton /><KPISkeleton />
          </>
        ) : (
          <>
            <KPICard
              delay={0}
              label="Total Revenue"
              value={
                analytics?.sales_metrics
                  ? `₹${(analytics.sales_metrics.total_revenue / 1000).toFixed(1)}k`
                  : totalOrdersComputed > 0 ? `₹${(totalRevenueComputed / 1000).toFixed(1)}k` : '—'
              }
              icon={TrendingUp} color="bg-accent-green-soft text-accent-green"
              hint={
                analytics?.sales_metrics
                  ? analytics.sales_metrics.timeframe
                  : totalOrdersComputed > 0
                    ? 'Computed from synced orders'
                    : (analytics?.sales_metrics_message ?? 'No orders synced yet')
              }
            />
            <KPICard
              delay={60}
              label="Total Orders"
              value={
                analytics?.sales_metrics
                  ? String(analytics.sales_metrics.total_orders)
                  : totalOrdersComputed > 0 ? String(totalOrdersComputed) : '—'
              }
              icon={ShoppingBag} color="bg-accent-blue-soft text-accent-blue"
              hint={totalOrdersComputed > 0 ? `Across ${connectedPlatforms.length} connected marketplace${connectedPlatforms.length === 1 ? '' : 's'}` : 'No orders synced yet'}
            />
            <KPICard
              delay={120}
              label="Pending Orders"
              value={
                summary?.pending_orders != null ? String(summary.pending_orders)
                  : analytics?.business_metrics ? String(analytics.business_metrics.pending_orders)
                    : totalOrdersComputed > 0 ? String(pendingOrdersComputed) : '—'
              }
              icon={Clock} color="bg-accent-amber-soft text-accent-amber"
            />
            <KPICard
              delay={180}
              label="Cancelled Orders"
              value={totalOrdersComputed > 0 ? String(cancelledOrdersCount) : '—'}
              icon={RotateCcw} color="bg-accent-red-soft text-accent-red"
              hint={cancellationRate != null ? `${cancellationRate.toFixed(1)}% of synced orders` : 'No orders synced yet'}
            />
          </>
        )}
      </div>

      {/* Inventory Summary / Marketplace Overview / Quick Business Insights */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {loading ? (
          <>
            <SectionSkeleton title="Inventory Summary" />
            <SectionSkeleton title="Marketplace Overview" />
            <SectionSkeleton title="Quick Business Insights" />
          </>
        ) : (
          <>
            <div className="card p-5">
              <h3 className="text-[14px] font-semibold text-app mb-4 flex items-center gap-2"><Boxes size={15} /> Inventory Summary</h3>
              {inventory.length === 0 ? (
                <p className="text-[12.5px] text-faint">No inventory synced yet{selected !== 'all' ? ` for ${PLATFORM_LABELS[selected]}` : ''}.</p>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-surface rounded-lg">
                    <div className="text-[11.5px] text-dim mb-1">Total SKUs</div>
                    <div className="text-lg font-bold text-app">{inventory.length}</div>
                  </div>
                  <div className="p-3 bg-surface rounded-lg">
                    <div className="text-[11.5px] text-dim mb-1">Healthy Stock</div>
                    <div className="text-lg font-bold text-accent-green">{healthyStockCount}</div>
                  </div>
                  <div className="p-3 bg-surface rounded-lg">
                    <div className="text-[11.5px] text-dim mb-1">Low Stock</div>
                    <div className="text-lg font-bold text-accent-amber">{lowStockItems.length}</div>
                  </div>
                  <div className="p-3 bg-surface rounded-lg">
                    <div className="text-[11.5px] text-dim mb-1">Out of Stock</div>
                    <div className="text-lg font-bold text-accent-red">{outOfStockCount}</div>
                  </div>
                </div>
              )}
              <Link to="/inventory" className="text-[12px] text-accent-blue hover:underline flex items-center gap-1 mt-4">
                View full inventory <ArrowRight size={12} />
              </Link>
            </div>

            <div className="card p-5">
              <h3 className="text-[14px] font-semibold text-app mb-4 flex items-center gap-2"><Store size={15} /> Marketplace Overview</h3>
              {marketplaceOverview.length === 0 ? (
                <p className="text-[12.5px] text-faint">No marketplaces connected yet.</p>
              ) : (
                <div className="space-y-3">
                  {marketplaceOverview.map(p => (
                    <div key={p.platform}>
                      <div className="flex items-center justify-between text-[12.5px] mb-1">
                        <span className="text-app font-medium flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: PLATFORM_DOT_COLOR[p.platform] ?? 'var(--text-faint)' }} />
                          {PLATFORM_LABELS[p.platform as keyof typeof PLATFORM_LABELS] ?? p.platform}
                        </span>
                        <span className="text-dim whitespace-nowrap">
                          {p.count > 0 ? `₹${p.revenue.toLocaleString('en-IN')} · ${p.count} order${p.count === 1 ? '' : 's'}` : 'No orders synced'}
                        </span>
                      </div>
                      <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                        <div className="h-full bg-accent-blue rounded-full" style={{ width: `${p.share}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card p-5">
              <h3 className="text-[14px] font-semibold text-app mb-4 flex items-center gap-2"><Lightbulb size={15} /> Quick Business Insights</h3>
              {insights.length === 0 ? (
                <p className="text-[12.5px] text-faint">Insights will appear here once order data starts syncing in.</p>
              ) : (
                <div className="space-y-3">
                  {insights.map((ins, i) => (
                    <div key={i} className="flex items-start gap-2.5 text-[12.5px] text-dim leading-relaxed">
                      <ins.icon size={14} className={`${ins.tone} flex-shrink-0 mt-0.5`} />
                      <span>{ins.text}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Sales Trend Chart / Orders Trend Chart — dependency-free SVG charts
          computed from real order_date + total_amount values, shared with
          Business Intelligence so both pages agree on the same numbers. */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <TrendChartCard title="Sales Trend" orders={orders} loading={loading} metric="revenue" />
        <TrendChartCard title="Orders Trend" orders={orders} loading={loading} metric="orders" />
      </div>

      {/* Recent Activity / Low Stock Products / Top Performing Products */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {loading ? (
          <>
            <SectionSkeleton title="Recent Activity" />
            <SectionSkeleton title="Low Stock Products" />
            <SectionSkeleton title="Top Performing Products" />
          </>
        ) : (
          <>
            <div className="card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-[14px] font-semibold text-app flex items-center gap-2"><Activity size={15} /> Recent Activity</h3>
                <Link to="/orders" className="text-[12px] text-accent-blue hover:underline flex items-center gap-1">View all <ArrowRight size={12} /></Link>
              </div>
              <div className="space-y-3">
                {recentOrders.length === 0 && (
                  <div className="text-[12.5px] text-faint">No orders yet{selected !== 'all' ? ` on ${PLATFORM_LABELS[selected]}` : ''}.</div>
                )}
                {recentOrders.map(o => {
                  const { Icon, color } = statusVisual(o.status)
                  return (
                    <div key={o.order_id} className="flex items-start gap-3">
                      <Icon size={14} className={`${color} flex-shrink-0 mt-0.5`} />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-start justify-between gap-2">
                          <div className="text-[12.5px] font-medium text-app truncate">{o.order_id}</div>
                          <span className="text-[12px] text-dim whitespace-nowrap">
                            {o.total_amount != null ? `₹${o.total_amount.toLocaleString('en-IN')}` : '—'}
                          </span>
                        </div>
                        <div className="text-[11.5px] text-faint mt-0.5 capitalize">
                          {o.status} · {PLATFORM_LABELS[o.platform as keyof typeof PLATFORM_LABELS] ?? o.platform}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-[14px] font-semibold text-app flex items-center gap-2"><Package size={15} /> Low Stock Products</h3>
                <Link to="/inventory" className="text-[12px] text-accent-blue hover:underline flex items-center gap-1">View all <ArrowRight size={12} /></Link>
              </div>
              <div className="space-y-3">
                {lowStockItems.length === 0 && outOfStockCount === 0 && (
                  <div className="text-[12.5px] text-faint">All SKUs are healthily stocked.</div>
                )}
                {lowStockItems.length === 0 && outOfStockCount > 0 && (
                  <div className="text-[12.5px] text-faint">No SKUs are low — but some are fully out of stock.</div>
                )}
                {lowStockItems.slice(0, 5).map(item => (
                  <div key={item.sku} className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="w-1.5 h-1.5 rounded-full bg-accent-amber flex-shrink-0" />
                      <span className="text-[12.5px] font-mono-app text-app truncate">{item.sku}</span>
                    </div>
                    <span className="text-[12px] text-accent-amber font-medium whitespace-nowrap">{item.available_quantity} left</span>
                  </div>
                ))}
                {outOfStockCount > 0 && (
                  <div className="flex items-center gap-2 pt-2 border-t border-app">
                    <RotateCcw size={12} className="text-accent-red" />
                    <span className="text-[12px] text-accent-red">{outOfStockCount} SKU{outOfStockCount === 1 ? '' : 's'} out of stock</span>
                  </div>
                )}
              </div>
            </div>

            <div className="card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-[14px] font-semibold text-app flex items-center gap-2"><Award size={15} /> Top Performing Products</h3>
                <Link to="/business-intelligence" className="text-[12px] text-accent-blue hover:underline flex items-center gap-1">Full report <ArrowRight size={12} /></Link>
              </div>
              {topProducts.length === 0 ? (
                <div className="text-[12.5px] text-faint">Top products will appear once your synced orders include line items.</div>
              ) : (
                <div className="space-y-2.5">
                  {topProducts.map(([sku, qty], i) => (
                    <div key={sku} className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-[11px] text-faint w-3.5 flex-shrink-0">{i + 1}</span>
                        <span className="text-[12.5px] font-mono-app text-app truncate">{sku}</span>
                      </div>
                      <span className="text-[12px] text-dim whitespace-nowrap">{qty} units</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

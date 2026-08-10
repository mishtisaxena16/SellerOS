import { useCallback, useEffect, useState } from 'react'
import { GraduationCap, TrendingUp, Search, DollarSign, Truck, Package, ShoppingBag, PlugZap, RefreshCw, AlertTriangle } from 'lucide-react'
import AgentConsole from '../components/AgentConsole'
import { useAuth } from '../context/AuthContext'
import { usePlatform } from '../context/PlatformContext'
import { getDashboardSummary, type DashboardSummary } from '../api/dashboard'
import { ApiError } from '../api/client'

// Seller Coach is a genuinely conversational surface backed by
// backend.ai.agent_layer.seller_coach.coach_agent via POST /chat.
// There's no backend model for lesson progress, badges, or a fixed
// "seller score" today, so this page doesn't invent one — it's a
// focused chat with the real coaching agent instead of a mock LMS.
//
// Starter prompts are the one thing that changes with userType — someone who
// said they're just starting out gets prompts about getting set up, someone
// already selling gets prompts about optimizing what they've got. Same agent,
// same backend call, just a different first question suggested.
const PROMPTS_NEW = [
  { label: "What should I sell first?", prompt: "I'm new to online selling — what should I think about before choosing what to sell?" },
  { label: 'Amazon vs Flipkart vs Meesho', prompt: 'How do Amazon, Flipkart and Meesho differ for a brand-new seller?' },
  { label: 'What does listing require?', prompt: "What do I need ready before I can list a product for the first time?" },
  { label: 'Common beginner mistakes', prompt: 'What mistakes do new marketplace sellers commonly make early on?' },
]
const PROMPTS_EXISTING = [
  { label: 'How do I improve my listings?', prompt: 'How do I improve my listings?' },
  { label: 'Tips to grow sales', prompt: 'Give me tips to grow my sales this month.' },
  { label: 'Improve search ranking', prompt: 'How can I improve my search ranking?' },
  { label: 'Pricing advice', prompt: 'Give me pricing advice for my products.' },
]

export default function SellerCoach() {
  const { userType } = useAuth()
  const { connectedPlatforms } = usePlatform()
  const hasMarketplace = connectedPlatforms.length > 0
  const quickPrompts = userType === 'new' ? PROMPTS_NEW : PROMPTS_EXISTING

  // Real numbers, from the same /dashboard/summary endpoint Dashboard
  // uses — shown here so it's visible (not just internal) that the
  // coach's answers are grounded in this seller's actual business via
  // ContextBuilder's "business" section, not a generic script.
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  const loadSummary = useCallback(() => {
    if (!hasMarketplace) { setSummary(null); setSummaryError(null); return () => {} }
    let cancelled = false
    setSummaryLoading(true)
    setSummaryError(null)
    getDashboardSummary()
      .then(s => { if (!cancelled) setSummary(s) })
      .catch(err => {
        if (cancelled) return
        // Previously swallowed silently, leaving the coach's numbers
        // permanently blank with no way to tell if they'd ever load.
        setSummaryError(err instanceof ApiError ? err.message : 'Could not load your business numbers.')
      })
      .finally(() => { if (!cancelled) setSummaryLoading(false) })
    return () => { cancelled = true }
  }, [hasMarketplace])

  useEffect(() => {
    const cancel = loadSummary()
    return cancel
  }, [loadSummary])

  return (
    <div className="p-6 fade-in space-y-6">
      <div>
        <h2 className="text-xl font-bold text-app flex items-center gap-2">
          <GraduationCap size={22} className="text-accent-blue" />
          Seller Coach
        </h2>
        <p className="text-[13px] text-dim mt-0.5">Ask for advice on growing your marketplace business — powered by your live AI coach.</p>
      </div>

      {hasMarketplace ? (
        summaryLoading ? (
          <div className="flex items-center gap-3 text-[12px] text-faint animate-pulse">
            <span className="h-5 w-32 rounded-md bg-hover inline-block" />
            <span className="h-5 w-32 rounded-md bg-hover inline-block" />
          </div>
        ) : summaryError ? (
          <div className="flex flex-wrap items-center gap-2 text-[12px] text-accent-red">
            <AlertTriangle size={13} className="flex-shrink-0" />
            <span>{summaryError}</span>
            <button onClick={loadSummary} className="inline-flex items-center gap-1 text-accent-blue hover:underline">
              <RefreshCw size={11} /> Retry
            </button>
          </div>
        ) : summary && summary.inventory_items != null ? (
          <div className="flex flex-wrap items-center gap-3 text-[12px]">
            <span className="badge bg-accent-blue-soft text-accent-blue border-0"><Package size={11} /> {summary.inventory_items} inventory items</span>
            <span className="badge bg-accent-amber-soft text-accent-amber border-0"><ShoppingBag size={11} /> {summary.pending_orders ?? 0} pending orders</span>
            <span className="text-faint">Your coach sees these numbers too — try asking about them directly.</span>
          </div>
        ) : null
      ) : (
        <div className="flex items-center gap-2 text-[12px] text-faint">
          <PlugZap size={13} /> Connect a marketplace so your coach can answer using your real numbers, not just general advice.
        </div>
      )}

      <AgentConsole
        title="Seller Coach"
        description="Advice on listings, pricing, fulfillment, reviews, and growth"
        icon={GraduationCap}
        iconColor="bg-accent-blue-soft text-accent-blue"
        sessionKey="seller-coach"
        placeholder="Ask your seller coach anything…"
        emptyHint="Try asking about your account health, how to improve conversion, or what to focus on this month."
        quickPrompts={quickPrompts}
      />

      <div>
        <div className="text-[13px] font-semibold text-app mb-3">Common topics</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Listings', icon: Search, color: 'bg-accent-blue-soft text-accent-blue', hint: 'Titles, images, keywords', tip: 'Improve listing quality' },
            { label: 'Pricing', icon: DollarSign, color: 'bg-accent-green-soft text-accent-green', hint: 'Margins, discounts, Buy Box', tip: 'Improve pricing' },
            { label: 'Fulfillment', icon: Truck, color: 'bg-accent-purple-soft text-accent-purple', hint: 'Shipping, SLAs, returns', tip: 'Reduce stock-outs' },
            { label: 'Growth', icon: TrendingUp, color: 'bg-accent-amber-soft text-accent-amber', hint: 'Trends, demand, scaling', tip: 'Increase conversion' },
          ].map(t => (
            <div key={t.label} className="card p-4 flex items-center gap-3">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${t.color}`}>
                <t.icon size={16} />
              </div>
              <div>
                <div className="text-[13px] font-semibold text-app">{t.label}</div>
                <div className="text-[11.5px] text-faint">{t.hint}</div>
                <div className="text-[10.5px] text-accent-green mt-0.5">Tip: {t.tip}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

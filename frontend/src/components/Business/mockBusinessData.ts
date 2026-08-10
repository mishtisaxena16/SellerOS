// ============================================================================
// SellerOS — Phase 5: Business Intelligence mock data layer
// ============================================================================
// Everything in this file is DEMO / MOCK data only. No network calls, no
// marketplace APIs. It exists purely so the AI-driven BI dashboard has
// realistic numbers to render today.
//
// Structure is intentionally shaped like a future API response
// (id / value / trend / insight) so a real backend endpoint can replace
// `getMockBusinessSnapshot()` later without touching any component that
// consumes it — just swap the fetch, keep the same shape.
// ============================================================================

export type TrendDirection = 'up' | 'down' | 'flat'
export type ActionPriority = 'Low' | 'Medium' | 'High' | 'Critical'

export interface AIInsight {
  title: string
  metricLabel: string
  metricValue: string
  trend: TrendDirection
  changePercent: number
  analysis: string[]
  impact: string
  recommendations: string[]
  confidence: number // 0-100
  sources: string[]
  priority: ActionPriority
}

export interface MetricCardData {
  id: string
  label: string
  value: string
  trend: TrendDirection
  changePercent: number
  icon: 'revenue' | 'orders' | 'profit' | 'inventory' | 'returns' | 'conversion' | 'adspend' | 'ctr' | 'roas'
  color: 'blue' | 'green' | 'purple' | 'amber' | 'red' | 'pink'
  insight: AIInsight
}

export interface BusinessWarning {
  id: string
  severity: 'warning' | 'critical'
  message: string
  insight: AIInsight
}

export interface Recommendation {
  id: string
  title: string
  priority: ActionPriority
  expectedImpact: string
  estimatedImprovement: string
  confidence: number
}

export interface HealthBreakdownItem {
  label: string
  score: number // 0-100
  weight: number // fraction of overall score, sums to 1
}

export interface BusinessHealth {
  score: number
  label: string
  breakdown: HealthBreakdownItem[]
}

export interface BusinessSummary {
  headline: string[]
  highestOpportunity: string
}

export interface QuickAction {
  id: string
  label: string
  description: string
  route: string
}

export interface DemoDataPoint {
  label: string
  value: number
}

export interface BusinessSnapshot {
  summary: BusinessSummary
  health: BusinessHealth
  metrics: MetricCardData[]
  warnings: BusinessWarning[]
  recommendations: Recommendation[]
  quickActions: QuickAction[]
  topCategories: DemoDataPoint[]
  topProducts: DemoDataPoint[]
  revenueTrend: DemoDataPoint[]
  campaigns: { name: string; spend: number; roas: number; ctr: number }[]
}

// ----------------------------------------------------------------------------
// Demo snapshot — static but shaped like a real response payload.
// ----------------------------------------------------------------------------

export function getMockBusinessSnapshot(): BusinessSnapshot {
  return {
    summary: {
      headline: [
        "Revenue ↑12%",
        "Orders ↑8%",
        "Returns ↓4%",
        "Inventory healthy",
        "Ads performing above target",
      ],
      highestOpportunity: 'Electronics category',
    },

    health: {
      score: 89,
      label: 'Excellent',
      breakdown: [
        { label: 'Sales', score: 92, weight: 0.25 },
        { label: 'Inventory', score: 84, weight: 0.2 },
        { label: 'Marketing', score: 88, weight: 0.2 },
        { label: 'Customer Satisfaction', score: 90, weight: 0.15 },
        { label: 'Operations', score: 87, weight: 0.1 },
        { label: 'Returns', score: 91, weight: 0.1 },
      ],
    },

    metrics: [
      {
        id: 'revenue',
        label: 'Revenue',
        value: '₹12.4L',
        trend: 'up',
        changePercent: 12,
        icon: 'revenue',
        color: 'blue',
        insight: {
          title: 'Revenue',
          metricLabel: 'Revenue',
          metricValue: '₹12.4L',
          trend: 'up',
          changePercent: 12,
          analysis: [
            'Electronics grew 18%',
            'Repeat customers +9%',
            'Weekend sales spike',
          ],
          impact: 'Revenue growth is outpacing last month across your two strongest categories, driven mainly by repeat buyers rather than new acquisition.',
          recommendations: [
            'Increase stock of top-selling SKUs before next weekend',
            'Extend the Electronics promotion by one more week',
          ],
          confidence: 94,
          sources: ['Order history', 'Category performance', 'Customer repeat-purchase rate'],
          priority: 'High',
        },
      },
      {
        id: 'orders',
        label: 'Orders',
        value: '3,842',
        trend: 'up',
        changePercent: 8,
        icon: 'orders',
        color: 'green',
        insight: {
          title: 'Orders',
          metricLabel: 'Orders',
          metricValue: '3,842',
          trend: 'up',
          changePercent: 8,
          analysis: [
            'Weekend order volume up 22%',
            'Mobile checkout share rising',
            'Fewer abandoned carts than last month',
          ],
          impact: 'Order volume growth is healthy and broad-based, not concentrated in a single channel.',
          recommendations: [
            'Prepare fulfillment capacity for continued weekend spikes',
            'Keep mobile checkout as the default experience',
          ],
          confidence: 91,
          sources: ['Order history', 'Checkout funnel'],
          priority: 'Medium',
        },
      },
      {
        id: 'profit',
        label: 'Profit',
        value: '₹3.1L',
        trend: 'up',
        changePercent: 6,
        icon: 'profit',
        color: 'purple',
        insight: {
          title: 'Profit',
          metricLabel: 'Profit',
          metricValue: '₹3.1L',
          trend: 'up',
          changePercent: 6,
          analysis: [
            'Margins held steady despite promotions',
            'Lower return rate protected net profit',
            'Ad spend efficiency improved',
          ],
          impact: 'Profit is growing slower than revenue, mainly because of promotional discounting — still a healthy net position.',
          recommendations: [
            'Review discount depth on lower-margin SKUs',
            'Shift ad budget toward the highest-ROAS campaign',
          ],
          confidence: 88,
          sources: ['P&L summary', 'Campaign performance'],
          priority: 'Medium',
        },
      },
      {
        id: 'inventory',
        label: 'Inventory',
        value: '143 units',
        trend: 'down',
        changePercent: -9,
        icon: 'inventory',
        color: 'amber',
        insight: {
          title: 'Inventory',
          metricLabel: 'Current stock',
          metricValue: '143 units',
          trend: 'down',
          changePercent: -9,
          analysis: [
            'Stock decreased due to weekend sales',
            'Top 3 SKUs account for most of the drawdown',
            'No incoming purchase order scheduled yet',
          ],
          impact: 'At the current sell-through rate, expected stockout in 6 days for your fastest-moving SKU.',
          recommendations: [
            'Recommended reorder: 250 units',
            'Prioritize restock for the top 3 SKUs first',
          ],
          confidence: 90,
          sources: ['Inventory ledger', 'Sales velocity'],
          priority: 'Critical',
        },
      },
      {
        id: 'returns',
        label: 'Returns',
        value: '4.2%',
        trend: 'down',
        changePercent: -4,
        icon: 'returns',
        color: 'green',
        insight: {
          title: 'Returns',
          metricLabel: 'Return rate',
          metricValue: '4.2%',
          trend: 'down',
          changePercent: -4,
          analysis: [
            'Sizing-related returns dropped after updated size chart',
            'Fewer damaged-in-transit claims',
            'Apparel still the highest-return category',
          ],
          impact: 'Return rate is improving and now sits below the category benchmark.',
          recommendations: [
            'Roll the updated size chart out to remaining apparel listings',
            'Monitor packaging for the SKUs with prior damage claims',
          ],
          confidence: 86,
          sources: ['Returns log', 'Customer feedback'],
          priority: 'Low',
        },
      },
      {
        id: 'conversion',
        label: 'Conversion Rate',
        value: '3.6%',
        trend: 'up',
        changePercent: 5,
        icon: 'conversion',
        color: 'blue',
        insight: {
          title: 'Conversion Rate',
          metricLabel: 'Conversion rate',
          metricValue: '3.6%',
          trend: 'up',
          changePercent: 5,
          analysis: [
            'Improved product images lifted add-to-cart rate',
            'Faster page load on mobile',
            'Better-reviewed listings convert 1.4x higher',
          ],
          impact: 'Conversion improvements are concentrated in listings updated in the last two weeks.',
          recommendations: [
            'Apply the same image treatment to remaining listings',
            'Prioritize review-collection for low-review, high-traffic SKUs',
          ],
          confidence: 89,
          sources: ['Listing analytics', 'Funnel data'],
          priority: 'Medium',
        },
      },
      {
        id: 'adspend',
        label: 'Ad Spend',
        value: '₹68,200',
        trend: 'flat',
        changePercent: 1,
        icon: 'adspend',
        color: 'pink',
        insight: {
          title: 'Ad Spend',
          metricLabel: 'Ad spend',
          metricValue: '₹68,200',
          trend: 'flat',
          changePercent: 1,
          analysis: [
            'Spend held roughly flat month over month',
            'One campaign under-delivering on ROAS',
            'Two campaigns above target ROAS',
          ],
          impact: 'Overall spend is efficient, but budget is not yet weighted toward your best-performing campaign.',
          recommendations: [
            'Reduce CPC for Campaign X',
            'Reallocate 15% of budget to the top-ROAS campaign',
          ],
          confidence: 85,
          sources: ['Campaign performance', 'Ad platform reporting'],
          priority: 'Medium',
        },
      },
      {
        id: 'ctr',
        label: 'CTR',
        value: '2.9%',
        trend: 'up',
        changePercent: 7,
        icon: 'ctr',
        color: 'purple',
        insight: {
          title: 'CTR',
          metricLabel: 'Click-through rate',
          metricValue: '2.9%',
          trend: 'up',
          changePercent: 7,
          analysis: [
            'New thumbnail creative outperforming old set',
            'Electronics ads driving most of the lift',
            'Mobile CTR now ahead of desktop',
          ],
          impact: 'Creative refresh is the main driver — this has not yet been rolled out to all campaigns.',
          recommendations: [
            'Extend the new creative to remaining active campaigns',
          ],
          confidence: 87,
          sources: ['Campaign performance'],
          priority: 'Low',
        },
      },
      {
        id: 'roas',
        label: 'ROAS',
        value: '4.1x',
        trend: 'up',
        changePercent: 10,
        icon: 'roas',
        color: 'green',
        insight: {
          title: 'ROAS',
          metricLabel: 'Return on ad spend',
          metricValue: '4.1x',
          trend: 'up',
          changePercent: 10,
          analysis: [
            'Best campaign returning 6.2x',
            'Weakest campaign returning 1.8x',
            'Overall blended ROAS above target of 3.5x',
          ],
          impact: 'Blended ROAS is strong, but pulled down by one underperforming campaign.',
          recommendations: [
            'Pause or restructure the 1.8x campaign',
            'Increase budget on the 6.2x campaign gradually',
          ],
          confidence: 90,
          sources: ['Campaign performance', 'Ad platform reporting'],
          priority: 'High',
        },
      },
    ],

    warnings: [
      {
        id: 'inv-low',
        severity: 'critical',
        message: 'Inventory running low',
        insight: {
          title: 'Inventory running low',
          metricLabel: 'Current stock',
          metricValue: '143 units',
          trend: 'down',
          changePercent: -9,
          analysis: [
            'Weekend demand pulled stock down faster than forecast',
            'No purchase order currently scheduled',
          ],
          impact: 'Expected stockout in 6 days at the current sell-through rate.',
          recommendations: ['Recommended reorder: 250 units', 'Expedite the top 3 SKUs first'],
          confidence: 90,
          sources: ['Inventory ledger', 'Sales velocity'],
          priority: 'Critical',
        },
      },
      {
        id: 'listing-quality',
        severity: 'warning',
        message: 'Listing quality dropping',
        insight: {
          title: 'Listing quality dropping',
          metricLabel: 'Avg. listing score',
          metricValue: '78/100',
          trend: 'down',
          changePercent: -5,
          analysis: [
            '6 listings missing updated images',
            'Average review count per SKU has plateaued',
          ],
          impact: 'Listings with lower quality scores are converting noticeably worse than the account average.',
          recommendations: ['Improve product images on the 6 flagged listings', 'Run a review-request campaign on top SKUs'],
          confidence: 82,
          sources: ['Listing analytics'],
          priority: 'Medium',
        },
      },
      {
        id: 'ad-inefficient',
        severity: 'warning',
        message: 'Ad spend inefficient',
        insight: {
          title: 'Ad spend inefficient',
          metricLabel: 'Campaign ROAS',
          metricValue: '1.8x',
          trend: 'down',
          changePercent: -3,
          analysis: [
            'Campaign X CPC has risen without a matching conversion lift',
            'Budget share for this campaign is disproportionate to its return',
          ],
          impact: 'This campaign is dragging down blended ROAS by roughly 0.4x.',
          recommendations: ['Reduce CPC for Campaign X', 'Reallocate budget to higher-ROAS campaigns'],
          confidence: 85,
          sources: ['Campaign performance'],
          priority: 'High',
        },
      },
    ],

    recommendations: [
      {
        id: 'rec-restock-a',
        title: 'Restock Product A',
        priority: 'Critical',
        expectedImpact: 'Avoid stockout',
        estimatedImprovement: '+₹1.2L revenue protected',
        confidence: 92,
      },
      {
        id: 'rec-optimize-b',
        title: 'Optimize Product B title',
        priority: 'High',
        expectedImpact: 'Higher search visibility',
        estimatedImprovement: '+6% conversion rate',
        confidence: 84,
      },
      {
        id: 'rec-cpc-x',
        title: 'Reduce CPC for Campaign X',
        priority: 'High',
        expectedImpact: 'Improved ad efficiency',
        estimatedImprovement: '+0.4x ROAS',
        confidence: 85,
      },
      {
        id: 'rec-images',
        title: 'Improve Product Images',
        priority: 'Medium',
        expectedImpact: 'Better conversion on flagged listings',
        estimatedImprovement: '+4% conversion rate',
        confidence: 82,
      },
      {
        id: 'rec-weekend-stock',
        title: 'Increase inventory before weekend',
        priority: 'Medium',
        expectedImpact: 'Capture weekend demand spike',
        estimatedImprovement: '+8% weekend revenue',
        confidence: 88,
      },
    ],

    quickActions: [
      { id: 'analyze-listings', label: 'Analyze Listings', description: 'Review listing quality and SEO', route: '/product-studio' },
      { id: 'optimize-pricing', label: 'Optimize Pricing', description: 'AI pricing recommendations', route: '/product-studio' },
      { id: 'review-inventory', label: 'Review Inventory', description: 'Check stock levels and reorder points', route: '/inventory' },
      { id: 'forecast-demand', label: 'Forecast Demand', description: 'Predict upcoming demand by SKU', route: '/seller-coach' },
      { id: 'generate-report', label: 'Generate Report', description: 'Export a business performance report', route: '/business-intelligence' },
    ],

    topCategories: [
      { label: 'Electronics', value: 412000 },
      { label: 'Home & Kitchen', value: 268000 },
      { label: 'Apparel', value: 191000 },
      { label: 'Beauty', value: 104000 },
      { label: 'Sports', value: 65000 },
    ],

    topProducts: [
      { label: 'Wireless Earbuds Pro', value: 812 },
      { label: 'Smart LED Strip 5m', value: 640 },
      { label: 'Cotton Bedsheet Set', value: 521 },
      { label: 'Stainless Steel Bottle', value: 478 },
      { label: 'Yoga Mat Premium', value: 390 },
    ],

    revenueTrend: [
      { label: 'Mon', value: 148000 },
      { label: 'Tue', value: 152000 },
      { label: 'Wed', value: 149000 },
      { label: 'Thu', value: 161000 },
      { label: 'Fri', value: 178000 },
      { label: 'Sat', value: 214000 },
      { label: 'Sun', value: 238000 },
    ],

    campaigns: [
      { name: 'Electronics Boost', spend: 24500, roas: 6.2, ctr: 3.4 },
      { name: 'Home & Kitchen Reach', spend: 18300, roas: 4.0, ctr: 2.6 },
      { name: 'Campaign X', spend: 15200, roas: 1.8, ctr: 1.9 },
      { name: 'Brand Defense', spend: 10200, roas: 5.1, ctr: 3.1 },
    ],
  }
}

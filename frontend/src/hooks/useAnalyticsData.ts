import { useEffect, useState } from 'react'
import { getAnalytics, type AnalyticsResponse } from '../api/analytics'
import { ApiError } from '../api/client'
import type { Platform } from '../api/marketplace'
import { getMockBusinessIntelligence, type BusinessIntelligenceView } from '../mock/businessIntelligenceView'

export type { BusinessIntelligenceView }

// ============================================================================
// Phase 7.5B — unified Analytics data source
// ============================================================================
// Every analytics-related screen should see one metrics shape
// (BusinessIntelligenceView) regardless of whether the data came from the
// live backend (GET /analytics) or the Phase 7.1 mock dataset. This hook
// mirrors useOrdersData.ts / useInventoryData.ts exactly:
//   1. Always calls the existing, unmodified `getAnalytics` API first.
//   2. Normalizes a response that actually has at least one of
//      sales_metrics / business_metrics into BusinessIntelligenceView.
//   3. Falls back to the existing mock dataset (frontend/src/mock/analytics.ts,
//      via businessIntelligenceView.ts) when the backend has neither metric
//      for this platform, or can't be reached at all — matching the exact
//      "dashboard pages fall back to their own mock data" pattern already
//      used by useOrdersData.ts / useInventoryData.ts.
// No backend, connector, RAG, Playwright, routing, or auth code is touched
// by this hook — it only reads from the existing api/analytics.ts client
// and the existing mock dataset.
// ============================================================================

type PlatformFilter = 'all' | Platform

function normalizeLive(res: AnalyticsResponse): BusinessIntelligenceView {
  return {
    salesMetrics: res.sales_metrics ? {
      totalOrders: res.sales_metrics.total_orders,
      totalRevenue: res.sales_metrics.total_revenue,
      averageOrderValue: res.sales_metrics.average_order_value,
      currency: res.sales_metrics.currency,
      timeframe: res.sales_metrics.timeframe,
    } : null,
    salesMetricsMessage: res.sales_metrics_message,
    businessMetrics: res.business_metrics ? {
      shippedOrders: res.business_metrics.shipped_orders,
      pendingOrders: res.business_metrics.pending_orders,
      currency: res.business_metrics.currency,
    } : null,
    businessMetricsMessage: res.business_metrics_message,
  }
}

const EMPTY_VIEW: BusinessIntelligenceView = {
  salesMetrics: null,
  salesMetricsMessage: null,
  businessMetrics: null,
  businessMetricsMessage: null,
}

export interface UseAnalyticsDataResult {
  data: BusinessIntelligenceView
  loading: boolean
  error: { status: number; message: string } | null
  // True when `data` is the Phase 7.1 mock dataset rather than a live
  // backend response (no marketplace connected, neither metric came back
  // for this platform, or the backend couldn't be reached).
  usingMockData: boolean
}

export function useAnalyticsData(selected: PlatformFilter): UseAnalyticsDataResult {
  const [data, setData] = useState<BusinessIntelligenceView>(EMPTY_VIEW)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<{ status: number; message: string } | null>(null)
  const [usingMockData, setUsingMockData] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    getAnalytics(selected)
      .then(res => {
        if (cancelled) return
        if (res.sales_metrics || res.business_metrics) {
          setData(normalizeLive(res))
          setUsingMockData(false)
        } else {
          // Neither metric came back for this platform (no marketplace
          // connected, or a connected marketplace with nothing to report
          // yet) — fall back to the mock dataset so the dashboard still
          // shows realistic analytics.
          setData(getMockBusinessIntelligence(selected))
          setUsingMockData(true)
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const apiErr = err instanceof ApiError ? err : null
        setData(getMockBusinessIntelligence(selected))
        setUsingMockData(true)
        setError({ status: apiErr?.status ?? 0, message: apiErr?.message ?? 'Could not reach the SellerOS API.' })
      })
      .finally(() => !cancelled && setLoading(false))

    return () => { cancelled = true }
  }, [selected])

  return { data, loading, error, usingMockData }
}

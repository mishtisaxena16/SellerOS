import { apiRequest } from './client'
import type { Platform } from './marketplace'

// Backend today only wires sales/business metrics for Amazon
// (SALES_METRICS_FETCHERS / BUSINESS_METRICS_FETCHERS in
// marketplace_connector.py). For Flipkart/Meesho, *_message will be
// populated instead of the data — surface that honestly rather than
// pretending the numbers exist.
export interface SalesMetrics {
  platform: string
  timeframe: string
  total_orders: number
  total_revenue: number
  average_order_value: number
  currency: string
  note?: string
}

export interface BusinessMetrics {
  platform: string
  timeframe: string
  shipped_orders: number
  pending_orders: number
  currency: string
  note?: string
}

export interface AnalyticsResponse {
  platform: string
  sales_metrics: SalesMetrics | null
  sales_metrics_message: string | null
  business_metrics: BusinessMetrics | null
  business_metrics_message: string | null
}

export function getAnalytics(platform?: Platform | 'all') {
  const query = platform && platform !== 'all' ? `?platform=${platform}` : ''
  return apiRequest<AnalyticsResponse>(`/analytics${query}`)
}

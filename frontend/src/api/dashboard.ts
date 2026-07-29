import { apiRequest } from './client'

// Mirrors what backend.service.marketplace_data_service.get_dashboard_summary
// actually returns (NOT backend.schema.dashboard.DashboardSummaryResponse,
// which is unused/stale — the router has no response_model, so the real
// shape is whatever this function returns). There is no active_listings
// field on the backend today.
export interface DashboardSummary {
  connected_marketplaces: number
  platform?: string
  inventory_items: number | null
  pending_orders: number | null
  message?: string
}

export function getDashboardSummary() {
  return apiRequest<DashboardSummary>('/dashboard/summary')
}

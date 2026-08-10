// ============================================================================
// SellerOS — Phase 7.5B: Mock Business Intelligence View-Model Adapter
// ============================================================================
// Pure, read-only adapter layer. It does NOT invent or generate any new
// figures — it only *reshapes* metrics already computed in ./analytics.ts
// (itself derived from ./orders.ts, ./products.ts, and ./inventory.ts, per
// Phase 7.1) into the sales/business metrics shape every analytics-related
// screen needs, mirroring the live backend's /analytics response
// (SalesMetrics / BusinessMetrics in api/analytics.ts) field-for-field.
//
// Same role ordersView.ts and inventoryView.ts already play for Orders and
// Inventory. Nothing here touches the backend, connectors, Playwright,
// routing, or auth. This file has zero network/API calls — it's a
// synchronous, in-memory transform.
// ============================================================================

import type { Platform } from '../api/marketplace'
import { orders } from './orders'
import { seller } from './seller'
import { revenueSummary } from './analytics'

export interface SalesMetricsView {
  totalOrders: number
  totalRevenue: number
  averageOrderValue: number
  currency: string
  timeframe: string
}

export interface BusinessMetricsView {
  shippedOrders: number
  pendingOrders: number
  currency: string
}

export interface BusinessIntelligenceView {
  salesMetrics: SalesMetricsView | null
  salesMetricsMessage: string | null
  businessMetrics: BusinessMetricsView | null
  businessMetricsMessage: string | null
}

// Shipped/Pending are read straight off the same Order.status values
// ordersView.ts already maps to ShippingStatus — not a separately
// hand-typed count, so it can't drift out of sync with the Orders screen.
const shippedOrders = orders.filter(o => o.status === 'Shipped' || o.status === 'Delivered').length
const pendingOrders = orders.filter(o => o.status === 'Processing').length

const mockBusinessIntelligenceView: BusinessIntelligenceView = {
  salesMetrics: {
    totalOrders: revenueSummary.completedOrders,
    totalRevenue: revenueSummary.netRevenue,
    averageOrderValue: revenueSummary.averageOrderValue,
    currency: 'INR',
    timeframe: 'All mock order history',
  },
  salesMetricsMessage: null,
  businessMetrics: {
    shippedOrders,
    pendingOrders,
    currency: 'INR',
  },
  businessMetricsMessage: null,
}

const NO_MOCK_DATA_MESSAGE = 'Mock analytics are only available for Amazon in this demo dataset.'

// The Phase 7.1 mock dataset represents a single Amazon seller — same rule
// ordersView.ts / inventoryView.ts already apply to mockOrderRows /
// mockInventoryRows: it stands in for the 'all' or 'amazon' platform filter
// only, rather than pretending to have Flipkart/Meesho analytics that were
// never generated.
const emptyBusinessIntelligenceView: BusinessIntelligenceView = {
  salesMetrics: null,
  salesMetricsMessage: NO_MOCK_DATA_MESSAGE,
  businessMetrics: null,
  businessMetricsMessage: NO_MOCK_DATA_MESSAGE,
}

export function getMockBusinessIntelligence(selected: 'all' | Platform): BusinessIntelligenceView {
  return selected === 'all' || selected === seller.platform
    ? mockBusinessIntelligenceView
    : emptyBusinessIntelligenceView
}

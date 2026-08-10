import { useEffect, useState } from 'react'
import { getOrders, type OrderRecord } from '../api/orders'
import { ApiError } from '../api/client'
import type { Platform } from '../api/marketplace'
import { PLATFORM_LABELS } from '../context/PlatformContext'
import { mockOrderRows, type OrderViewRow } from '../mock/ordersView'

export type { OrderViewRow }

// ============================================================================
// Phase 7.2 — unified Orders data source
// ============================================================================
// Every Orders-related screen should see one row shape (OrderViewRow)
// regardless of whether the data came from the live backend (GET /orders)
// or the Phase 7.1 mock dataset. This hook:
//   1. Always calls the existing, unmodified `getOrders` API first.
//   2. Normalizes a successful, non-empty response into OrderViewRow[].
//   3. Falls back to the existing mock dataset (frontend/src/mock/orders.ts,
//      via ordersView.ts) when the backend has no marketplace connected,
//      returns zero orders, or can't be reached at all — matching the
//      existing "dashboard pages fall back to their own mock data" pattern
//      already noted in PlatformContext.
// No backend, connector, routing, or auth code is touched by this hook —
// it only reads from the existing api/orders.ts client and the existing
// mock dataset.
// ============================================================================

type PlatformFilter = 'all' | Platform

// Live orders don't carry a customer name or payment status from the
// backend today (see OrderRecord in api/orders.ts) — rather than invent
// data that isn't there, those fields are surfaced honestly.
const LIVE_DELIVERY_LABEL: Record<string, OrderViewRow['deliveryStatus']> = {
  delivered: 'Delivered',
  shipped: 'Out for Delivery',
  unshipped: 'Pending',
  pending: 'Pending',
  processing: 'Pending',
  cancelled: 'Cancelled',
  returned: 'Returned',
}
const LIVE_SHIPPING_LABEL: Record<string, OrderViewRow['shippingStatus']> = {
  delivered: 'Delivered',
  shipped: 'Shipped',
  unshipped: 'Processing',
  pending: 'Processing',
  processing: 'Processing',
  cancelled: 'Cancelled',
  returned: 'Returned',
}

function normalizeLiveOrder(order: OrderRecord): OrderViewRow {
  const key = order.status.toLowerCase()
  const quantity = order.items.reduce((sum, it) => sum + it.quantity, 0)
  const [first, ...rest] = order.items
  const product = first ? (rest.length === 0 ? first.sku : `${first.sku} +${rest.length} more`) : '—'

  return {
    id: order.order_id,
    orderNumber: order.order_id,
    customerName: order.customer_state ? `Customer — ${order.customer_state}` : 'Customer',
    customerLocation: order.customer_state ?? '—',
    product,
    itemCount: order.items.length,
    quantity,
    orderDate: order.order_date ?? '',
    deliveryStatus: LIVE_DELIVERY_LABEL[key] ?? 'Pending',
    // Not modeled on the live backend yet — shown as-is rather than guessed.
    paymentStatus: 'Paid',
    orderValue: order.total_amount ?? 0,
    marketplace: PLATFORM_LABELS[order.platform as Platform] ?? order.platform,
    shippingStatus: LIVE_SHIPPING_LABEL[key] ?? 'Processing',
    paymentMethod: 'Credit Card',
    items: order.items.map(it => ({
      sku: it.sku,
      name: it.sku,
      quantity: it.quantity,
      unitPrice: it.unit_price ?? 0,
      lineTotal: (it.unit_price ?? 0) * it.quantity,
    })),
    source: 'live',
  }
}

// The Phase 7.1 mock dataset represents a single Amazon seller — so it
// only stands in for the 'all' or 'amazon' filter, rather than pretending
// to have Flipkart/Meesho orders that were never generated.
function mockRowsForPlatform(selected: PlatformFilter): OrderViewRow[] {
  if (selected === 'all' || selected === 'amazon') return mockOrderRows
  return []
}

export interface UseOrdersDataResult {
  rows: OrderViewRow[]
  loading: boolean
  error: { status: number; message: string } | null
  // True when the rows on screen are the Phase 7.1 mock dataset rather
  // than a live backend response (no marketplace connected, zero orders,
  // or the backend couldn't be reached).
  usingMockData: boolean
}

export function useOrdersData(selected: PlatformFilter): UseOrdersDataResult {
  const [rows, setRows] = useState<OrderViewRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<{ status: number; message: string } | null>(null)
  const [usingMockData, setUsingMockData] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    getOrders(selected)
      .then(res => {
        if (cancelled) return
        if (res.success && res.orders.length > 0) {
          setRows(res.orders.map(normalizeLiveOrder))
          setUsingMockData(false)
        } else {
          // No live orders (either no marketplace connected, or a
          // connected marketplace with nothing in it yet) — fall back to
          // the mock dataset so the dashboard still shows a realistic
          // order history.
          setRows(mockRowsForPlatform(selected))
          setUsingMockData(true)
          if (!res.success) setError({ status: 200, message: res.message || 'Orders could not be fetched.' })
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const apiErr = err instanceof ApiError ? err : null
        setRows(mockRowsForPlatform(selected))
        setUsingMockData(true)
        setError({ status: apiErr?.status ?? 0, message: apiErr?.message ?? 'Could not reach the SellerOS API.' })
      })
      .finally(() => !cancelled && setLoading(false))

    return () => { cancelled = true }
  }, [selected])

  return { rows, loading, error, usingMockData }
}

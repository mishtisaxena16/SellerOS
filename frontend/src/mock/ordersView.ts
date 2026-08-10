// ============================================================================
// SellerOS — Phase 7.2: Mock Orders View-Model Adapter
// ============================================================================
// Pure, read-only adapter layer. It does NOT invent or generate any order
// data — it only *reshapes* the existing `orders` array from ./orders.ts
// (itself already tied to ./products.ts and ./seller.ts, per Phase 7.1) into
// the flat row shape every Orders-related screen needs:
//   Order ID · Customer Name · Product · Quantity · Order Date ·
//   Delivery Status · Payment Status · Order Value · Marketplace ·
//   Shipping Status
//
// Nothing here touches the backend, connectors, Playwright, routing, or
// auth. This file has zero imports outside ./orders and ./seller, and zero
// network/API calls — it's a synchronous, in-memory transform.
// ============================================================================

import { orders, type Order, type OrderStatus } from './orders'
import { seller } from './seller'

// ----------------------------------------------------------------------------
// Status derivation
// ----------------------------------------------------------------------------
// `Order.status` (from Phase 7.1) is the single source of truth for an
// order's lifecycle state. Delivery/Shipping/Payment status are three
// different *views* onto that one field — never separately hand-typed,
// so they can never drift out of sync with each other or with the
// summary badge already used on the Orders page.

export type DeliveryStatus = 'Delivered' | 'Out for Delivery' | 'Pending' | 'Cancelled' | 'Returned'
export type ShippingStatus = 'Delivered' | 'Shipped' | 'Processing' | 'Cancelled' | 'Returned'
export type PaymentStatus = 'Paid' | 'Refunded'

const DELIVERY_STATUS_BY_ORDER_STATUS: Record<OrderStatus, DeliveryStatus> = {
  Delivered: 'Delivered',
  Shipped: 'Out for Delivery',
  Processing: 'Pending',
  Cancelled: 'Cancelled',
  Returned: 'Returned',
}

// Shipping status mirrors the raw order status directly (it already is a
// fulfillment/shipping-centric label from Phase 7.1) — kept as its own
// named mapping so callers never reach into `order.status` directly and
// so a future change in wording only has to happen in one place.
const SHIPPING_STATUS_BY_ORDER_STATUS: Record<OrderStatus, ShippingStatus> = {
  Delivered: 'Delivered',
  Shipped: 'Shipped',
  Processing: 'Processing',
  Cancelled: 'Cancelled',
  Returned: 'Returned',
}

// No separate payment ledger exists in the Phase 7.1 dataset, so payment
// status is derived from the same order status: an order that was
// cancelled or returned is treated as refunded, everything else as paid.
const PAYMENT_STATUS_BY_ORDER_STATUS: Record<OrderStatus, PaymentStatus> = {
  Delivered: 'Paid',
  Shipped: 'Paid',
  Processing: 'Paid',
  Cancelled: 'Refunded',
  Returned: 'Refunded',
}

export function deliveryStatusFor(status: OrderStatus): DeliveryStatus {
  return DELIVERY_STATUS_BY_ORDER_STATUS[status]
}
export function shippingStatusFor(status: OrderStatus): ShippingStatus {
  return SHIPPING_STATUS_BY_ORDER_STATUS[status]
}
export function paymentStatusFor(status: OrderStatus): PaymentStatus {
  return PAYMENT_STATUS_BY_ORDER_STATUS[status]
}

// Every order in the Phase 7.1 dataset belongs to the one seller in
// seller.ts, who sells on a single platform — so marketplace is a
// constant derived from seller.ts, not a per-order guess.
const MARKETPLACE_LABEL: Record<typeof seller.platform, string> = {
  amazon: 'Amazon',
  flipkart: 'Flipkart',
  meesho: 'Meesho',
}

// ----------------------------------------------------------------------------
// Row shape shared by every Orders-related screen
// ----------------------------------------------------------------------------

export interface OrderItemView {
  sku: string
  name: string
  quantity: number
  unitPrice: number
  lineTotal: number
}

export interface OrderViewRow {
  id: string // Order ID
  orderNumber: string
  customerName: string // Customer Name
  customerLocation: string
  product: string // Product (display summary across 1-3 line items)
  itemCount: number
  quantity: number // Quantity (total units across all line items)
  orderDate: string // Order Date (ISO)
  deliveryStatus: DeliveryStatus
  paymentStatus: PaymentStatus
  orderValue: number // Order Value
  marketplace: string // Marketplace
  shippingStatus: ShippingStatus
  paymentMethod: Order['paymentMethod']
  items: OrderItemView[]
  // 'mock' rows come from this file; 'live' rows are normalized from the
  // real backend (see hooks/useOrdersData.ts) into this same shape so
  // every Orders-related screen can render one row type regardless of
  // where the data actually came from.
  source: 'mock' | 'live'
}

function productSummary(order: Order): string {
  const [first, ...rest] = order.items
  if (!first) return '—'
  return rest.length === 0 ? first.name : `${first.name} +${rest.length} more`
}

function totalQuantity(order: Order): number {
  return order.items.reduce((sum, item) => sum + item.quantity, 0)
}

function toViewRow(order: Order): OrderViewRow {
  return {
    id: order.id,
    orderNumber: order.orderNumber,
    customerName: order.customer.name,
    customerLocation: `${order.customer.city}, ${order.customer.state}`,
    product: productSummary(order),
    itemCount: order.items.length,
    quantity: totalQuantity(order),
    orderDate: order.orderDate,
    deliveryStatus: deliveryStatusFor(order.status),
    paymentStatus: paymentStatusFor(order.status),
    orderValue: order.total,
    marketplace: MARKETPLACE_LABEL[seller.platform],
    shippingStatus: shippingStatusFor(order.status),
    paymentMethod: order.paymentMethod,
    items: order.items.map(item => ({
      sku: item.sku,
      name: item.name,
      quantity: item.quantity,
      unitPrice: item.unitPrice,
      lineTotal: item.lineTotal,
    })),
    source: 'mock',
  }
}

// Computed once at import time, same pattern as analytics.ts — cheap (200
// rows) and keeps every consumer working off one identical array instance.
export const mockOrderRows: OrderViewRow[] = orders.map(toViewRow)

export function getMockOrderRowById(id: string): OrderViewRow | undefined {
  return mockOrderRows.find(row => row.id === id)
}

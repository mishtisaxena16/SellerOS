// ============================================================================
// SellerOS — Phase 7.1: Mock Orders Dataset
// ============================================================================
// ~200 orders for ABC Fashion Store, generated deterministically (index-based
// arithmetic, no Math.random) so the dataset is reproducible across runs.
// Every order's line items reference a real product from products.ts by id,
// and every dollar amount (unitPrice/lineTotal/subtotal/tax/total) is derived
// from that product's actual price — never a separately hand-typed number —
// so orders can never fall out of sync with the product catalog.
// ============================================================================

import { products, Product } from './products'

export type OrderStatus = 'Delivered' | 'Shipped' | 'Processing' | 'Cancelled' | 'Returned'
export type PaymentMethod = 'Credit Card' | 'Debit Card' | 'Amazon Pay' | 'Gift Card'

export interface OrderItem {
  productId: string
  sku: string
  name: string
  category: Product['category']
  unitPrice: number
  quantity: number
  lineTotal: number
}

export interface OrderCustomer {
  name: string
  city: string
  state: string
}

export interface Order {
  id: string
  orderNumber: string
  orderDate: string // ISO date
  customer: OrderCustomer
  items: OrderItem[]
  subtotal: number
  shippingFee: number
  tax: number
  total: number
  status: OrderStatus
  paymentMethod: PaymentMethod
}

const ORDER_COUNT = 200

// 65% Delivered / 15% Shipped / 10% Processing / 5% Cancelled / 5% Returned,
// expressed as an explicit 20-slot cycle (200 / 20 = 10 exact repeats) rather
// than a probability roll, so the distribution is exact and reproducible.
const STATUS_CYCLE: OrderStatus[] = [
  'Delivered', 'Delivered', 'Delivered', 'Delivered', 'Delivered',
  'Delivered', 'Delivered', 'Delivered', 'Delivered', 'Delivered',
  'Delivered', 'Delivered', 'Delivered',
  'Shipped', 'Shipped', 'Shipped',
  'Processing', 'Processing',
  'Cancelled',
  'Returned',
]

const PAYMENT_CYCLE: PaymentMethod[] = ['Credit Card', 'Amazon Pay', 'Debit Card', 'Credit Card', 'Gift Card']

const CUSTOMER_LOCATIONS: Array<{ name: string; city: string; state: string }> = [
  { name: 'Olivia Martinez', city: 'Charlotte', state: 'NC' },
  { name: 'Ethan Johnson', city: 'Raleigh', state: 'NC' },
  { name: 'Sophia Williams', city: 'Atlanta', state: 'GA' },
  { name: 'Liam Brown', city: 'Nashville', state: 'TN' },
  { name: 'Ava Davis', city: 'Columbia', state: 'SC' },
  { name: 'Noah Miller', city: 'Richmond', state: 'VA' },
  { name: 'Isabella Wilson', city: 'Orlando', state: 'FL' },
  { name: 'Mason Moore', city: 'Austin', state: 'TX' },
  { name: 'Mia Taylor', city: 'Phoenix', state: 'AZ' },
  { name: 'James Anderson', city: 'Denver', state: 'CO' },
  { name: 'Charlotte Thomas', city: 'Columbus', state: 'OH' },
  { name: 'Benjamin Jackson', city: 'Indianapolis', state: 'IN' },
  { name: 'Amelia White', city: 'Sacramento', state: 'CA' },
  { name: 'Lucas Harris', city: 'Portland', state: 'OR' },
  { name: 'Harper Martin', city: 'Kansas City', state: 'MO' },
]

// 6-month order window: 2025-02-01 through 2025-07-28 (178 days), spread
// evenly across all 200 orders via integer day-offset arithmetic.
const ORDER_WINDOW_START = new Date('2025-02-01T00:00:00Z')
const ORDER_WINDOW_DAYS = 178

function dateForOrderIndex(i: number): string {
  const dayOffset = Math.floor((i * ORDER_WINDOW_DAYS) / (ORDER_COUNT - 1))
  const d = new Date(ORDER_WINDOW_START)
  d.setUTCDate(d.getUTCDate() + dayOffset)
  return d.toISOString().slice(0, 10)
}

function round2(n: number): number {
  return Math.round(n * 100) / 100
}

function buildOrderItems(i: number): OrderItem[] {
  // 1-3 line items per order, cycling deterministically off the index.
  const itemCount = (i % 3) + 1
  const items: OrderItem[] = []
  const usedIndexes = new Set<number>()

  for (let slot = 0; slot < itemCount; slot++) {
    // Distinct deterministic product index per slot, guaranteed not to
    // collide with an already-used index in this same order.
    let productIndex = (i * (7 + slot * 6) + (3 + slot * 11)) % products.length
    while (usedIndexes.has(productIndex)) {
      productIndex = (productIndex + 1) % products.length
    }
    usedIndexes.add(productIndex)

    const product = products[productIndex]
    const quantity = ((i + slot) % 3) + 1
    const unitPrice = product.price
    items.push({
      productId: product.id,
      sku: product.sku,
      name: product.name,
      category: product.category,
      unitPrice,
      quantity,
      lineTotal: round2(unitPrice * quantity),
    })
  }
  return items
}

function buildOrder(i: number): Order {
  const items = buildOrderItems(i)
  const subtotal = round2(items.reduce((sum, item) => sum + item.lineTotal, 0))
  const shippingFee = subtotal >= 35 ? 0 : 5.99
  const tax = round2(subtotal * 0.07) // flat 7% sales tax, matching seller HQ (NC)
  const total = round2(subtotal + shippingFee + tax)
  const customer = CUSTOMER_LOCATIONS[i % CUSTOMER_LOCATIONS.length]

  return {
    id: `ord_${String(i + 1).padStart(3, '0')}`,
    orderNumber: `AMZ-2025-${String(100000 + i)}`,
    orderDate: dateForOrderIndex(i),
    customer,
    items,
    subtotal,
    shippingFee,
    tax,
    total,
    status: STATUS_CYCLE[i % STATUS_CYCLE.length],
    paymentMethod: PAYMENT_CYCLE[i % PAYMENT_CYCLE.length],
  }
}

export const orders: Order[] = Array.from({ length: ORDER_COUNT }, (_, i) => buildOrder(i))

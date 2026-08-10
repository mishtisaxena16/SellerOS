// ============================================================================
// SellerOS — Phase 7.1: Mock Inventory Dataset
// ============================================================================
// One inventory record per product in products.ts (50/50 — never fewer,
// never extra). Available stock is NOT an independent hand-typed number: it
// is this product's deterministic starting stock MINUS units actually sold
// (Delivered/Shipped/Processing order line items) PLUS units actually
// returned (Returned order line items), computed straight from orders.ts.
// Cancelled orders never touched stock, so they're excluded entirely.
// ============================================================================

import { products, Product } from './products'
import { orders } from './orders'

export type StockStatus = 'In Stock' | 'Low Stock' | 'Out of Stock'

export interface InventoryItem {
  productId: string
  sku: string
  name: string
  category: Product['category']
  warehouse: string
  startingStock: number
  unitsSold: number // Delivered + Shipped + Processing, net of Returned
  availableQuantity: number
  reorderPoint: number
  reorderQuantity: number
  lastRestocked: string // ISO date
  status: StockStatus
}

const WAREHOUSES = [
  'ABC-EAST-1 (Charlotte, NC)',
  'ABC-CENTRAL-1 (Dallas, TX)',
  'ABC-WEST-1 (Reno, NV)',
]

// A handful of the best-reviewed products are deliberately given a smaller
// starting stock than the general formula below would assign, so that
// popular items realistically show up as Low Stock / Out of Stock once
// actual units sold (from orders.ts) are subtracted — rather than every
// product uniformly showing "plenty of stock," which no real seller
// dashboard ever looks like.
const LOW_STARTING_STOCK_OVERRIDES: Record<string, number> = {
  p001: 22, // Floral Wrap Midi Dress — high demand, deliberately tight
  p035: 18, // High-Rise Compression Leggings — best-reviewed activewear item
  p017: 16, // Vintage Wash Denim Jeans — top-rated, runs low
  p044: 20, // Wool Blend Trench Coat — seasonal, limited run
}

function startingStockFor(index: number, productId: string): number {
  if (productId in LOW_STARTING_STOCK_OVERRIDES) {
    return LOW_STARTING_STOCK_OVERRIDES[productId]
  }
  // Deterministic spread: 60-120 units depending on catalog position.
  return 60 + (index % 7) * 10
}

// Sum quantities sold (Delivered/Shipped/Processing) and returned (Returned)
// per product, straight from the same order records analytics.ts also reads.
function computeUnitsSold(): Record<string, number> {
  const sold: Record<string, number> = {}
  for (const order of orders) {
    for (const item of order.items) {
      const current = sold[item.productId] ?? 0
      if (order.status === 'Delivered' || order.status === 'Shipped' || order.status === 'Processing') {
        sold[item.productId] = current + item.quantity
      } else if (order.status === 'Returned') {
        sold[item.productId] = current - item.quantity
      }
      // Cancelled: no stock impact at all.
    }
  }
  return sold
}

const unitsSoldByProduct = computeUnitsSold()

// Deterministic restock dates: spread over the 60 days before the order
// window closes (2025-07-28), cycling by catalog index.
const RESTOCK_WINDOW_END = new Date('2025-07-28T00:00:00Z')
function lastRestockedFor(index: number): string {
  const daysAgo = (index * 3) % 60
  const d = new Date(RESTOCK_WINDOW_END)
  d.setUTCDate(d.getUTCDate() - daysAgo)
  return d.toISOString().slice(0, 10)
}

export const inventory: InventoryItem[] = products.map((product, index) => {
  const startingStock = startingStockFor(index, product.id)
  const unitsSold = unitsSoldByProduct[product.id] ?? 0
  const availableQuantity = Math.max(0, startingStock - unitsSold)
  const reorderPoint = Math.round(startingStock * 0.2)
  const reorderQuantity = Math.round(startingStock * 0.5)

  let status: StockStatus
  if (availableQuantity <= 0) {
    status = 'Out of Stock'
  } else if (availableQuantity <= reorderPoint) {
    status = 'Low Stock'
  } else {
    status = 'In Stock'
  }

  return {
    productId: product.id,
    sku: product.sku,
    name: product.name,
    category: product.category,
    warehouse: WAREHOUSES[index % WAREHOUSES.length],
    startingStock,
    unitsSold,
    availableQuantity,
    reorderPoint,
    reorderQuantity,
    lastRestocked: lastRestockedFor(index),
    status,
  }
})

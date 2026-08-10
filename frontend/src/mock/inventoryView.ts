// ============================================================================
// SellerOS — Phase 7.3: Mock Inventory View-Model Adapter
// ============================================================================
// Pure, read-only adapter layer. It does NOT invent or generate any
// inventory data — it only *reshapes* the existing `inventory` array from
// ./inventory.ts (itself already tied to ./products.ts and ./orders.ts, per
// Phase 7.1) into the flat row shape every Inventory-related screen needs:
//   Product Name · SKU · Category · Available Stock · Reserved Stock ·
//   Reorder Level · Warehouse · Inventory Status · Last Updated
//
// Same pattern as mock/ordersView.ts (Phase 7.2). Nothing here touches the
// backend, connectors, Playwright, routing, or auth. Zero imports outside
// ./inventory and ./orders, and zero network/API calls — a synchronous,
// in-memory transform.
// ============================================================================

import { inventory, type InventoryItem, type StockStatus } from './inventory'
import { orders } from './orders'

export type { StockStatus }

// ----------------------------------------------------------------------------
// Reserved stock derivation
// ----------------------------------------------------------------------------
// inventory.ts models "available quantity" only — it does not carry a
// reserved/committed figure. Rather than hand-typing one, "reserved" is
// derived the same way inventory.ts derives `unitsSold`: read straight off
// orders.ts. A unit is reserved when it belongs to an order that has been
// placed and accepted but not yet shipped (status 'Processing') — it's
// committed against this product's stock but hasn't left the warehouse yet.
// Shipped/Delivered orders are not reserved (already fulfilled and already
// subtracted from availableQuantity by inventory.ts); Cancelled/Returned
// orders never held stock. This keeps Available + Reserved always
// traceable back to the same order records analytics.ts and inventory.ts
// already use, so the two figures can't drift out of sync with each other.
function computeReservedByProduct(): Record<string, number> {
  const reserved: Record<string, number> = {}
  for (const order of orders) {
    if (order.status !== 'Processing') continue
    for (const item of order.items) {
      reserved[item.productId] = (reserved[item.productId] ?? 0) + item.quantity
    }
  }
  return reserved
}

const reservedByProduct = computeReservedByProduct()

// ----------------------------------------------------------------------------
// Row shape shared by every Inventory-related screen
// ----------------------------------------------------------------------------

export interface InventoryViewRow {
  productId: string
  sku: string // SKU
  name: string // Product Name
  category: string // Category
  availableQuantity: number // Available Stock
  reservedQuantity: number // Reserved Stock
  reorderLevel: number // Reorder Level
  warehouse: string // Warehouse
  status: StockStatus // Inventory Status (In Stock / Low Stock / Out of Stock)
  lastUpdated: string // Last Updated (ISO date)
  // 'mock' rows come from this file; 'live' rows are normalized from the
  // real backend (see hooks/useInventoryData.ts) into this same shape so
  // every Inventory-related screen can render one row type regardless of
  // where the data actually came from — same convention as OrderViewRow.
  source: 'mock' | 'live'
}

function toViewRow(item: InventoryItem): InventoryViewRow {
  return {
    productId: item.productId,
    sku: item.sku,
    name: item.name,
    category: item.category,
    availableQuantity: item.availableQuantity,
    reservedQuantity: reservedByProduct[item.productId] ?? 0,
    reorderLevel: item.reorderPoint,
    warehouse: item.warehouse,
    // Inventory Status is read directly from inventory.ts, not
    // recomputed here — that field is the same one Dashboard/analytics.ts
    // already sums for lowStockCount/outOfStockCount, so the badge on this
    // screen can never disagree with the dashboard totals.
    status: item.status,
    lastUpdated: item.lastRestocked,
    source: 'mock',
  }
}

// Computed once at import time, same pattern as ordersView.ts/analytics.ts —
// cheap (50 rows) and keeps every consumer working off one identical array.
export const mockInventoryRows: InventoryViewRow[] = inventory.map(toViewRow)

export function getMockInventoryRowBySku(sku: string): InventoryViewRow | undefined {
  return mockInventoryRows.find(row => row.sku === sku)
}

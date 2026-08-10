import { useEffect, useState } from 'react'
import { getInventory, type InventoryItem as LiveInventoryItem } from '../api/inventory'
import { ApiError } from '../api/client'
import type { Platform } from '../api/marketplace'
import { mockInventoryRows, type InventoryViewRow, type StockStatus } from '../mock/inventoryView'

export type { InventoryViewRow }

// ============================================================================
// Phase 7.3 — unified Inventory data source
// ============================================================================
// Every Inventory-related screen should see one row shape (InventoryViewRow)
// regardless of whether the data came from the live backend (GET /inventory)
// or the Phase 7.1 mock dataset. This hook:
//   1. Always calls the existing, unmodified `getInventory` API first.
//   2. Normalizes a successful, non-empty response into InventoryViewRow[].
//   3. Falls back to the existing mock dataset (frontend/src/mock/inventory.ts,
//      via inventoryView.ts) when the backend has no marketplace connected,
//      returns zero items, or can't be reached at all — matching the exact
//      pattern already used by useOrdersData.ts and documented in
//      PlatformContext ("dashboard pages fall back to their own mock data").
// No backend, connector, routing, or auth code is touched by this hook — it
// only reads from the existing api/inventory.ts client and the existing
// mock dataset.
// ============================================================================

type PlatformFilter = 'all' | Platform

// The live backend mirrors backend.ai.models.models.Inventory, which today
// only carries: platform, sku, available_quantity, reserved_quantity,
// warehouse, raw. It does not model product name, category, reorder level,
// or a last-updated timestamp yet — rather than invent data that isn't
// there, those fields are surfaced honestly (falling back to `raw` if the
// connector happened to include it, otherwise a clear placeholder).
const LOW_STOCK_THRESHOLD = 20

function statusFor(availableQuantity: number): StockStatus {
  if (availableQuantity <= 0) return 'Out of Stock'
  if (availableQuantity < LOW_STOCK_THRESHOLD) return 'Low Stock'
  return 'In Stock'
}

function readRawString(raw: Record<string, unknown>, ...keys: string[]): string | null {
  for (const key of keys) {
    const value = raw[key]
    if (typeof value === 'string' && value.trim().length > 0) return value
  }
  return null
}

function readRawNumber(raw: Record<string, unknown>, ...keys: string[]): number | null {
  for (const key of keys) {
    const value = raw[key]
    if (typeof value === 'number' && Number.isFinite(value)) return value
  }
  return null
}

function normalizeLiveItem(item: LiveInventoryItem): InventoryViewRow {
  const raw = item.raw ?? {}
  return {
    productId: item.sku,
    sku: item.sku,
    name: readRawString(raw, 'name', 'title', 'product_name') ?? item.sku,
    category: readRawString(raw, 'category') ?? '—',
    availableQuantity: item.available_quantity,
    reservedQuantity: item.reserved_quantity,
    // Not modeled on the live backend yet — same threshold-based fallback
    // this page already used before Phase 7.3, kept as-is rather than
    // guessed at a per-product level.
    reorderLevel: readRawNumber(raw, 'reorder_point', 'reorder_level') ?? LOW_STOCK_THRESHOLD,
    warehouse: item.warehouse ?? '—',
    status: statusFor(item.available_quantity),
    lastUpdated: readRawString(raw, 'last_updated', 'updated_at') ?? '—',
    source: 'live',
  }
}

// The Phase 7.1 mock dataset represents a single Amazon seller — so it only
// stands in for the 'all' or 'amazon' filter, rather than pretending to have
// Flipkart/Meesho inventory that was never generated. Same rule
// useOrdersData.ts applies to mockOrderRows.
function mockRowsForPlatform(selected: PlatformFilter): InventoryViewRow[] {
  if (selected === 'all' || selected === 'amazon') return mockInventoryRows
  return []
}

export interface UseInventoryDataResult {
  rows: InventoryViewRow[]
  loading: boolean
  error: { status: number; message: string } | null
  // True when the rows on screen are the Phase 7.1 mock dataset rather than
  // a live backend response (no marketplace connected, zero items, or the
  // backend couldn't be reached).
  usingMockData: boolean
}

export function useInventoryData(selected: PlatformFilter): UseInventoryDataResult {
  const [rows, setRows] = useState<InventoryViewRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<{ status: number; message: string } | null>(null)
  const [usingMockData, setUsingMockData] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    getInventory(selected)
      .then(res => {
        if (cancelled) return
        if (res.success && res.items.length > 0) {
          setRows(res.items.map(normalizeLiveItem))
          setUsingMockData(false)
        } else {
          // No live inventory (either no marketplace connected, or a
          // connected marketplace with nothing in it yet) — fall back to
          // the mock dataset so the dashboard still shows a realistic
          // inventory picture.
          setRows(mockRowsForPlatform(selected))
          setUsingMockData(true)
          if (!res.success) setError({ status: 200, message: res.message || 'Inventory could not be fetched.' })
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

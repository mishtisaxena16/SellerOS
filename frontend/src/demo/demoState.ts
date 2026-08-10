// ============================================================================
// SellerOS — Phase 7.7A: Demo Reset Infrastructure — demoState.ts
// ============================================================================
// Single source of truth for "what does a freshly-loaded demo look like,
// and what does it currently look like right now". Reuses every existing
// mock dataset/view-model (products.ts / orders.ts / inventory.ts /
// inventoryView.ts / listingsView.ts / businessIntelligenceView.ts /
// seller.ts) exactly as-is — nothing here re-declares or hand-types a
// second copy of any seller/order/inventory/listing/analytics figure.
//
// Two things live here:
//   1. INITIAL_DEMO_STATE — a frozen, one-time snapshot of the mock data
//      as it exists at import time (the "factory reset" target).
//   2. The live demo store — a mutable, subscribable copy of the same
//      shape that anything in the app simulating a demo edit (a status
//      change, a restock, a listing publish, a scenario/seller switch,
//      a chat session) can read from and write to, entirely client-side.
//      No API calls, no backend, no persistence beyond this module.
//
// demoReset.ts is the only other file that should call `patchDemoState` —
// everything else should treat the live store as read-only via
// `getDemoState()` / `subscribeToDemoState()`.
// ============================================================================

import { orders, type Order } from '../mock/orders'
import { inventory, type InventoryItem } from '../mock/inventory'
import { mockListingRows, type ListingViewRow } from '../mock/listingsView'
import {
  getMockBusinessIntelligence,
  type BusinessIntelligenceView,
} from '../mock/businessIntelligenceView'
import { seller } from '../mock/seller'

// ----------------------------------------------------------------------------
// Types
// ----------------------------------------------------------------------------

/** Default platform filter Business Intelligence is derived for when no
 * scenario/platform switch has changed it — matches the same 'all' default
 * PlatformContext.tsx already uses for its own selected-platform filter. */
export const DEFAULT_PLATFORM_FILTER = 'all' as const

/** Default demo scenario. There's only one scenario/seller in the mock
 * dataset today (ABC Fashion Store) — this exists so future scenarios can
 * be introduced without changing the shape of DemoState or the reset API. */
export const DEFAULT_SCENARIO = 'default'

export interface DemoMutation {
  id: string
  /** Free-form label for what kind of simulated edit this was, e.g.
   * "order-status-change", "inventory-restock", "listing-published". */
  type: string
  appliedAt: string // ISO timestamp
  payload?: unknown
}

export interface DemoState {
  scenario: string
  selectedSellerId: string
  chatSessionId: string | null
  orders: Order[]
  inventory: InventoryItem[]
  listings: ListingViewRow[]
  businessIntelligence: BusinessIntelligenceView
  mutations: DemoMutation[]
}

// ----------------------------------------------------------------------------
// Cloning helper — every dataset here is plain, JSON-serializable data
// (numbers/strings/dates-as-ISO-strings/nested objects/arrays), same
// assumption products.ts/orders.ts/inventory.ts already rely on.
// ----------------------------------------------------------------------------

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

// ----------------------------------------------------------------------------
// Initial snapshot — built once, from the existing mock modules only.
// ----------------------------------------------------------------------------

function buildDemoState(overrides?: Partial<DemoState>): DemoState {
  return {
    scenario: DEFAULT_SCENARIO,
    selectedSellerId: seller.id,
    chatSessionId: null,
    orders: clone(orders),
    inventory: clone(inventory),
    listings: clone(mockListingRows),
    businessIntelligence: clone(getMockBusinessIntelligence(DEFAULT_PLATFORM_FILTER)),
    mutations: [],
    ...overrides,
  }
}

/** The pristine, original demo state — what "Reset Entire Demo" restores
 * back to. Captured once at module load; never mutated after that. */
export const INITIAL_DEMO_STATE: DemoState = Object.freeze(buildDemoState())

// ----------------------------------------------------------------------------
// Live store — the mutable "current runtime demo state"
// ----------------------------------------------------------------------------

let liveState: DemoState = buildDemoState()

type DemoStateListener = (state: DemoState) => void
const listeners = new Set<DemoStateListener>()

/** Current runtime demo state. Treat this as read-only outside of
 * demoReset.ts — mutate via `patchDemoState` so subscribers are notified. */
export function getDemoState(): DemoState {
  return liveState
}

/** Subscribe to every demo-state change (including resets). Returns an
 * unsubscribe function. Safe to call from a React effect. */
export function subscribeToDemoState(listener: DemoStateListener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

/** Merges `partial` into the live demo state and notifies subscribers.
 * Exported for demoReset.ts; not intended for ad-hoc use elsewhere — that
 * would recreate the "every page loads/mutates mock data individually"
 * problem this infrastructure exists to avoid. */
export function patchDemoState(partial: Partial<DemoState>): DemoState {
  liveState = { ...liveState, ...partial }
  listeners.forEach((listener) => listener(liveState))
  return liveState
}

/** Appends one entry to the live mutation log — the "Any mock mutations"
 * record the reset system restores back to empty. Callers only need to
 * supply what changed; id/timestamp are filled in here. */
export function recordMockMutation(mutation: Omit<DemoMutation, 'id' | 'appliedAt'>): DemoMutation {
  const entry: DemoMutation = {
    id: `demo_mut_${Date.now()}_${Math.random().toString(16).slice(2)}`,
    appliedAt: new Date().toISOString(),
    ...mutation,
  }
  patchDemoState({ mutations: [...liveState.mutations, entry] })
  return entry
}

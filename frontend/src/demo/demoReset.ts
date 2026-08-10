// ============================================================================
// SellerOS — Phase 7.7A: Demo Reset Infrastructure — demoReset.ts
// ============================================================================
// Restores the live demo store (demoState.ts) back to INITIAL_DEMO_STATE —
// the snapshot captured from the existing mock dataset at module load.
// No dataset is re-declared or hand-typed here: every reset function below
// only re-clones a field already present on INITIAL_DEMO_STATE.
//
// No API calls. No backend/connector/Playwright/RAG/AI changes. No browser
// reload — every function here just updates the in-memory live store and
// notifies subscribers via patchDemoState/subscribeToDemoState.
// ============================================================================

import {
  DEFAULT_SCENARIO,
  INITIAL_DEMO_STATE,
  getDemoState,
  patchDemoState,
  type DemoState,
} from './demoState'

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

/** Restores orders to their original mock state. */
export function resetOrders(): DemoState {
  return patchDemoState({ orders: clone(INITIAL_DEMO_STATE.orders) })
}

/** Restores inventory (stock levels, statuses) to their original mock state. */
export function resetInventory(): DemoState {
  return patchDemoState({ inventory: clone(INITIAL_DEMO_STATE.inventory) })
}

/** Restores listings (Product Studio catalog rows) to their original mock state. */
export function resetListings(): DemoState {
  return patchDemoState({ listings: clone(INITIAL_DEMO_STATE.listings) })
}

/** Restores Business Intelligence derived values to their original mock state. */
export function resetBusinessData(): DemoState {
  return patchDemoState({
    businessIntelligence: clone(INITIAL_DEMO_STATE.businessIntelligence),
  })
}

/** Restores the selected mock seller back to the original demo seller. */
export function resetSelectedSeller(): DemoState {
  return patchDemoState({ selectedSellerId: INITIAL_DEMO_STATE.selectedSellerId })
}

/** Restores the chat session id back to its original (unset) state — the
 * next chat message sent will start a brand-new session, same as a first
 * visit to the demo. */
export function resetChatSession(): DemoState {
  return patchDemoState({ chatSessionId: INITIAL_DEMO_STATE.chatSessionId })
}

/** Clears the recorded log of simulated demo mutations without touching
 * any other part of the live state. */
export function resetMockMutations(): DemoState {
  return patchDemoState({ mutations: clone(INITIAL_DEMO_STATE.mutations) })
}

/** Restores the current scenario back to the default demo scenario. */
export function resetScenario(): DemoState {
  return patchDemoState({ scenario: DEFAULT_SCENARIO })
}

/**
 * Full demo reset — restores every piece of demo state back to
 * INITIAL_DEMO_STATE in one call, without reloading the browser.
 * Composed entirely from the individual reset*() functions above so
 * there's exactly one place each dataset's reset logic lives.
 */
export function resetEntireDemo(): DemoState {
  resetScenario()
  resetSelectedSeller()
  resetChatSession()
  resetOrders()
  resetInventory()
  resetListings()
  resetBusinessData()
  resetMockMutations()
  return getDemoState()
}

export { getDemoState, subscribeToDemoState } from './demoState'

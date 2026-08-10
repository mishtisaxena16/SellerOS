# Phase 7.3 — Mock Inventory Module Integration

## Goal

Wire the Phase 7.1 mock Inventory dataset (`inventory.ts`) into the
existing Inventory screen so the app shows a realistic, fully-populated
inventory picture for ABC Fashion Store — without touching the backend,
AI/agent architecture, RAG, connector layer, Playwright, marketplace
APIs, routing, sidebar, or auth. Same approach as Phase 7.2 (Orders).

## What changed

### New files

- **`frontend/src/mock/inventoryView.ts`** — a pure, read-only adapter.
  It does not generate or duplicate any inventory data; it only
  *reshapes* the existing `inventory` array (from `inventory.ts`, which
  is already tied to `products.ts` and `orders.ts`) into the flat row
  shape every Inventory-related screen needs:

  `Product Name · SKU · Category · Available Stock · Reserved Stock ·
  Reorder Level · Warehouse · Inventory Status · Last Updated`

  - **Available Stock**, **Reorder Level**, **Inventory Status**, and
    **Warehouse** are read straight from `inventory.ts` — not
    recomputed — so this screen can never disagree with the numbers
    `analytics.ts` already sums for the Dashboard
    (`inventoryHealth.lowStockCount` / `outOfStockCount` / etc).
  - **Reserved Stock** did not exist as a field on `inventory.ts`, so it
    is derived the same way `inventory.ts` derives `unitsSold`: summed
    straight from `orders.ts`. A unit counts as reserved when it belongs
    to an order with status `'Processing'` — placed and accepted, not
    yet shipped. Shipped/Delivered orders are already fulfilled (and
    already subtracted from `availableQuantity` by `inventory.ts`);
    Cancelled/Returned orders never held stock. This keeps Available and
    Reserved traceable back to the same order records, so they can't
    drift apart.
  - **Last Updated** maps directly from `inventory.ts`'s
    `lastRestocked` field (renamed for the UI label only — same value).
  - Zero imports outside `./inventory` and `./orders`, zero network/API
    calls — a synchronous, in-memory transform, computed once at import
    time (`mockInventoryRows`), same pattern as `ordersView.ts` /
    `analytics.ts`.

- **`frontend/src/hooks/useInventoryData.ts`** — a small hook that gives
  every Inventory-related screen one unified row type
  (`InventoryViewRow`) regardless of where the data comes from:
  1. Calls the existing, unmodified `getInventory()` API client first.
  2. Normalizes a successful, non-empty response into
     `InventoryViewRow[]`. The live backend
     (`backend.ai.models.models.Inventory`) does not yet model product
     name, category, reorder level, or a last-updated timestamp — those
     are read from the connector's `raw` payload if present, otherwise
     shown honestly as `—` rather than invented. Live status is derived
     with the same 20-unit low-stock threshold this page already used
     before Phase 7.3.
  3. Falls back to `mockInventoryRows` from `inventoryView.ts` when the
     backend has no marketplace connected, returns zero items, or can't
     be reached — the same "fall back to mock data" behavior already
     used by `useOrdersData.ts` and documented in `PlatformContext.tsx`.
  - Exposes `usingMockData` so the UI can show an honest "showing demo
    data" notice instead of silently mixing sources.
  - The mock dataset represents a single Amazon seller, so it's only
    surfaced for the `all` / `amazon` platform filter — same rule
    `useOrdersData.ts` applies to `mockOrderRows`.

### Modified files

- **`frontend/src/pages/Inventory.tsx`** — rewired onto
  `useInventoryData` instead of calling `getInventory` directly. No
  layout redesign; the same card/table/badge/search components and
  classes are reused. Changes:
  - Table now shows all nine required fields: Product Name, SKU,
    Category, Available (with the existing stock bar), Reserved,
    Reorder Level, Warehouse, Status (badge), Last Updated.
  - Status badges (`In Stock` / `Low Stock` / `Out of Stock`) now come
    from each row's own `status` field instead of a hard-coded
    `LOW_STOCK_THRESHOLD` re-check on every render — for mock rows this
    is the exact value `analytics.ts` already uses; for live rows it's
    computed once in the hook.
  - Search now matches SKU, product name, or category — not just SKU.
  - Low Stock / Out of Stock filter buttons now filter by `status`
    instead of re-deriving it inline.
  - Added a result count next to the filters, matching the pattern
    already used on the Orders page.
  - A small `bg-accent-blue-soft` notice (same style already used on
    Orders) appears only when `usingMockData` is true.

## What did NOT change

Per scope: no backend, connector, Playwright, marketplace API, routing,
sidebar, or auth code was touched. `inventory.ts`, `orders.ts`,
`products.ts`, and `seller.ts` from Phase 7.1 were not modified — no new
mock inventory was generated, and no data is duplicated between files.
`api/inventory.ts` (the live API client) is called exactly as before; it
is only wrapped, not altered.

## Verified

- `inventoryView.ts` and `useInventoryData.ts` type-check cleanly
  (`npx tsc --noEmit` — zero new errors; only a pre-existing, unrelated
  `tsconfig` deprecation notice for `baseUrl`).
- Every row's `status` / `availableQuantity` / `reorderLevel` in
  `inventoryView.ts` is read directly from `inventory.ts`, matching
  `analytics.ts`'s `inventoryHealth` totals exactly (0 hand-typed
  duplicates).
- `reservedQuantity` is computed directly from `orders.ts` (`Processing`
  status only), consistent with how `inventory.ts` itself already
  computes `unitsSold` from the same order records.
- Live-item and mock-item paths both resolve to the same
  `InventoryViewRow` shape, so `Inventory.tsx` has one render path
  regardless of data source — matching the Orders page's pattern.

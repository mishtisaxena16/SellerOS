# Phase 7.2 — Mock Orders Module Integration

## Goal

Wire the Phase 7.1 mock Orders dataset (`orders.ts`) into the existing
Orders screen so the app shows a realistic, fully-populated order history
for ABC Fashion Store — without touching the backend, AI/agent
architecture, RAG, connector layer, Playwright, marketplace APIs,
routing, sidebar, or auth.

## What changed

### New files

- **`frontend/src/mock/ordersView.ts`** — a pure, read-only adapter. It
  does not generate or duplicate any order data; it only *reshapes* the
  existing `orders` array (from `orders.ts`, which is already tied to
  `products.ts` and `seller.ts`) into the flat row shape every
  Orders-related screen needs:

  `Order ID · Customer Name · Product · Quantity · Order Date ·
  Delivery Status · Payment Status · Order Value · Marketplace ·
  Shipping Status`

  - **Delivery Status**, **Shipping Status**, and **Payment Status** are
    all derived from the single existing `order.status` field via three
    named mapping tables (`deliveryStatusFor`, `shippingStatusFor`,
    `paymentStatusFor`), so they can never drift out of sync with each
    other or with each order's real status.
  - **Marketplace** is derived from `seller.ts` (`seller.platform`),
    since every order in the dataset belongs to the one seller defined
    there — not a per-order guess.
  - **Product** and **Quantity** are computed straight from each order's
    real `items[]` (product name for a single-item order, `"<name> +N
    more"` for multi-item orders; quantity is the sum of all line-item
    quantities).
  - Has zero imports outside `./orders` and `./seller`, and zero
    network/API calls — a synchronous, in-memory transform, computed
    once at import time (`mockOrderRows`), same pattern as
    `analytics.ts`.

- **`frontend/src/hooks/useOrdersData.ts`** — a small hook that gives
  every Orders-related screen one unified row type (`OrderViewRow`)
  regardless of where the data comes from:
  1. Calls the existing, unmodified `getOrders()` API client first.
  2. Normalizes a successful, non-empty response into `OrderViewRow[]`.
  3. Falls back to `mockOrderRows` from `ordersView.ts` when the backend
     has no marketplace connected, returns zero orders, or can't be
     reached — the same "fall back to mock data" behavior already
     documented in `PlatformContext.tsx`.
  - Exposes `usingMockData` so the UI can show a small, honest "showing
    demo data" notice instead of silently mixing sources.
  - The mock dataset represents a single Amazon seller, so it's only
    surfaced for the `all` / `amazon` platform filter — it does not
    fabricate Flipkart/Meesho orders that were never generated.

### Modified files

- **`frontend/src/pages/Orders.tsx`** — rewired onto `useOrdersData`
  instead of calling `getOrders` directly. No layout redesign; the same
  card/table/badge/search components and classes are reused. Changes:
  - Table now shows all ten required fields: Order ID, Customer (name +
    city/state), Product, Qty, Marketplace, Delivery status, Payment
    status (badge), Shipping status (badge), Date, Value.
  - Search now matches order ID, order number, customer name, and
    product — not just order ID.
  - Status filter/summary strip now buckets by Shipping Status.
  - Added click-to-sort on the Date and Value column headers (asc/desc).
  - Added simple pagination (20 rows/page) — the mock dataset has 200
    orders, and the page had no pagination before; search/filter/sort
    changes reset back to page 1.
  - Detail panel extended with Customer and Payment Status, reusing the
    same panel layout.
  - A small `bg-accent-blue-soft` notice (same style already used for
    inline banners on this page) appears only when `usingMockData` is
    true.

## What did NOT change

Per scope: no backend, connector, Playwright, marketplace API, routing,
sidebar, or auth code was touched. `orders.ts`, `products.ts`,
`inventory.ts`, and `seller.ts` from Phase 7.1 were not modified — no
new mock orders were generated, and no data is duplicated between files.
`api/orders.ts` (the live API client) is called exactly as before; it is
only wrapped, not altered.

## Verified

- `ordersView.ts` and `useOrdersData.ts` type-check cleanly.
- Every row's `product`/`quantity` in `ordersView.ts` is computed
  directly from `order.items`, matching `orders.ts` exactly (0 hand-typed
  duplicates).
- `marketplace` matches `seller.ts` for all 200 mock rows.
- Live-order and mock-order paths both resolve to the same
  `OrderViewRow` shape, so `Orders.tsx` has one render path regardless of
  data source.

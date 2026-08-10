# Phase 7.1 — Mock Seller Dataset

## What changed

Added five new files under `frontend/src/mock/`:

- `seller.ts` — one seller profile: **ABC Fashion Store**, an Amazon FBA
  seller (Charlotte, NC), Gold tier, 4.6★ / 8,734 reviews.
- `products.ts` — 50 products across 6 categories (Women's Apparel,
  Men's Apparel, Footwear, Accessories, Activewear, Outerwear — 9/9/8/8/8/8),
  each with a real product name, price, cost, rating, review count, status,
  and listing date. No lorem ipsum; no placeholder names.
- `orders.ts` — 200 orders, generated deterministically (index-based
  arithmetic — no `Math.random`) over a 6-month window (Feb–Jul 2025).
  Every order's line items reference a real `productId` from `products.ts`,
  and every dollar figure (`unitPrice`, `lineTotal`, `subtotal`, `tax`,
  `total`) is derived from that product's actual price, not typed
  separately. Status mix: 65% Delivered, 15% Shipped, 10% Processing,
  5% Cancelled, 5% Returned.
- `inventory.ts` — exactly one record per product (50/50). Available stock
  is `startingStock - unitsSold + unitsReturned`, computed straight from
  `orders.ts` (Cancelled orders never touch stock; Returned orders add
  back). A handful of well-reviewed products are given a deliberately
  tighter starting stock so at least one realistically shows as low/out of
  stock, rather than every item uniformly looking fully stocked.
- `analytics.ts` — every figure (gross/net revenue, monthly trend, growth
  %, category performance, top products, inventory health, ratings) is
  **computed from** `orders.ts` / `products.ts` / `inventory.ts` at import
  time — nothing here is a separately hand-typed number. Changing a price
  in `products.ts` or adding an order in `orders.ts` recalculates every
  downstream figure automatically.

## Consistency, verified

- Every order line item's `productId` resolves to a real entry in
  `products.ts` (0 dangling references).
- `inventory.ts` has exactly one row per product, matching IDs exactly.
- `categoryPerformance` product counts sum to 50.
- `analytics.revenueSummary.grossRevenue` was independently recomputed
  from raw order totals and matches exactly.
- All five files type-check cleanly under the project's existing
  `tsconfig.json` (`strict`, `noUnusedLocals`, `noUnusedParameters`, etc.).

## What did NOT change

Per the task scope, nothing outside `frontend/src/mock/` was touched:
no backend, connector layer, Playwright code, APIs, AI/agent architecture,
RAG, routing, or sidebar/navigation changes. These files are standalone
and are not yet imported anywhere else in the app — wiring them into
pages/components is a separate follow-up task.

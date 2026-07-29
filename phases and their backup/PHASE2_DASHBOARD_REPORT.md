# SellerOS — Phase 2: Executive Dashboard Report

## Scope
Single file touched: `frontend/src/pages/Dashboard.tsx`. No routing, auth, Playwright, marketplace connectors, AI agents, backend logic, database schema, or other pages (Orders/Inventory/Analytics/Marketplace) were modified. No new dependencies were added — the rebuild reuses the project's existing `TrendChartCard` component (dependency-free SVG bar chart) and existing design tokens from `index.css`.

## Files Modified
- `frontend/src/pages/Dashboard.tsx` (rewritten)

No other files were changed. (`Dashboard.tsx.orig` backup kept alongside outputs for reference/rollback.)

## Audit Findings (Before)
- KPI row duplicated data shown elsewhere (`Connected Marketplaces`, `Inventory Items`) instead of the metrics stakeholders actually ask about in a demo (Total Revenue, Total Orders, Pending, Cancelled).
- No **Total Orders** or **Cancelled Orders** metric anywhere on the dashboard.
- `TrendChartCard` — a working, dependency-free sales/orders trend chart — already existed in the codebase but was **never used on the Dashboard** (only on Business Intelligence). It was a fully built widget sitting unused.
- No **Marketplace Overview**, **Inventory Summary**, **Top Performing Products**, or **Quick Business Insights** widgets existed on the Dashboard at all.
- Loading state was a single full-page spinner that blocked the entire dashboard, including the header — a poor look for a live demo.
- No handling for partial failures: if `/orders` or `/inventory` failed while `/dashboard/summary` succeeded, sections silently rendered "no data" empty states with no indication that a fetch actually failed (Business Intelligence already solved this with a `derivedDataError` flag; Dashboard did not).
- "Fulfillment" card duplicated the new Pending Orders KPI once cancelled/pending were added.

## Improvements Made
1. **New KPI row** — Total Revenue, Total Orders, Pending Orders, Cancelled Orders. Each prefers the live backend value (`/analytics`, `/dashboard/summary`) and only falls back to an honest client-side computation over already-fetched `/orders` data when the backend has none for that platform (mirrors the "no fabricated numbers" convention already used elsewhere in the app) — the hint text under each card always says which is happening.
2. **Inventory Summary** — Total SKUs / Healthy Stock / Low Stock / Out of Stock at a glance, with a link to the full Inventory page.
3. **Marketplace Overview** — per-connected-platform revenue, order count, and share bar (reused the same aggregation pattern Business Intelligence uses for its "Marketplace Split" card), so it now works for a single connected marketplace too, not just multi-platform sellers.
4. **Quick Business Insights** — up to 4 short, data-derived insight lines (average order value, cancellation rate, leading marketplace, low/out-of-stock warnings) built entirely from data already on the page — no new endpoint.
5. **Sales Trend Chart / Orders Trend Chart** — wired in the existing `TrendChartCard` component (previously unused on this page), giving real per-day revenue/order bars with tooltips, a loading skeleton, and an honest empty state.
6. **Recent Activity** — renamed from "Recent Orders," now shows a status icon (shipped/pending/cancelled/other) per order for faster scanning.
7. **Low Stock Products** — kept as its own dedicated widget (previously mixed into a "Stock Alerts" card), sorted lowest-quantity-first so the most urgent SKUs surface first.
8. **Top Performing Products** — new widget, top 5 SKUs by units sold from synced order line items; renders a graceful empty state if no line-item data exists yet, per the "if data exists" instruction.
9. **Loading states** — replaced the single blocking spinner with per-section skeleton placeholders (`KPISkeleton`, `SectionSkeleton`) sized to match the real widgets, so the header and layout are visible immediately and nothing jumps once data arrives.
10. **Error states** — added the same `derivedDataError` pattern Business Intelligence uses: if `/orders` or `/inventory` fails while other calls succeed, a clear banner says some sections may be incomplete, instead of silently showing empty states that look like "you have no data."
11. **Removed duplication** — dropped the standalone "Fulfillment" card (its numbers now live in the Pending Orders KPI and the Quick Insights leader line) and removed the redundant "Connected Marketplaces" / "Inventory Items" KPI tiles now that they're covered by the new Marketplace Overview / Inventory Summary widgets.
12. **Visual consistency** — every widget uses the same `card p-5` shell, heading size/weight, icon-plus-label pattern, and spacing already established elsewhere in the app (Business Intelligence, Orders, Inventory), so nothing here reads as a new design language.

## Data Mapping (existing endpoints only)
| Widget | Source |
|---|---|
| Total Revenue / Orders | `/analytics` `sales_metrics`, fallback: sum of `/orders` |
| Pending Orders | `/dashboard/summary`, fallback `/analytics` `business_metrics`, fallback computed from `/orders` status |
| Cancelled Orders | computed from `/orders` status (`cancelled`/`canceled`/`returned`/`rejected`) |
| Inventory Summary | `/inventory` |
| Marketplace Overview | connected platforms (`/marketplaces`) × `/orders` aggregation |
| Sales/Orders Trend | `/orders` (`order_date`, `total_amount`) via `TrendChartCard` |
| Recent Activity | `/orders` |
| Low Stock Products | `/inventory` (threshold: 20 units, existing constant) |
| Top Performing Products | `/orders` line items |
| Quick Business Insights | derived from the above, client-side only |

## Remaining Dashboard Limitations
- `sales_metrics` / `business_metrics` are only wired up on the backend for Amazon today (pre-existing backend limitation, out of scope for this phase) — Flipkart/Meesho sellers will see the client-computed fallback values instead, clearly labeled "Computed from synced orders."
- Cancelled Orders and Top Performing Products have no dedicated backend fields; both are computed from the `/orders` payload already being fetched, so their accuracy is bounded by what `/orders` currently returns (same caveat Business Intelligence already carries for its equivalent sections).
- A full production build (`vite build`) could not be executed in this sandbox due to a pre-existing missing native binding (`@rolldown/binding-linux-x64-gnu`) unrelated to this change — confirmed by reproducing the identical failure against the untouched original file. `tsc --noEmit` against the project's own `tsconfig.json` passes cleanly with no errors introduced.

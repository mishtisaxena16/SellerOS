# Phase 7.4 — Mock Listings Module Integration

## Goal

Integrate the Listings module (Product Studio's landing screen) with the
existing mock seller catalog (`products.ts`) while leaving every AI-powered
listing feature — the RAG-backed AI Listing Optimizer — completely
untouched.

## The seller-data / RAG split (per the brief's examples)

| Ask | Source | Touched by this phase? |
|---|---|---|
| "Show all my products" | mock `products.ts` via `listingsView.ts` | Yes — new |
| "Which of my products has poor SEO?" | mock product metrics (`seoScore`/`seoTier` in `listingsView.ts`) | Yes — new |
| "Improve this product title" | RAG (`AgentConsole` → `POST /chat` → listing_agent) | **No** |
| "What are Amazon title guidelines?" | RAG (same pipeline) | **No** |

`AgentConsole.tsx`, the `/chat` call it makes, and every AI prompt string in
`ProductStudio.tsx` (`quickPrompts`, `handlePublish`) are byte-identical to
before this phase — verified by diffing against the pre-Phase-7.4 zip.

## What changed

### New files

- **`frontend/src/mock/listingsView.ts`** — a pure, read-only adapter. It
  does not generate a new products dataset; it only *reshapes* the
  existing `products` array (from `products.ts`, the same source of truth
  `orders.ts` / `inventory.ts` / `analytics.ts` already build on) into the
  row shape the Listings screen needs: Product Name, SKU, Category,
  Marketplace, Brand, Price, Rating, Listing Status, SEO Score, Listing
  Quality Score, Image.

  Fields read straight from `products.ts` with no transformation: name,
  sku, category, price, rating, reviewCount.

  Fields derived, and how:
  - **Marketplace** / **Brand** — from `seller.ts` (`seller.platform` /
    `seller.businessName`), since every product belongs to the one
    single-platform, single-brand seller — same reasoning `ordersView.ts`
    already applies to `marketplace`.
  - **Listing Status** (`Live` / `Inactive`) — a direct relabeling of
    `product.status` (`active` / `inactive`), not a new concept.
  - **SEO Score** and **Listing Quality Score** — `products.ts` has no
    title/description/keyword fields to reuse (it's a catalog record, not
    listing copy), so these are built entirely from real fields that do
    exist: product name length (proxy for keyword-rich titles, using the
    same length bands `ProductStudio`'s own `SEOScoreRing` already applies
    to a live-typed title), review count (proxy for historical search
    performance), star rating, and active/inactive status. Full formula
    and weights are commented in the file — deliberately simple and easy
    to challenge or retune, not a black box.
  - **Image** — a deterministic placeholder URL keyed by SKU
    (`placehold.co`, per the brief's explicit "placeholder URLs" allowance).
    No real product photography exists in the mock dataset.
  - Score tiers (`Excellent` ≥80, `Good` ≥60, `Needs Improvement` <60)
    match the exact bands `SEOScoreRing` already used, just with the
    brief's requested "Needs Improvement" label instead of "Needs Work".
  - Zero imports outside `./products` and `./seller`, zero network/API
    calls — computed once at import time (`mockListingRows`), same pattern
    as `ordersView.ts` / `inventoryView.ts`.

- **`frontend/src/components/ListingsCatalogTable.tsx`** — the product
  table: search (name/SKU/category/brand), sort (name/price/rating/SEO/
  quality, click-to-toggle like Orders.tsx), status filter (All/Live/
  Inactive), SEO-tier filter, and status/tier badges — same table/badge
  CSS classes already used on the Orders and Inventory pages, no new
  visual language introduced. Each row has an "Optimize" button that calls
  an `onOptimize(row)` prop; the component has no knowledge of the AI
  pipeline, it only supplies catalog facts.

### Modified files

- **`frontend/src/pages/ProductStudio.tsx`** — landing screen only; the
  editor (form, `SEOScoreRing`, marketplace previews, `AgentConsole`) is
  untouched.
  - Renders `<ListingsCatalogTable>` below the existing "blank listing" /
    "start from SKU" cards.
  - New `startFromListing(row)` handler: prefills the editor's `title`,
    `category`, `brand`, `price`, and `imageUrl` from the clicked catalog
    row, then switches to editor mode — same shape as the existing
    `startFromSku` handler for live inventory. It does **not** touch
    `description`, `keywords`, or `features`; those are listing *copy*,
    and writing/improving copy is what the AI Listing Optimizer
    (unmodified) is for. This function never calls `/chat` itself.
  - `CATEGORIES` (the dropdown list) is now `GENERIC_CATEGORIES` (the
    original 8 home-goods options, kept for blank listings) plus a new
    `CATALOG_CATEGORIES` array with the seller's 6 real apparel
    categories, appended.
    - **Flagging this, not burying it:** `ProductStudio.tsx`'s original
      category list ("Kitchen & Dining", "Electronics", "Clothing", etc.)
      never overlapped with `products.ts`'s real categories ("Women's
      Apparel", "Footwear", "Activewear", etc.) — this page was built
      against a generic home-goods demo persona, not the ABC Fashion
      Store dataset Phase 7.1 established. Without this addition, clicking
      "Optimize" on a real catalog product would silently show the wrong
      category in the dropdown (no matching `<option>` for the prefilled
      value). This is an existing inconsistency in the codebase, not
      something introduced by this phase — I'm surfacing it here in case
      you want the generic list retired instead of extended.
  - Landing container widened from `max-w-3xl` to `max-w-6xl` — the
    original width was sized for two option cards only; a 10-column table
    needs more room. No other layout on the page changed.

## What did NOT change

Per scope: no backend, connector, Playwright, marketplace API, routing,
sidebar, or auth code was touched — verified by diffing `App.tsx`,
`components/Sidebar.tsx`, `api/client.ts`, and `api/marketplace.ts` against
the pre-Phase-7.4 zip (all byte-identical). `AgentConsole.tsx` and every AI
prompt string in `ProductStudio.tsx` are also byte-identical — no AI prompt
was modified. `products.ts`, `orders.ts`, `inventory.ts`, `seller.ts`, and
`analytics.ts` from earlier phases were not modified — no new mock products
were generated, and no data is duplicated between files.

## Verified

- `npx tsc --noEmit` — clean, zero new errors (only the pre-existing,
  unrelated `tsconfig` `baseUrl` deprecation notice).
- Diffed `AgentConsole.tsx`, `mock/analytics.ts`, `mock/inventory.ts`,
  `mock/seller.ts`, `mock/orders.ts`, `mock/products.ts`, `App.tsx`,
  `components/Sidebar.tsx`, `api/client.ts`, and `api/marketplace.ts`
  against the pre-Phase-7.4 zip — all byte-identical.
- Every field in `listingsView.ts` is either read directly from
  `products.ts`/`seller.ts` or derived by a documented, deterministic
  formula off real fields — 0 hand-typed or random values.

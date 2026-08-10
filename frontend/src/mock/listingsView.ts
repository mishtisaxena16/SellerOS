// ============================================================================
// SellerOS — Phase 7.4: Mock Listings View-Model Adapter
// ============================================================================
// Pure, read-only adapter layer. It does NOT generate a new products
// dataset — it only *reshapes* the existing `products` array from
// ./products.ts (the single source of truth already used by orders.ts,
// inventory.ts, and analytics.ts) into the flat row shape the Listings
// screen needs:
//   Product Name · SKU · Category · Marketplace · Brand · Price · Rating ·
//   Listing Status · SEO Score · Listing Quality Score · Image
//
// This file is for SELLER-OWNED PRODUCT DATA ONLY (catalog facts: what a
// product is, its price, its historical performance). It has nothing to do
// with AI-generated advice — knowledge questions like "what are Amazon
// title guidelines?" or "improve this title" still go through the existing
// RAG pipeline via AgentConsole / POST /chat, completely untouched by this
// file. See CHANGELOG_PHASE7_4.md for the split.
//
// Same pattern as ordersView.ts (Phase 7.2) / inventoryView.ts (Phase 7.3):
// zero imports outside ./products and ./seller, zero network/API calls, a
// synchronous in-memory transform computed once at import time.
// ============================================================================

import { products, type Product } from './products'
import { seller } from './seller'

export type ListingStatus = 'Live' | 'Inactive'
export type ScoreTier = 'Excellent' | 'Good' | 'Needs Improvement'

export function tierForScore(score: number): ScoreTier {
  if (score >= 80) return 'Excellent'
  if (score >= 60) return 'Good'
  return 'Needs Improvement'
}

// ----------------------------------------------------------------------------
// SEO Score & Listing Quality Score derivation
// ----------------------------------------------------------------------------
// products.ts has no title-length/keyword/description fields to reuse (it's
// a catalog record, not a listing-copy record), so these two scores are
// built entirely from the real fields that DO exist — name, reviewCount,
// rating, status — rather than random or hand-typed numbers. Weights are
// intentionally simple and documented so they're easy to challenge/adjust.
//
// SEO Score = discoverability proxy: how findable the listing likely is.
//   - Title length (product.name) as a proxy for keyword-rich titles,
//     same >80/>50/>30-char bands ProductStudio's own SEOScoreRing already
//     uses for a live-typed title.
//   - Review volume as a proxy for historical search/click performance
//     (Amazon's own ranking factors weight this heavily in practice).
//   - Active listings score higher than inactive ones (an inactive listing
//     has zero discoverability regardless of copy quality).
function seoScoreFor(product: Product): number {
  const titleLen = product.name.length
  const titleScore = titleLen > 45 ? 40 : titleLen > 30 ? 30 : titleLen > 20 ? 20 : 10

  const reviews = product.reviewCount
  const reviewScore = reviews >= 300 ? 40 : reviews >= 100 ? 30 : reviews >= 50 ? 20 : reviews >= 10 ? 10 : 0

  const statusScore = product.status === 'active' ? 20 : 0

  return Math.min(100, titleScore + reviewScore + statusScore)
}

// Listing Quality Score = buyer-facing quality proxy: how good the listing
// looks to a shopper once they land on it.
//   - Star rating is the most direct buyer-quality signal available.
//   - Review volume again, since a well-optimized *listing* (not just
//     product) tends to accumulate more reviews over time.
//   - Active status, since an inactive listing is not a "quality" listing
//     for a shopper, whatever the score.
function listingQualityScoreFor(product: Product): number {
  const r = product.rating
  const ratingScore = r >= 4.7 ? 40 : r >= 4.3 ? 32 : r >= 4.0 ? 24 : r >= 3.5 ? 14 : 6

  const reviews = product.reviewCount
  const reviewScore = reviews >= 300 ? 30 : reviews >= 100 ? 22 : reviews >= 50 ? 14 : reviews >= 10 ? 6 : 0

  const statusScore = product.status === 'active' ? 30 : 0

  return Math.min(100, ratingScore + reviewScore + statusScore)
}

function listingStatusFor(product: Product): ListingStatus {
  return product.status === 'active' ? 'Live' : 'Inactive'
}

// Every product in the Phase 7.1 dataset belongs to the one seller in
// seller.ts, who sells on a single platform and under one storefront name
// — so Marketplace and Brand are derived from seller.ts, not per-product
// guesses. Same reasoning ordersView.ts already applies to `marketplace`.
const MARKETPLACE_LABEL: Record<typeof seller.platform, string> = {
  amazon: 'Amazon',
  flipkart: 'Flipkart',
  meesho: 'Meesho',
}

// Deterministic placeholder image per SKU — no real product photography
// exists in the mock dataset, and the brief explicitly allows placeholder
// URLs. Same URL every time for a given SKU (not random per render).
function placeholderImageFor(sku: string): string {
  return `https://placehold.co/400x400/e8e8e8/71717a?text=${encodeURIComponent(sku)}`
}

// ----------------------------------------------------------------------------
// Row shape shared by every Listings-related screen
// ----------------------------------------------------------------------------

export interface ListingViewRow {
  productId: string
  sku: string // SKU
  name: string // Product Name
  category: Product['category'] // Category
  marketplace: string // Marketplace
  brand: string // Brand
  price: number // Price
  rating: number // Rating
  reviewCount: number
  listingStatus: ListingStatus // Listing Status
  seoScore: number // SEO Score (0-100)
  seoTier: ScoreTier
  listingQualityScore: number // Listing Quality Score (0-100)
  listingQualityTier: ScoreTier
  imageUrl: string // Images (placeholder)
}

function toViewRow(product: Product): ListingViewRow {
  const seoScore = seoScoreFor(product)
  const listingQualityScore = listingQualityScoreFor(product)
  return {
    productId: product.id,
    sku: product.sku,
    name: product.name,
    category: product.category,
    marketplace: MARKETPLACE_LABEL[seller.platform],
    brand: seller.businessName,
    price: product.price,
    rating: product.rating,
    reviewCount: product.reviewCount,
    listingStatus: listingStatusFor(product),
    seoScore,
    seoTier: tierForScore(seoScore),
    listingQualityScore,
    listingQualityTier: tierForScore(listingQualityScore),
    imageUrl: placeholderImageFor(product.sku),
  }
}

// Computed once at import time, same pattern as ordersView.ts /
// inventoryView.ts / analytics.ts — cheap (50 rows) and keeps every
// consumer working off one identical array instance.
export const mockListingRows: ListingViewRow[] = products.map(toViewRow)

export function getMockListingRowBySku(sku: string): ListingViewRow | undefined {
  return mockListingRows.find(row => row.sku === sku)
}

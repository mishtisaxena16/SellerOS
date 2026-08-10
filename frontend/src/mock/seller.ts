// ============================================================================
// SellerOS — Phase 7.1: Mock Seller Dataset
// ============================================================================
// Demo data only. No network calls, no marketplace APIs, no backend/connector
// changes. One realistic seller, referenced consistently across
// products.ts / orders.ts / inventory.ts / analytics.ts in this folder.
//
// All figures in analytics.ts are DERIVED from orders.ts/products.ts/
// inventory.ts at import time (sums, counts, averages) rather than hand-typed
// separately, so revenue/inventory/growth numbers can never drift out of
// sync with the underlying products/orders here.
// ============================================================================

export type MarketplacePlatform = 'amazon' | 'flipkart' | 'meesho'
export type FulfillmentType = 'FBA' | 'FBM'
export type SellerTier = 'Standard' | 'Silver' | 'Gold' | 'Platinum'

export interface SellerCategoryBreakdown {
  category: string
  productCount: number
}

export interface Seller {
  id: string
  businessName: string
  legalName: string
  platform: MarketplacePlatform
  sellerId: string
  storeFrontUrl: string
  fulfillmentType: FulfillmentType
  tier: SellerTier
  joinedDate: string // ISO date
  headquarters: {
    city: string
    state: string
    country: string
  }
  primaryCategories: string[]
  categoryBreakdown: SellerCategoryBreakdown[]
  rating: {
    average: number // 0-5, one decimal
    totalReviews: number
  }
  accountHealth: {
    orderDefectRate: number // percent
    lateShipmentRate: number // percent
    validTrackingRate: number // percent
    status: 'Healthy' | 'At Risk' | 'Suspended'
  }
}

// Category breakdown mirrors products.ts exactly (9/9/8/8/8/8 = 50 products).
export const seller: Seller = {
  id: 'seller_abc_fashion',
  businessName: 'ABC Fashion Store',
  legalName: 'ABC Fashion Retail LLC',
  platform: 'amazon',
  sellerId: 'A2B3C4D5E6F7G8',
  storeFrontUrl: 'https://www.amazon.com/shops/abcfashionstore',
  fulfillmentType: 'FBA',
  tier: 'Gold',
  joinedDate: '2022-03-14',
  headquarters: {
    city: 'Charlotte',
    state: 'North Carolina',
    country: 'United States',
  },
  primaryCategories: [
    "Women's Apparel",
    "Men's Apparel",
    'Footwear',
    'Accessories',
    'Activewear',
    'Outerwear',
  ],
  categoryBreakdown: [
    { category: "Women's Apparel", productCount: 9 },
    { category: "Men's Apparel", productCount: 9 },
    { category: 'Footwear', productCount: 8 },
    { category: 'Accessories', productCount: 8 },
    { category: 'Activewear', productCount: 8 },
    { category: 'Outerwear', productCount: 8 },
  ],
  rating: {
    average: 4.6,
    totalReviews: 8734,
  },
  accountHealth: {
    orderDefectRate: 0.4,
    lateShipmentRate: 1.1,
    validTrackingRate: 98.7,
    status: 'Healthy',
  },
}

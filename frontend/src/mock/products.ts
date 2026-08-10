// ============================================================================
// SellerOS — Phase 7.1: Mock Products Dataset
// ============================================================================
// 50 products for ABC Fashion Store (Amazon), across 6 categories. Prices,
// costs, ratings, and stock reference numbers here are the single source of
// truth that orders.ts / inventory.ts / analytics.ts build on — change a
// price here and revenue in analytics.ts recalculates automatically since
// analytics derives from orders, which derive their unit price from here.
// ============================================================================

export type ProductCategory =
  | "Women's Apparel"
  | "Men's Apparel"
  | 'Footwear'
  | 'Accessories'
  | 'Activewear'
  | 'Outerwear'

export type ProductStatus = 'active' | 'inactive'

export interface Product {
  id: string
  sku: string
  name: string
  category: ProductCategory
  price: number // customer-facing selling price, USD
  cost: number // seller's unit cost, USD
  rating: number // 0-5, one decimal
  reviewCount: number
  status: ProductStatus
  createdAt: string // ISO date, first listed
}

export const products: Product[] = [
  // ---- Women's Apparel (9) ----
  { id: 'p001', sku: 'ABC-WA-001', name: 'Floral Wrap Midi Dress', category: "Women's Apparel", price: 44.99, cost: 19.5, rating: 4.7, reviewCount: 412, status: 'active', createdAt: '2022-04-02' },
  { id: 'p002', sku: 'ABC-WA-002', name: 'Ribbed Knit Turtleneck Sweater', category: "Women's Apparel", price: 38.99, cost: 16.75, rating: 4.5, reviewCount: 289, status: 'active', createdAt: '2022-05-18' },
  { id: 'p003', sku: 'ABC-WA-003', name: 'High-Waisted Wide-Leg Trousers', category: "Women's Apparel", price: 48.99, cost: 21.0, rating: 4.4, reviewCount: 176, status: 'active', createdAt: '2022-07-09' },
  { id: 'p004', sku: 'ABC-WA-004', name: 'Pleated A-Line Skirt', category: "Women's Apparel", price: 34.99, cost: 14.25, rating: 4.3, reviewCount: 98, status: 'active', createdAt: '2022-09-21' },
  { id: 'p005', sku: 'ABC-WA-005', name: 'Silk Blend Button-Down Blouse', category: "Women's Apparel", price: 42.99, cost: 18.9, rating: 4.6, reviewCount: 331, status: 'active', createdAt: '2022-11-03' },
  { id: 'p006', sku: 'ABC-WA-006', name: 'Cropped Cotton Cardigan', category: "Women's Apparel", price: 36.99, cost: 15.4, rating: 4.2, reviewCount: 64, status: 'active', createdAt: '2023-01-14' },
  { id: 'p007', sku: 'ABC-WA-007', name: 'Linen Blend Jumpsuit', category: "Women's Apparel", price: 54.99, cost: 24.75, rating: 4.8, reviewCount: 447, status: 'active', createdAt: '2023-03-22' },
  { id: 'p008', sku: 'ABC-WA-008', name: 'Off-Shoulder Ruffle Top', category: "Women's Apparel", price: 29.99, cost: 12.6, rating: 3.9, reviewCount: 41, status: 'inactive', createdAt: '2022-06-11' },
  { id: 'p009', sku: 'ABC-WA-009', name: 'Tailored Blazer Dress', category: "Women's Apparel", price: 59.99, cost: 27.5, rating: 4.7, reviewCount: 203, status: 'active', createdAt: '2023-08-05' },

  // ---- Men's Apparel (9) ----
  { id: 'p010', sku: 'ABC-MA-001', name: 'Slim-Fit Oxford Dress Shirt', category: "Men's Apparel", price: 39.99, cost: 17.0, rating: 4.6, reviewCount: 356, status: 'active', createdAt: '2022-04-15' },
  { id: 'p011', sku: 'ABC-MA-002', name: 'Classic Straight-Leg Chinos', category: "Men's Apparel", price: 44.99, cost: 19.25, rating: 4.5, reviewCount: 298, status: 'active', createdAt: '2022-06-02' },
  { id: 'p012', sku: 'ABC-MA-003', name: 'Heavyweight Cotton Henley', category: "Men's Apparel", price: 27.99, cost: 11.75, rating: 4.4, reviewCount: 187, status: 'active', createdAt: '2022-08-19' },
  { id: 'p013', sku: 'ABC-MA-004', name: 'Plaid Flannel Button-Up', category: "Men's Apparel", price: 34.99, cost: 15.1, rating: 4.3, reviewCount: 122, status: 'active', createdAt: '2022-10-27' },
  { id: 'p014', sku: 'ABC-MA-005', name: 'Textured Crewneck Sweater', category: "Men's Apparel", price: 41.99, cost: 18.4, rating: 4.5, reviewCount: 265, status: 'active', createdAt: '2023-01-08' },
  { id: 'p015', sku: 'ABC-MA-006', name: 'Relaxed-Fit Cargo Pants', category: "Men's Apparel", price: 46.99, cost: 20.5, rating: 4.1, reviewCount: 88, status: 'active', createdAt: '2023-02-25' },
  { id: 'p016', sku: 'ABC-MA-007', name: 'Merino Wool Polo', category: "Men's Apparel", price: 49.99, cost: 22.75, rating: 4.7, reviewCount: 374, status: 'active', createdAt: '2023-05-13' },
  { id: 'p017', sku: 'ABC-MA-008', name: 'Vintage Wash Denim Jeans', category: "Men's Apparel", price: 52.99, cost: 24.0, rating: 4.8, reviewCount: 501, status: 'active', createdAt: '2022-09-30' },
  { id: 'p018', sku: 'ABC-MA-009', name: 'Linen Short-Sleeve Shirt', category: "Men's Apparel", price: 32.99, cost: 13.9, rating: 3.8, reviewCount: 37, status: 'inactive', createdAt: '2022-07-04' },

  // ---- Footwear (8) ----
  { id: 'p019', sku: 'ABC-FW-001', name: 'Leather Ankle Chelsea Boots', category: 'Footwear', price: 79.99, cost: 36.5, rating: 4.7, reviewCount: 412, status: 'active', createdAt: '2022-05-06' },
  { id: 'p020', sku: 'ABC-FW-002', name: 'Canvas Low-Top Sneakers', category: 'Footwear', price: 44.99, cost: 19.75, rating: 4.5, reviewCount: 328, status: 'active', createdAt: '2022-06-21' },
  { id: 'p021', sku: 'ABC-FW-003', name: 'Suede Espadrille Flats', category: 'Footwear', price: 39.99, cost: 17.25, rating: 4.2, reviewCount: 143, status: 'active', createdAt: '2022-08-30' },
  { id: 'p022', sku: 'ABC-FW-004', name: 'Platform Block Heel Sandals', category: 'Footwear', price: 54.99, cost: 24.9, rating: 4.4, reviewCount: 209, status: 'active', createdAt: '2023-03-02' },
  { id: 'p023', sku: 'ABC-FW-005', name: 'Knit Slip-On Sneakers', category: 'Footwear', price: 49.99, cost: 22.0, rating: 4.6, reviewCount: 361, status: 'active', createdAt: '2023-04-17' },
  { id: 'p024', sku: 'ABC-FW-006', name: 'Classic Penny Loafers', category: 'Footwear', price: 64.99, cost: 29.75, rating: 4.5, reviewCount: 176, status: 'active', createdAt: '2022-11-11' },
  { id: 'p025', sku: 'ABC-FW-007', name: 'Quilted Puffer Slides', category: 'Footwear', price: 29.99, cost: 12.5, rating: 4.0, reviewCount: 72, status: 'active', createdAt: '2023-09-19' },
  { id: 'p026', sku: 'ABC-FW-008', name: 'Strappy Block Heel Pumps', category: 'Footwear', price: 59.99, cost: 27.25, rating: 4.3, reviewCount: 154, status: 'active', createdAt: '2023-06-08' },

  // ---- Accessories (8) ----
  { id: 'p027', sku: 'ABC-AC-001', name: 'Woven Leather Belt', category: 'Accessories', price: 24.99, cost: 9.75, rating: 4.5, reviewCount: 267, status: 'active', createdAt: '2022-04-28' },
  { id: 'p028', sku: 'ABC-AC-002', name: 'Structured Crossbody Bag', category: 'Accessories', price: 44.99, cost: 19.5, rating: 4.7, reviewCount: 389, status: 'active', createdAt: '2022-07-15' },
  { id: 'p029', sku: 'ABC-AC-003', name: 'Cashmere Blend Scarf', category: 'Accessories', price: 34.99, cost: 15.25, rating: 4.6, reviewCount: 231, status: 'active', createdAt: '2022-10-02' },
  { id: 'p030', sku: 'ABC-AC-004', name: 'Polarized Aviator Sunglasses', category: 'Accessories', price: 29.99, cost: 11.9, rating: 4.4, reviewCount: 198, status: 'active', createdAt: '2023-02-11' },
  { id: 'p031', sku: 'ABC-AC-005', name: 'Beaded Statement Necklace', category: 'Accessories', price: 19.99, cost: 7.5, rating: 4.1, reviewCount: 84, status: 'active', createdAt: '2023-05-29' },
  { id: 'p032', sku: 'ABC-AC-006', name: 'Quilted Chain Wallet', category: 'Accessories', price: 27.99, cost: 11.25, rating: 3.9, reviewCount: 46, status: 'inactive', createdAt: '2022-08-08' },
  { id: 'p033', sku: 'ABC-AC-007', name: 'Wide-Brim Wool Fedora', category: 'Accessories', price: 32.99, cost: 14.0, rating: 4.3, reviewCount: 112, status: 'active', createdAt: '2023-10-14' },
  { id: 'p034', sku: 'ABC-AC-008', name: 'Leather Card Holder Wallet', category: 'Accessories', price: 14.99, cost: 5.75, rating: 4.6, reviewCount: 302, status: 'active', createdAt: '2022-12-19' },

  // ---- Activewear (8) ----
  { id: 'p035', sku: 'ABC-AW-001', name: 'High-Rise Compression Leggings', category: 'Activewear', price: 34.99, cost: 14.5, rating: 4.8, reviewCount: 521, status: 'active', createdAt: '2022-04-09' },
  { id: 'p036', sku: 'ABC-AW-002', name: 'Seamless Racerback Sports Bra', category: 'Activewear', price: 24.99, cost: 10.25, rating: 4.6, reviewCount: 388, status: 'active', createdAt: '2022-06-27' },
  { id: 'p037', sku: 'ABC-AW-003', name: 'Moisture-Wicking Performance Tee', category: 'Activewear', price: 22.99, cost: 9.4, rating: 4.4, reviewCount: 214, status: 'active', createdAt: '2022-09-13' },
  { id: 'p038', sku: 'ABC-AW-004', name: 'Lightweight Running Shorts', category: 'Activewear', price: 26.99, cost: 11.1, rating: 4.5, reviewCount: 267, status: 'active', createdAt: '2023-01-30' },
  { id: 'p039', sku: 'ABC-AW-005', name: 'Zip-Up Training Jacket', category: 'Activewear', price: 44.99, cost: 19.75, rating: 4.3, reviewCount: 156, status: 'active', createdAt: '2023-04-06' },
  { id: 'p040', sku: 'ABC-AW-006', name: 'Ribbed Yoga Bike Shorts', category: 'Activewear', price: 28.99, cost: 12.0, rating: 4.7, reviewCount: 342, status: 'active', createdAt: '2023-07-22' },
  { id: 'p041', sku: 'ABC-AW-007', name: 'Mesh-Panel Training Tank', category: 'Activewear', price: 21.99, cost: 8.9, rating: 4.0, reviewCount: 59, status: 'active', createdAt: '2023-11-01' },
  { id: 'p042', sku: 'ABC-AW-008', name: 'Fleece-Lined Jogger Pants', category: 'Activewear', price: 48.99, cost: 21.5, rating: 4.6, reviewCount: 278, status: 'active', createdAt: '2022-11-25' },

  // ---- Outerwear (8) ----
  { id: 'p043', sku: 'ABC-OW-001', name: 'Quilted Puffer Vest', category: 'Outerwear', price: 54.99, cost: 24.5, rating: 4.5, reviewCount: 231, status: 'active', createdAt: '2022-05-20' },
  { id: 'p044', sku: 'ABC-OW-002', name: 'Wool Blend Trench Coat', category: 'Outerwear', price: 89.99, cost: 41.25, rating: 4.7, reviewCount: 298, status: 'active', createdAt: '2022-09-04' },
  { id: 'p045', sku: 'ABC-OW-003', name: 'Faux Shearling Bomber Jacket', category: 'Outerwear', price: 69.99, cost: 32.0, rating: 4.6, reviewCount: 245, status: 'active', createdAt: '2022-12-08' },
  { id: 'p046', sku: 'ABC-OW-004', name: 'Water-Resistant Windbreaker', category: 'Outerwear', price: 49.99, cost: 21.75, rating: 4.3, reviewCount: 167, status: 'active', createdAt: '2023-03-16' },
  { id: 'p047', sku: 'ABC-OW-005', name: 'Double-Breasted Wool Coat', category: 'Outerwear', price: 84.99, cost: 39.5, rating: 4.8, reviewCount: 356, status: 'active', createdAt: '2023-09-27' },
  { id: 'p048', sku: 'ABC-OW-006', name: 'Packable Down Jacket', category: 'Outerwear', price: 74.99, cost: 34.25, rating: 4.6, reviewCount: 289, status: 'active', createdAt: '2023-10-30' },
  { id: 'p049', sku: 'ABC-OW-007', name: 'Sherpa-Lined Denim Jacket', category: 'Outerwear', price: 59.99, cost: 27.0, rating: 4.2, reviewCount: 103, status: 'active', createdAt: '2022-07-31' },
  { id: 'p050', sku: 'ABC-OW-008', name: 'Longline Rain Trench', category: 'Outerwear', price: 64.99, cost: 29.5, rating: 3.9, reviewCount: 52, status: 'inactive', createdAt: '2022-10-12' },
]

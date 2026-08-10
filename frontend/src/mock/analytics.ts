// ============================================================================
// SellerOS — Phase 7.1: Mock Analytics Dataset
// ============================================================================
// Nothing in this file is a hand-typed figure. Every value is derived from
// orders.ts / products.ts / inventory.ts at import time, so "analytics
// matches revenue" holds by construction: change a price in products.ts or
// add an order in orders.ts and every number below recalculates on its own.
// ============================================================================

import { products, Product } from './products'
import { orders, Order } from './orders'
import { inventory } from './inventory'

export interface MonthlyRevenue {
  month: string // 'YYYY-MM'
  grossRevenue: number
  refunds: number
  netRevenue: number
  orderCount: number
}

export interface CategoryPerformance {
  category: Product['category']
  netRevenue: number
  unitsSold: number
  productCount: number
}

export interface TopProduct {
  productId: string
  sku: string
  name: string
  category: Product['category']
  netRevenue: number
  unitsSold: number
  rating: number
}

export interface InventoryHealth {
  totalSkus: number
  totalUnitsAvailable: number
  lowStockCount: number
  outOfStockCount: number
  inStockCount: number
}

export interface RevenueSummary {
  grossRevenue: number
  refunds: number
  netRevenue: number
  totalOrdersPlaced: number
  completedOrders: number
  cancelledOrders: number
  returnedOrders: number
  averageOrderValue: number
}

export interface GrowthSummary {
  firstPeriodLabel: string
  secondPeriodLabel: string
  firstPeriodRevenue: number
  secondPeriodRevenue: number
  growthPercent: number
}

export interface RatingsSummary {
  averageProductRating: number
  totalReviews: number
  topRatedProduct: { name: string; rating: number; reviewCount: number }
  lowestRatedProduct: { name: string; rating: number; reviewCount: number }
}

function round2(n: number): number {
  return Math.round(n * 100) / 100
}

function isRevenueBearing(status: Order['status']): boolean {
  return status === 'Delivered' || status === 'Shipped' || status === 'Processing'
}

// ---- Revenue summary --------------------------------------------------

const completedOrders = orders.filter((o) => isRevenueBearing(o.status))
const cancelledOrdersList = orders.filter((o) => o.status === 'Cancelled')
const returnedOrdersList = orders.filter((o) => o.status === 'Returned')

const grossRevenue = round2(completedOrders.reduce((sum, o) => sum + o.total, 0))
const refunds = round2(returnedOrdersList.reduce((sum, o) => sum + o.total, 0))
const netRevenue = round2(grossRevenue - refunds)

export const revenueSummary: RevenueSummary = {
  grossRevenue,
  refunds,
  netRevenue,
  totalOrdersPlaced: orders.length,
  completedOrders: completedOrders.length,
  cancelledOrders: cancelledOrdersList.length,
  returnedOrders: returnedOrdersList.length,
  averageOrderValue: round2(netRevenue / (completedOrders.length || 1)),
}

// ---- Revenue by month ---------------------------------------------------

function monthKey(isoDate: string): string {
  return isoDate.slice(0, 7) // 'YYYY-MM'
}

const monthlyMap = new Map<string, { gross: number; refund: number; count: number }>()
for (const order of orders) {
  const key = monthKey(order.orderDate)
  const entry = monthlyMap.get(key) ?? { gross: 0, refund: 0, count: 0 }
  if (isRevenueBearing(order.status)) {
    entry.gross += order.total
    entry.count += 1
  } else if (order.status === 'Returned') {
    entry.refund += order.total
  }
  monthlyMap.set(key, entry)
}

export const revenueByMonth: MonthlyRevenue[] = Array.from(monthlyMap.entries())
  .sort(([a], [b]) => (a < b ? -1 : 1))
  .map(([month, v]) => ({
    month,
    grossRevenue: round2(v.gross),
    refunds: round2(v.refund),
    netRevenue: round2(v.gross - v.refund),
    orderCount: v.count,
  }))

// ---- Growth: first half of the order window vs. second half -------------

const midpoint = Math.floor(revenueByMonth.length / 2)
const firstHalf = revenueByMonth.slice(0, midpoint)
const secondHalf = revenueByMonth.slice(midpoint)
const firstPeriodRevenue = round2(firstHalf.reduce((sum, m) => sum + m.netRevenue, 0))
const secondPeriodRevenue = round2(secondHalf.reduce((sum, m) => sum + m.netRevenue, 0))

export const growthSummary: GrowthSummary = {
  firstPeriodLabel: firstHalf.length ? `${firstHalf[0].month} to ${firstHalf[firstHalf.length - 1].month}` : 'n/a',
  secondPeriodLabel: secondHalf.length ? `${secondHalf[0].month} to ${secondHalf[secondHalf.length - 1].month}` : 'n/a',
  firstPeriodRevenue,
  secondPeriodRevenue,
  growthPercent: firstPeriodRevenue > 0 ? round2(((secondPeriodRevenue - firstPeriodRevenue) / firstPeriodRevenue) * 100) : 0,
}

// ---- Category performance -------------------------------------------------

const categoryMap = new Map<Product['category'], { revenue: number; units: number }>()
for (const order of orders) {
  const sign = isRevenueBearing(order.status) ? 1 : order.status === 'Returned' ? -1 : 0
  if (sign === 0) continue
  for (const item of order.items) {
    const entry = categoryMap.get(item.category) ?? { revenue: 0, units: 0 }
    entry.revenue += sign * item.lineTotal
    entry.units += sign * item.quantity
    categoryMap.set(item.category, entry)
  }
}

export const categoryPerformance: CategoryPerformance[] = Array.from(categoryMap.entries())
  .map(([category, v]) => ({
    category,
    netRevenue: round2(v.revenue),
    unitsSold: v.units,
    productCount: products.filter((p) => p.category === category).length,
  }))
  .sort((a, b) => b.netRevenue - a.netRevenue)

// ---- Top products by net revenue ----------------------------------------

const productRevenueMap = new Map<string, { revenue: number; units: number }>()
for (const order of orders) {
  const sign = isRevenueBearing(order.status) ? 1 : order.status === 'Returned' ? -1 : 0
  if (sign === 0) continue
  for (const item of order.items) {
    const entry = productRevenueMap.get(item.productId) ?? { revenue: 0, units: 0 }
    entry.revenue += sign * item.lineTotal
    entry.units += sign * item.quantity
    productRevenueMap.set(item.productId, entry)
  }
}

export const topProducts: TopProduct[] = Array.from(productRevenueMap.entries())
  .map(([productId, v]) => {
    const product = products.find((p) => p.id === productId)!
    return {
      productId,
      sku: product.sku,
      name: product.name,
      category: product.category,
      netRevenue: round2(v.revenue),
      unitsSold: v.units,
      rating: product.rating,
    }
  })
  .sort((a, b) => b.netRevenue - a.netRevenue)
  .slice(0, 10)

// ---- Inventory health -----------------------------------------------------

export const inventoryHealth: InventoryHealth = {
  totalSkus: inventory.length,
  totalUnitsAvailable: inventory.reduce((sum, i) => sum + i.availableQuantity, 0),
  lowStockCount: inventory.filter((i) => i.status === 'Low Stock').length,
  outOfStockCount: inventory.filter((i) => i.status === 'Out of Stock').length,
  inStockCount: inventory.filter((i) => i.status === 'In Stock').length,
}

// ---- Ratings summary -------------------------------------------------------

const totalReviews = products.reduce((sum, p) => sum + p.reviewCount, 0)
const weightedRatingSum = products.reduce((sum, p) => sum + p.rating * p.reviewCount, 0)
const sortedByRating = [...products].sort((a, b) => b.rating - a.rating)
const topRated = sortedByRating[0]
const lowestRated = sortedByRating[sortedByRating.length - 1]

export const ratingsSummary: RatingsSummary = {
  averageProductRating: round2(weightedRatingSum / totalReviews),
  totalReviews,
  topRatedProduct: { name: topRated.name, rating: topRated.rating, reviewCount: topRated.reviewCount },
  lowestRatedProduct: { name: lowestRated.name, rating: lowestRated.rating, reviewCount: lowestRated.reviewCount },
}

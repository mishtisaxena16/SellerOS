import { apiRequest } from './client'
import type { Platform } from './marketplace'

// Mirrors backend.ai.models.models.OrderItem / Order exactly (GET /orders).
export interface OrderLineItem {
  sku: string
  quantity: number
  unit_price: number | null
}

export interface OrderRecord {
  platform: string
  order_id: string
  status: string
  items: OrderLineItem[]
  total_amount: number | null
  currency: string
  order_date: string | null
  customer_state: string | null
  raw: Record<string, unknown>
}

export interface OrdersResponse {
  platform: string
  success: boolean
  message?: string
  orders: OrderRecord[]
}

export function getOrders(platform?: Platform | 'all') {
  const query = platform && platform !== 'all' ? `?platform=${platform}` : ''
  return apiRequest<OrdersResponse>(`/orders${query}`)
}

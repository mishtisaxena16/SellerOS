import { apiRequest } from './client'
import type { Platform } from './marketplace'

// Mirrors backend.ai.models.models.Inventory exactly — do not rename fields,
// the backend returns these keys as-is (see GET /inventory).
export interface InventoryItem {
  platform: string
  sku: string
  available_quantity: number
  reserved_quantity: number
  warehouse: string | null
  raw: Record<string, unknown>
}

export interface InventoryResponse {
  platform: string
  success: boolean
  message?: string
  items: InventoryItem[]
}

export function getInventory(platform?: Platform | 'all') {
  const query = platform && platform !== 'all' ? `?platform=${platform}` : ''
  return apiRequest<InventoryResponse>(`/inventory${query}`)
}

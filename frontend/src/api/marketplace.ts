import { apiRequest } from './client'

export const SUPPORTED_PLATFORMS = ['amazon', 'flipkart', 'meesho'] as const
export type Platform = (typeof SUPPORTED_PLATFORMS)[number]

export interface MarketplaceAccount {
  id: number
  platform: string
  created_at: string
}

export function connectMarketplace(platform: Platform, credentials: Record<string, string>) {
  return apiRequest<MarketplaceAccount>('/marketplaces/connect', {
    method: 'POST',
    body: { platform, credentials },
  })
}

export function listMarketplaces() {
  return apiRequest<MarketplaceAccount[]>('/marketplaces')
}

export function disconnectMarketplace(id: number) {
  return apiRequest<void>(`/marketplaces/${id}`, { method: 'DELETE' })
}

export interface AmazonAuthorizeResponse {
  authorization_url: string
}

// Step 1 of the existing "Connect Amazon" OAuth flow (backend
// GET /marketplaces/amazon/authorize) — returns the Amazon consent URL
// the browser should be sent to. Step 2 (GET /marketplaces/amazon/callback)
// is Amazon redirecting the browser straight to the backend, not a
// frontend route, so there is no corresponding client function for it.
export function authorizeAmazon(region = 'eu') {
  return apiRequest<AmazonAuthorizeResponse>(
    `/marketplaces/amazon/authorize?region=${encodeURIComponent(region)}`
  )
}

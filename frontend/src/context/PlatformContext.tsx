import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import * as marketplaceApi from '../api/marketplace'
import { useAuth } from './AuthContext'

export type PlatformFilter = 'all' | marketplaceApi.Platform

export const PLATFORM_LABELS: Record<marketplaceApi.Platform, string> = {
  amazon: 'Amazon',
  flipkart: 'Flipkart',
  meesho: 'Meesho',
}

interface PlatformContextValue {
  connected: marketplaceApi.MarketplaceAccount[]
  connectedPlatforms: marketplaceApi.Platform[]
  loading: boolean
  selected: PlatformFilter
  setSelected: (p: PlatformFilter) => void
  refresh: () => Promise<void>
}

const PlatformContext = createContext<PlatformContextValue | undefined>(undefined)

const SELECTED_KEY = 'sellerOS.selectedPlatform'

export function PlatformProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const [connected, setConnected] = useState<marketplaceApi.MarketplaceAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelectedState] = useState<PlatformFilter>(
    () => (window.localStorage.getItem(SELECTED_KEY) as PlatformFilter | null) || 'all'
  )

  const refresh = async () => {
    if (!isAuthenticated) {
      setConnected([])
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const accounts = await marketplaceApi.listMarketplaces()
      setConnected(accounts)
    } catch {
      // Non-fatal — dashboard pages fall back to their own mock data
      // if this list can't be fetched (e.g. backend isn't running yet).
      setConnected([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated])

  const setSelected = (p: PlatformFilter) => {
    setSelectedState(p)
    window.localStorage.setItem(SELECTED_KEY, p)
  }

  const connectedPlatforms = connected.map(c => c.platform) as marketplaceApi.Platform[]

  return (
    <PlatformContext.Provider
      value={{ connected, connectedPlatforms, loading, selected, setSelected, refresh }}
    >
      {children}
    </PlatformContext.Provider>
  )
}

export function usePlatform() {
  const ctx = useContext(PlatformContext)
  if (!ctx) throw new Error('usePlatform must be used within a PlatformProvider')
  return ctx
}

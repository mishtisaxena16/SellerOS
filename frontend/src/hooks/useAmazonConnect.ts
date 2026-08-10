import { useCallback, useEffect, useRef, useState } from 'react'
import { authorizeAmazon, listMarketplaces } from '../api/marketplace'
import { usePlatform } from '../context/PlatformContext'
import { ApiError } from '../api/client'

// The existing backend's OAuth redirect URI (AMAZON_OAUTH_REDIRECT_URI)
// points at the backend's own GET /marketplaces/amazon/callback route,
// not a page in this frontend app — so once the seller lands there, this
// tab never receives a navigation/route event to react to. Instead we
// open the consent page in a popup and poll the existing GET /marketplaces
// endpoint until Amazon shows up as connected (or the seller closes the
// popup without finishing).
const POPUP_FEATURES = 'width=520,height=680,menubar=no,toolbar=no,status=no,noopener'
const POLL_INTERVAL_MS = 1500
const POLL_TIMEOUT_MS = 5 * 60 * 1000 // matches the backend's own OAuth state TTL (10 min) with headroom

export function useAmazonConnect() {
  const { refresh } = usePlatform()
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollHandleRef = useRef<number | null>(null)

  // Guards re-entrancy synchronously. `connecting` (React state) is what
  // the UI disables its button on, but state updates aren't applied
  // until the next render — a second connectAmazon() call fired before
  // that render commits would otherwise slip through and open a second
  // popup/poll loop. This ref is set/read synchronously so a duplicate
  // call is rejected immediately regardless of render timing.
  const inFlightRef = useRef(false)

  // The poll interval fires on a fixed cadence and doesn't wait for a
  // tick's async work (the listMarketplaces() call) to finish before the
  // next one fires. Without this guard, a slow response could overlap
  // with the next tick and let two checks resolve out of order.
  const tickInFlightRef = useRef(false)

  const stopPolling = useCallback(() => {
    if (pollHandleRef.current !== null) {
      window.clearInterval(pollHandleRef.current)
      pollHandleRef.current = null
    }
  }, [])

  // Don't leave a popup or a poll loop running if the component unmounts
  // mid-flow (e.g. the seller navigates away from Onboarding).
  useEffect(() => stopPolling, [stopPolling])

  const connectAmazon = useCallback(
    async (): Promise<boolean> => {
      // A connection attempt is already in progress — ignore this call
      // instead of starting a second popup/poll loop for the same flow.
      if (inFlightRef.current) return false
      inFlightRef.current = true

      setError(null)
      setConnecting(true)

      let authorizationUrl: string
      try {
        const res = await authorizeAmazon()
        authorizationUrl = res.authorization_url
      } catch (err) {
        inFlightRef.current = false
        setConnecting(false)
        setError(err instanceof ApiError ? err.message : 'Could not start the Amazon connection. Please try again.')
        return false
      }

      const popup = window.open(authorizationUrl, 'sellerOS-amazon-connect', POPUP_FEATURES)

      if (!popup) {
        // Popup blocked by the browser — nothing was opened, so there's
        // nothing to poll. Surface this as a clear, actionable error
        // rather than a silent no-op.
        inFlightRef.current = false
        setConnecting(false)
        setError('Could not open the Amazon sign-in window. Please allow pop-ups for this site and try again.')
        return false
      }

      return new Promise<boolean>(resolve => {
        const startedAt = Date.now()
        let settled = false

        const finish = async (success: boolean, failureMessage?: string) => {
          if (settled) return
          settled = true
          stopPolling()
          if (!popup.closed) popup.close()
          // Always resync with the backend's own record of what's
          // connected, whether this attempt succeeded or failed, so the
          // UI never drifts from what's actually persisted.
          await refresh()
          setConnecting(false)
          inFlightRef.current = false
          if (!success && failureMessage) setError(failureMessage)
          resolve(success)
        }

        pollHandleRef.current = window.setInterval(async () => {
          if (tickInFlightRef.current) return
          tickInFlightRef.current = true
          try {
            const popupClosedBeforeCheck = popup.closed
            const timedOut = Date.now() - startedAt >= POLL_TIMEOUT_MS

            let isConnected = false
            try {
              const accounts = await listMarketplaces()
              isConnected = accounts.some(a => a.platform === 'amazon')
            } catch {
              // Transient network hiccup — keep polling unless the popup
              // has already closed or we've timed out (handled below).
            }

            if (isConnected) {
              await finish(true)
              return
            }
            if (popupClosedBeforeCheck) {
              await finish(
                false,
                'Amazon connection was not completed — the sign-in window was closed before authorization finished.'
              )
              return
            }
            if (timedOut) {
              await finish(false, 'Amazon connection timed out. Please try again.')
              return
            }
          } finally {
            tickInFlightRef.current = false
          }
        }, POLL_INTERVAL_MS)
      })
    },
    [refresh, stopPolling]
  )

  return { connectAmazon, connecting, error }
}

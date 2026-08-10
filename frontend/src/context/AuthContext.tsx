import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import * as authApi from '../api/auth'
import { getToken, setToken } from '../api/client'

export type UserType = 'new' | 'existing' | null

interface AuthContextValue {
  user: authApi.CurrentUser | null
  loading: boolean
  error: string | null
  isAuthenticated: boolean
  userType: UserType
  setUserType: (t: UserType) => void
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, businessName: string) => Promise<void>
  updateProfile: (businessName: string) => Promise<void>
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>
  logout: () => void
  clearError: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

// There's no user_type field on the backend yet, so this is stored client-side,
// keyed by user_id (not just a flat browser-wide flag) so it doesn't bleed across
// accounts on a shared browser. This describes the user's identity ("I already
// sell online" vs "I'm just starting") — it's intentionally separate from
// connectedPlatforms, which describes current integration status. A seller can
// answer "existing" and still have zero connected marketplaces (e.g. they
// disconnected everything temporarily), so connection count alone isn't a
// reliable stand-in for this. Worth promoting to a real backend field
// (nullable column on the user profile) if this distinction needs to survive
// a device change or be used server-side.
const userTypeKey = (userId: number) => `sellerOS.userType.${userId}`

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<authApi.CurrentUser | null>(null)
  // Starts true — we don't know if the stored token is still valid until we've checked.
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [userType, setUserTypeState] = useState<UserType>(null)

  const loadCurrentUser = async () => {
    if (!getToken()) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const me = await authApi.getMe()
      setUser(me)
      const stored = window.localStorage.getItem(userTypeKey(me.user_id))
      setUserTypeState(stored === 'new' || stored === 'existing' ? stored : null)
    } catch {
      setToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const setUserType = (t: UserType) => {
    setUserTypeState(t)
    if (!user) return
    if (t) window.localStorage.setItem(userTypeKey(user.user_id), t)
    else window.localStorage.removeItem(userTypeKey(user.user_id))
  }

  useEffect(() => {
    loadCurrentUser()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // If any API call comes back 401 mid-session (expired/invalid token), drop the
  // in-memory user immediately so protected routes redirect to /login instead of
  // continuing to render a page whose data can no longer load.
  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null)
      setUserTypeState(null)
    }
    window.addEventListener('sellerOS:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('sellerOS:unauthorized', handleUnauthorized)
  }, [])

  const login = async (email: string, password: string) => {
    setError(null)
    try {
      const { access_token } = await authApi.login(email, password)
      setToken(access_token)
      const me = await authApi.getMe()
      setUser(me)
      const stored = window.localStorage.getItem(userTypeKey(me.user_id))
      setUserTypeState(stored === 'new' || stored === 'existing' ? stored : null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not log in')
      throw err
    }
  }

  const register = async (email: string, password: string, businessName: string) => {
    setError(null)
    try {
      const { access_token } = await authApi.register(email, password, businessName)
      setToken(access_token)
      const me = await authApi.getMe()
      setUser(me)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create your account')
      throw err
    }
  }

  const updateProfile = async (businessName: string) => {
    setError(null)
    try {
      const updated = await authApi.updateProfile(businessName)
      setUser(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update your profile')
      throw err
    }
  }

  const changePassword = async (currentPassword: string, newPassword: string) => {
    setError(null)
    try {
      await authApi.changePassword(currentPassword, newPassword)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not change your password')
      throw err
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    setUserTypeState(null)
  }

  const clearError = () => setError(null)

  return (
    <AuthContext.Provider
      value={{ user, loading, error, isAuthenticated: !!user, userType, setUserType, login, register, updateProfile, changePassword, logout, clearError }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}

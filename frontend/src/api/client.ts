// Thin fetch wrapper for the SellerOS FastAPI backend.
// Base URL comes from VITE_API_URL (see .env / .env.example) so the same
// build can point at localhost in dev and the real API in prod.

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const TOKEN_KEY = 'sellerOS.token'

export function getToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null) {
  if (token) window.localStorage.setItem(TOKEN_KEY, token)
  else window.localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  body?: unknown
  auth?: boolean // defaults to true — set false for /auth/register and /auth/login
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, auth = true } = options

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (auth) {
    const token = getToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError('Could not reach the SellerOS API. Is the backend running?', 0)
  }

  if (res.status === 401) {
    // Token missing/expired — clear it and notify listeners (e.g. AuthContext)
    // so any in-memory user state is dropped too, not just the stored token.
    setToken(null)
    window.dispatchEvent(new CustomEvent('sellerOS:unauthorized'))
  }

  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      detail = data.detail ?? detail
    } catch {
      // response wasn't JSON — keep the status text
    }
    throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), res.status)
  }

  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

import { apiRequest } from './client'

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface CurrentUser {
  user_id: number
  seller_id: number
  email: string
  business_name: string
}

export function register(email: string, password: string, business_name: string) {
  return apiRequest<TokenResponse>('/auth/register', {
    method: 'POST',
    auth: false,
    body: { email, password, business_name },
  })
}

export function login(email: string, password: string) {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    auth: false,
    body: { email, password },
  })
}

export function getMe() {
  return apiRequest<CurrentUser>('/auth/me')
}

export function updateProfile(business_name: string) {
  return apiRequest<CurrentUser>('/auth/me', {
    method: 'PATCH',
    body: { business_name },
  })
}

export function changePassword(current_password: string, new_password: string) {
  return apiRequest<void>('/auth/change-password', {
    method: 'POST',
    body: { current_password, new_password },
  })
}

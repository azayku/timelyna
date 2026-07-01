import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient, ApiError } from './apiClient'
import { tokenStore } from './tokenStore'

export interface AuthUser {
  employee_id: number
  email: string
  role: 'employee' | 'manager' | 'admin' | 'finance' | 'payroll'
  org_id: number
  first_name?: string
  last_name?: string
}

interface TokenResponse {
  access_token: string
  token_type: string
}

interface JwtPayload {
  employee_id: number
  sub: string
  role: 'employee' | 'manager' | 'admin' | 'finance' | 'payroll'
  org_id?: number
  must_change_password?: boolean
  first_name?: string
  last_name?: string
}

interface AuthState {
  user: AuthUser | null
  isAuthenticated: boolean
  login: (identifier: string, password: string) => Promise<void>
  logout: () => Promise<void>
  setUser: (user: AuthUser) => void
  clearUser: () => void
}

function decodeJwtPayload(token: string): JwtPayload {
  const base64Url = token.split('.')[1]
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
  const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=')
  return JSON.parse(atob(padded)) as JwtPayload
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,

      login: async (identifier: string, password: string) => {
        const data = await apiClient.post<TokenResponse>('/auth/login', { identifier, password })
        const payload = decodeJwtPayload(data.access_token)
        const user: AuthUser = {
          employee_id: payload.employee_id,
          email: payload.sub,
          role: payload.role,
          org_id: payload.org_id ?? 1,
          first_name: payload.first_name,
          last_name: payload.last_name,
        }
        tokenStore.set(data.access_token)
        set({ isAuthenticated: true, user })
      },

      logout: async () => {
        try {
          await apiClient.post<void>('/auth/logout', {})
        } catch (err) {
          if (!(err instanceof ApiError)) throw err
        }
        tokenStore.set(null)
        set({ user: null, isAuthenticated: false })
        window.location.href = '/login'
      },

      setUser: (user: AuthUser) => set({ user, isAuthenticated: true }),

      clearUser: () => {
        tokenStore.set(null)
        set({ user: null, isAuthenticated: false })
      },
    }),
    {
      name: 'auth-store',
      partialize: (s) => ({ user: s.user, isAuthenticated: s.isAuthenticated }),
      onRehydrateStorage: () => (state) => {
        // On reload, check if we have a valid token in tokenStore (localStorage).
        // If we have both state.isAuthenticated and a token, we're good.
        // If we have state.isAuthenticated but no token, try to refresh via httpOnly cookie.
        // If refresh fails, force logout.
        const existingToken = tokenStore.get()
        
        if (state?.isAuthenticated) {
          if (existingToken) {
            // Token exists, we're authenticated
            return
          }
          
          // No token but state says authenticated — try refresh
          apiClient.post<TokenResponse>('/auth/refresh', {})
            .then((data) => {
              tokenStore.set(data.access_token)
            })
            .catch(() => {
              // Refresh failed, clear auth state
              useAuthStore.getState().clearUser()
            })
        }
      },
    }
  )
)

// Écoute l'événement émis par apiClient sur toute réponse 401
// afin de découpler la navigation de la couche HTTP.
if (typeof window !== 'undefined') {
  window.addEventListener('auth:unauthorized', () => {
    useAuthStore.getState().clearUser()
    window.location.href = '/login'
  })
}

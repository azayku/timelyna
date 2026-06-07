/**
 * Singleton token store — no imports, breaks the circular dependency
 * between apiClient (needs the token) and authStore (imports apiClient).
 *
 * authStore writes here on login/logout/rehydration.
 * apiClient reads here to inject Authorization: Bearer.
 * 
 * Token is persisted in localStorage for page refresh persistence.
 */

const TOKEN_KEY = 'access_token'

let _token: string | null = null

// Initialize from localStorage on module load
try {
  _token = localStorage.getItem(TOKEN_KEY)
} catch {
  // localStorage might not be available (SSR, private mode, etc.)
}

export const tokenStore = {
  get: () => _token,
  set: (t: string | null) => {
    _token = t
    try {
      if (t) {
        localStorage.setItem(TOKEN_KEY, t)
      } else {
        localStorage.removeItem(TOKEN_KEY)
      }
    } catch {
      // Ignore localStorage errors
    }
  },
}

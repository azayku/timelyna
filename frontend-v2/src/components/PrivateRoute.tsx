import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../lib/authStore'
import { tokenStore } from '../lib/tokenStore'

function hasValidAccessToken(): boolean {
  const token = tokenStore.get()
  if (!token) return false

  try {
    const payloadPart = token.split('.')[1]
    if (!payloadPart) return false

    const base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=')
    const payload = JSON.parse(atob(padded)) as { exp?: number }

    // If no exp exists, consider token valid and rely on backend checks.
    if (typeof payload.exp !== 'number') return true

    const nowInSeconds = Math.floor(Date.now() / 1000)
    return payload.exp > nowInSeconds
  } catch {
    return false
  }
}

/**
 * Protects all child routes.
 * Unauthenticated users are redirected to /login with the current location
 * stored in state so LoginPage can redirect back after successful login.
 *
 * Usage (react-router-dom v6/v7 layout route pattern):
 *
 *   <Route element={<PrivateRoute />}>
 *     <Route path="/" element={<DashboardPage />} />
 *     ...
 *   </Route>
 */
export default function PrivateRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const hasUser = useAuthStore((s) => Boolean(s.user))
  const location = useLocation()
  const hasValidToken = hasValidAccessToken()

  if (!isAuthenticated || !hasUser || !hasValidToken) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Outlet />
}

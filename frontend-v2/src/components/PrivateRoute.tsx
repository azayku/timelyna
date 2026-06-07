import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../lib/authStore'

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
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Outlet />
}

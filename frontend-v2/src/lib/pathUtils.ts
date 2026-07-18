/**
 * Path utilities for handling base path in multi-environment deployments.
 * 
 * When deployed at /dev, /uat, /uat2, etc., React Router's basename removes
 * the prefix from all pathname operations. This utility helps normalize paths.
 */

/**
 * Get the current base path from environment or Vite config.
 * Returns '/' for production or local dev, '/dev', '/uat', '/uat2', etc. for deployments.
 */
export function getBasePath(): string {
  // At build time, VITE_BASE_PATH is set by docker-compose build args
  // Vite replaces import.meta.env.VITE_BASE_PATH with the actual value
  const basePath = import.meta.env.VITE_BASE_PATH || '/'
  // Ensure it starts with / and doesn't end with /
  const normalized = basePath.startsWith('/') ? basePath : '/' + basePath
  return normalized.endsWith('/') && normalized !== '/' ? normalized.slice(0, -1) : normalized
}

/**
 * Strip the base path prefix from a pathname.
 * 
 * Example:
 *   stripBasePath('/dev/dashboard', '/dev') → '/dashboard'
 *   stripBasePath('/dashboard', '/dev') → '/dashboard' (no prefix, returned as-is)
 *   stripBasePath('/dashboard', '/') → '/dashboard' (root, returned as-is)
 */
export function stripBasePath(pathname: string, basePath: string): string {
  if (basePath === '/' || !basePath) {
    return pathname
  }
  if (pathname.startsWith(basePath + '/')) {
    return pathname.slice(basePath.length)
  }
  if (pathname === basePath) {
    return '/'
  }
  return pathname
}

/**
 * Add the base path prefix to a pathname.
 * Used when manually navigating or constructing URLs that will be seen by the browser.
 * 
 * Example:
 *   addBasePath('/dashboard', '/dev') → '/dev/dashboard'
 *   addBasePath('/dashboard', '/') → '/dashboard'
 */
export function addBasePath(pathname: string, basePath: string): string {
  if (basePath === '/' || !basePath) {
    return pathname
  }
  // Ensure pathname starts with /
  const normalizedPath = pathname.startsWith('/') ? pathname : '/' + pathname
  // Avoid double slashes
  return basePath + normalizedPath
}

/**
 * Normalize a location pathname by stripping the base path.
 * Use this when storing or processing location.pathname from react-router.
 * 
 * This is useful in PrivateRoute when saving the "from" location:
 *   const from = stripBasePath(location.pathname, getBasePath())
 */
export function normalizePathname(pathname: string): string {
  return stripBasePath(pathname, getBasePath())
}

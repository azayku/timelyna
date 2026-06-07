/**
 * Lightweight API client for TimesheetPro.
 * Reads the base URL from VITE_API_URL (defaults to /api/v1).
 * JWT access_token is injected via Authorization: Bearer on every request.
 * tokenStore breaks the circular dep: authStore→apiClient→authStore.
 *
 * 401 interceptor: any 401 response triggers automatic logout via authStore.
 */
import { tokenStore } from './tokenStore'

const BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const token = tokenStore.get()
  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, {
    method,
    credentials: 'include',
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    let code = 'unknown_error'
    let detail = res.statusText
    try {
      const json = await res.json()
      code = json.code ?? code
      detail = json.detail ?? detail
    } catch {
      // ignore parse errors
    }

    const error = new ApiError(res.status, code, detail)

    // 401 interceptor — trigger logout except when calling /auth/logout itself
    // (to avoid an infinite loop).
    if (res.status === 401 && !path.includes('/auth/logout')) {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }

    throw error
  }

  // 204 No Content
  if (res.status === 204) return undefined as T

  return res.json() as Promise<T>
}

export const apiClient = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body: unknown) => request<T>('POST', path, body),
  put: <T>(path: string, body: unknown) => request<T>('PUT', path, body),
  delete: <T = void>(path: string) => request<T>('DELETE', path),
}

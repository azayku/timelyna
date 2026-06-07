import { tokenStore } from '../../lib/tokenStore'

const BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

export interface ImportResult {
  success: number
  skipped: number
  errors: string[]
  message: string
}

async function uploadCSV(endpoint: string, file: File): Promise<ImportResult> {
  const token = tokenStore.get()
  const formData = new FormData()
  formData.append('file', file)

  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const response = await fetch(`${BASE}${endpoint}`, {
    method: 'POST',
    credentials: 'include',
    headers,
    body: formData,
  })

  if (!response.ok) {
    const json = await response.json().catch(() => ({}))
    throw new Error(json.detail || 'Erreur lors de l\'import')
  }

  return response.json()
}

export async function importUsersCSV(file: File): Promise<ImportResult> {
  return uploadCSV('/admin/import/users', file)
}

export async function importProjectsCSV(file: File): Promise<ImportResult> {
  return uploadCSV('/admin/import/projects', file)
}

export function downloadUsersTemplate(): void {
  window.open(`${BASE}/admin/import/users/template`, '_blank')
}

export function downloadProjectsTemplate(): void {
  window.open(`${BASE}/admin/import/projects/template`, '_blank')
}

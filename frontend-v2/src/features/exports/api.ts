import { tokenStore } from '../../lib/tokenStore'

const BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

export async function downloadTimesheetPdf(startDate: string, endDate: string, projectIds?: number[]): Promise<void> {
  const token = tokenStore.get()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const url = new URL(`${BASE}/exports/timesheet/pdf`, window.location.origin)
  url.searchParams.set('start_date', startDate)
  url.searchParams.set('end_date', endDate)
  if (projectIds && projectIds.length > 0) {
    projectIds.forEach(id => url.searchParams.append('project_id', String(id)))
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    credentials: 'include',
    headers,
  })

  if (!response.ok) {
    throw new Error('Erreur lors du téléchargement du PDF')
  }

  const blob = await response.blob()
  const downloadUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = `timesheet_${startDate}_${endDate}.pdf`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(downloadUrl)
}

export async function downloadHoursReportPdf(startDate: string, endDate: string, projectIds?: number[]): Promise<void> {
  const token = tokenStore.get()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const url = new URL(`${BASE}/exports/hours-report/pdf`, window.location.origin)
  url.searchParams.set('start_date', startDate)
  url.searchParams.set('end_date', endDate)
  if (projectIds && projectIds.length > 0) {
    projectIds.forEach(id => url.searchParams.append('project_id', String(id)))
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    credentials: 'include',
    headers,
  })

  if (!response.ok) {
    throw new Error('Erreur lors du téléchargement du PDF')
  }

  const blob = await response.blob()
  const downloadUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = `rapport_heures_${startDate}_${endDate}.pdf`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(downloadUrl)
}

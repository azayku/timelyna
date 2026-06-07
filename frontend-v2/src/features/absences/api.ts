import { apiClient } from '../../lib/apiClient'
import type { Absence, CreateAbsencePayload } from './types'

export function fetchMyAbsences(): Promise<Absence[]> {
  return apiClient.get<Absence[]>('/employee/absences')
}

export function createAbsence(payload: CreateAbsencePayload): Promise<Absence> {
  return apiClient.post<Absence>('/employee/absences', payload)
}

export function cancelAbsence(id: number): Promise<void> {
  return apiClient.delete(`/employee/absences/${id}`)
}

export function fetchTeamAbsences(status?: string, year?: number): Promise<Absence[]> {
  const params = new URLSearchParams()
  if (status) params.append('status', status)
  if (year) params.append('year', year.toString())
  const q = params.toString() ? `?${params.toString()}` : ''
  return apiClient.get<Absence[]>(`/manager/absences${q}`)
}

export function approveAbsence(id: number): Promise<void> {
  return apiClient.post<void>(`/manager/absences/${id}/approve`, {})
}

export function rejectAbsence(id: number, reason: string): Promise<void> {
  return apiClient.post<void>(`/manager/absences/${id}/reject`, { reason })
}

export function revertAbsenceToPending(id: number): Promise<void> {
  return apiClient.post<void>(`/manager/absences/${id}/revert-to-pending`, {})
}

export function deleteAbsence(id: number): Promise<void> {
  return apiClient.delete(`/manager/absences/${id}`)
}

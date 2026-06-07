import { apiClient } from '../../lib/apiClient'
import type { WeekData, TimesheetEntry, CreateEntryPayload, UpdateEntryPayload } from './types'

export function fetchWeek(week: string): Promise<WeekData> {
  return apiClient.get<WeekData>(`/employee/timesheet/week?week=${week}`)
}

export function fetchDrafts(): Promise<TimesheetEntry[]> {
  return apiClient.get<TimesheetEntry[]>('/employee/timesheet/drafts')
}

export function createEntry(payload: CreateEntryPayload): Promise<TimesheetEntry> {
  return apiClient.post<TimesheetEntry>('/employee/timesheet/entries', payload)
}

export function updateEntry(id: number, payload: UpdateEntryPayload): Promise<TimesheetEntry> {
  return apiClient.put<TimesheetEntry>(`/employee/timesheet/entries/${id}`, payload)
}

export function deleteEntry(id: number): Promise<void> {
  return apiClient.delete(`/employee/timesheet/entries/${id}`)
}

export function submitWeek(week: string): Promise<{ status: string }> {
  return apiClient.post('/employee/timesheet/submit', { week })
}

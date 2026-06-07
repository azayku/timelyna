import { apiClient } from '../../lib/apiClient'

export interface TimerResponse {
  timer_id: number
  employee_id: number
  project_id: number
  description?: string
  task_type?: string
  started_at: string
  elapsed_seconds?: number
}

export interface TimerStopResponse {
  message: string
  hours_worked: number
  timesheet_entry_id?: number
}

export interface TimerStartPayload {
  project_id: number
  description?: string
  task_type?: string
}

export async function getActiveTimer(): Promise<TimerResponse | null> {
  try {
    const data = await apiClient.get<TimerResponse>('/timer/active')
    return data
  } catch {
    return null
  }
}

export async function startTimer(payload: TimerStartPayload): Promise<TimerResponse> {
  return apiClient.post<TimerResponse>('/timer/start', payload)
}

export async function stopTimer(): Promise<TimerStopResponse> {
  return apiClient.post<TimerStopResponse>('/timer/stop', {})
}

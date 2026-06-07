import { apiClient } from '../../lib/apiClient'
import type {
  Employee,
  CreateEmployeePayload,
  UpdateEmployeePayload,
  PendingEmployee,
  ScheduleDeactivationPayload,
  MutationLog,
} from './types'

interface PagedEmployees {
  items: Employee[]
  total: number
  page: number
  page_size: number
}

export async function fetchEmployees(): Promise<Employee[]> {
  const data = await apiClient.get<PagedEmployees>('/admin/users?page_size=2000')
  return data.items
}

export function fetchEmployee(id: number): Promise<Employee> {
  return apiClient.get<Employee>(`/admin/users/${id}`)
}

export function createEmployee(payload: CreateEmployeePayload): Promise<Employee | { type: 'pending'; account_creation_date: string }> {
  return apiClient.post('/admin/users', payload)
}

export function updateEmployee(id: number, payload: UpdateEmployeePayload): Promise<Employee> {
  return apiClient.put<Employee>(`/admin/users/${id}`, payload)
}

export function deactivateEmployee(id: number): Promise<void> {
  return apiClient.put<void>(`/admin/users/${id}/deactivate`, {})
}

export function scheduleDeactivation(id: number, payload: ScheduleDeactivationPayload): Promise<void> {
  return apiClient.put<void>(`/admin/users/${id}/schedule-deactivation`, payload)
}

export function cancelScheduledDeactivation(id: number): Promise<void> {
  return apiClient.delete(`/admin/users/${id}/schedule-deactivation`)
}

// Pending employees
export function fetchPendingEmployees(): Promise<PendingEmployee[]> {
  return apiClient.get<PendingEmployee[]>('/admin/pending-employees')
}

export function activatePendingEmployee(id: number): Promise<Employee> {
  return apiClient.post<Employee>(`/admin/pending-employees/${id}/activate`, {})
}

export function deletePendingEmployee(id: number): Promise<void> {
  return apiClient.delete(`/admin/pending-employees/${id}`)
}

// Mutation history
export function fetchMutationHistory(employeeId: number): Promise<MutationLog[]> {
  return apiClient.get<MutationLog[]>(`/admin/employees/${employeeId}/mutation-history`)
}

// Proxy
export function startProxy(employeeId: number): Promise<{ token: string; log_id: number }> {
  return apiClient.post('/admin/proxy/start', { employee_id: employeeId })
}

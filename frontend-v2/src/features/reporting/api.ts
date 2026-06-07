import { apiClient } from '../../lib/apiClient'
import type { EmployeeStatistics, HoursReportRow, HoursReportParams } from './types'

export function fetchEmployeeStatistics(period: string): Promise<EmployeeStatistics> {
  return apiClient.get<EmployeeStatistics>(`/employee/statistics?period=${period}`)
}

export function fetchHoursReport(params: HoursReportParams): Promise<HoursReportRow[]> {
  const qs = new URLSearchParams()
  qs.set('date_from', params.date_from)
  qs.set('date_to', params.date_to)
  if (params.employee_id != null) qs.set('employee_id', String(params.employee_id))
  if (params.project_id != null) qs.set('project_id', String(params.project_id))
  if (params.group_by) qs.set('group_by', params.group_by)
  return apiClient.get<HoursReportRow[]>(`/admin/hours-report?${qs.toString()}`)
}

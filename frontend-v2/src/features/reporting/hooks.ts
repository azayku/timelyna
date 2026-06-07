import { useQuery } from '@tanstack/react-query'
import { fetchEmployeeStatistics, fetchHoursReport } from './api'
import type { HoursReportParams } from './types'

export function useEmployeeStatistics(period: string) {
  return useQuery({
    queryKey: ['employee-statistics', period],
    queryFn: () => fetchEmployeeStatistics(period),
  })
}

export function useHoursReport(params: HoursReportParams, enabled = true) {
  return useQuery({
    queryKey: ['hours-report', params],
    queryFn: () => fetchHoursReport(params),
    enabled,
  })
}

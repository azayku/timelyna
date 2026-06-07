import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchEmployees,
  fetchEmployee,
  createEmployee,
  updateEmployee,
  deactivateEmployee,
  scheduleDeactivation,
  cancelScheduledDeactivation,
  fetchPendingEmployees,
  activatePendingEmployee,
  deletePendingEmployee,
  fetchMutationHistory,
} from './api'
import type { CreateEmployeePayload, UpdateEmployeePayload, ScheduleDeactivationPayload } from './types'

const EMPLOYEES_KEY = ['employees'] as const
const PENDING_KEY = ['pending-employees'] as const

export function useEmployees(options?: { enabled?: boolean }) {
  return useQuery({ queryKey: EMPLOYEES_KEY, queryFn: fetchEmployees, enabled: options?.enabled ?? true })
}

export function useEmployee(id: number) {
  return useQuery({
    queryKey: ['employees', id],
    queryFn: () => fetchEmployee(id),
    enabled: id > 0,
  })
}

export function useCreateEmployee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateEmployeePayload) => createEmployee(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: EMPLOYEES_KEY })
      qc.invalidateQueries({ queryKey: PENDING_KEY })
    },
  })
}

export function useUpdateEmployee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateEmployeePayload }) =>
      updateEmployee(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: EMPLOYEES_KEY }),
  })
}

export function useDeactivateEmployee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deactivateEmployee(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: EMPLOYEES_KEY }),
  })
}

export function useScheduleDeactivation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: ScheduleDeactivationPayload }) =>
      scheduleDeactivation(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: EMPLOYEES_KEY }),
  })
}

export function useCancelScheduledDeactivation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => cancelScheduledDeactivation(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: EMPLOYEES_KEY }),
  })
}

export function usePendingEmployees() {
  return useQuery({ queryKey: PENDING_KEY, queryFn: fetchPendingEmployees })
}

export function useActivatePendingEmployee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => activatePendingEmployee(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: PENDING_KEY })
      qc.invalidateQueries({ queryKey: EMPLOYEES_KEY })
    },
  })
}

export function useDeletePendingEmployee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deletePendingEmployee(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: PENDING_KEY }),
  })
}

export function useMutationHistory(employeeId: number) {
  return useQuery({
    queryKey: ['mutation-history', employeeId],
    queryFn: () => fetchMutationHistory(employeeId),
    enabled: employeeId > 0,
  })
}

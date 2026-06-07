import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../lib/authStore'
import {
  fetchManagerApprovals,
  fetchAdminApprovals,
  approveApproval,
  rejectApproval,
  fetchSubmissions,
  cancelSubmission,
  fetchApprovalEntries,
} from './api'

const MANAGER_KEY = (status: string) => ['manager-approvals', status] as const
const ADMIN_KEY = (status: string) => ['admin-approvals', status] as const
const SUBMISSIONS_KEY = (status: string) => ['submissions', status] as const

export function useManagerApprovals(status = 'pending') {
  // Only call for roles that have access to manager approvals
  const { user } = useAuthStore()
  const role = user?.role ?? 'employee'
  const canAccess = ['manager', 'admin', 'payroll'].includes(role)

  return useQuery({
    queryKey: MANAGER_KEY(status),
    queryFn: () => fetchManagerApprovals(status),
    enabled: canAccess,
  })
}

export function useAdminApprovals(status = 'all') {
  return useQuery({
    queryKey: ADMIN_KEY(status),
    queryFn: () => fetchAdminApprovals(status),
  })
}

export function useApproveApproval() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, notes }: { id: number; notes?: string }) => approveApproval(id, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['manager-approvals'] })
      qc.invalidateQueries({ queryKey: ['admin-approvals'] })
    },
  })
}

export function useRejectApproval() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => rejectApproval(id, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['manager-approvals'] })
      qc.invalidateQueries({ queryKey: ['admin-approvals'] })
    },
  })
}

export function useSubmissions(status = 'all') {
  return useQuery({
    queryKey: SUBMISSIONS_KEY(status),
    queryFn: () => fetchSubmissions(status),
  })
}

export function useCancelSubmission() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => cancelSubmission(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['submissions'] }),
  })
}

export function useApprovalEntries(id: number) {
  return useQuery({
    queryKey: ['approval-entries', id],
    queryFn: () => fetchApprovalEntries(id),
    enabled: id > 0,
  })
}

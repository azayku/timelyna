import { apiClient } from '../../lib/apiClient'
import type { Approval, ApprovalEntry } from './types'

type RawApproval = Omit<Approval, 'submitted_at'> & {
  created_at: string
}

function mapApproval(r: RawApproval): Approval {
  return { ...r, submitted_at: r.created_at }
}

// Manager
export function fetchManagerApprovals(status = 'pending'): Promise<Approval[]> {
  return apiClient.get<RawApproval[]>(`/manager/approvals?status=${status}`).then(list => list.map(mapApproval))
}

// Admin
export function fetchAdminApprovals(status = 'all'): Promise<Approval[]> {
  return apiClient.get<RawApproval[]>(`/admin/approvals?status=${status}`).then(list => list.map(mapApproval))
}

export function approveApproval(id: number, notes?: string): Promise<Approval> {
  return apiClient.post<Approval>(`/manager/approvals/${id}/approve`, { notes })
}

export function rejectApproval(id: number, rejection_reason: string): Promise<Approval> {
  return apiClient.post<Approval>(`/manager/approvals/${id}/reject`, { rejection_reason })
}

// Employee submissions
export function fetchSubmissions(status = 'all'): Promise<Approval[]> {
  return apiClient.get<RawApproval[]>(`/employee/submissions?status=${status}`).then(list => list.map(mapApproval))
}

export function cancelSubmission(id: number): Promise<Approval> {
  return apiClient.post<Approval>(`/employee/submissions/${id}/cancel`, {})
}

// Entries detail
export function fetchApprovalEntries(id: number): Promise<ApprovalEntry[]> {
  return apiClient.get<ApprovalEntry[]>(`/approvals/${id}/entries`)
}

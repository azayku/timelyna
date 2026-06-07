import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchMyAbsences,
  createAbsence,
  cancelAbsence,
  fetchTeamAbsences,
  approveAbsence,
  rejectAbsence,
} from './api'
import type { CreateAbsencePayload } from './types'

const MY_KEY = ['my-absences'] as const
const TEAM_KEY = ['team-absences'] as const

export function useMyAbsences() {
  return useQuery({ queryKey: MY_KEY, queryFn: fetchMyAbsences })
}

export function useCreateAbsence() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateAbsencePayload) => createAbsence(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: MY_KEY }),
  })
}

export function useCancelAbsence() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => cancelAbsence(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: MY_KEY }),
  })
}

export function useTeamAbsences(status?: string) {
  return useQuery({
    queryKey: [...TEAM_KEY, status],
    queryFn: () => fetchTeamAbsences(status),
  })
}

export function useApproveAbsence() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => approveAbsence(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: TEAM_KEY }),
  })
}

export function useRejectAbsence() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => rejectAbsence(id, reason),
    onSuccess: () => qc.invalidateQueries({ queryKey: TEAM_KEY }),
  })
}

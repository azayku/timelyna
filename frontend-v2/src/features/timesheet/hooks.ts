import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchWeek, fetchDrafts, createEntry, updateEntry, deleteEntry, submitWeek } from './api'
import type { CreateEntryPayload, UpdateEntryPayload } from './types'

export function useWeek(week: string) {
  return useQuery({
    queryKey: ['timesheet-week', week],
    queryFn: () => fetchWeek(week),
    enabled: !!week,
  })
}

export function useDrafts() {
  return useQuery({
    queryKey: ['timesheet-drafts'],
    queryFn: fetchDrafts,
  })
}

export function useCreateEntry(week: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateEntryPayload) => createEntry(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timesheet-week', week] }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['timesheet-week', week] })
      qc.invalidateQueries({ queryKey: ['timesheet-all-entries'] })
      qc.invalidateQueries({ queryKey: ['timesheet-drafts'] })
    },
  })
}

export function useUpdateEntry(week: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateEntryPayload }) =>
      updateEntry(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['timesheet-week', week] })
      qc.invalidateQueries({ queryKey: ['timesheet-all-entries'] })
      qc.invalidateQueries({ queryKey: ['timesheet-drafts'] })
    },
  })
}

export function useDeleteEntry(week: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteEntry(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['timesheet-week', week] })
      qc.invalidateQueries({ queryKey: ['timesheet-all-entries'] })
      qc.invalidateQueries({ queryKey: ['timesheet-drafts'] })
    },
  })
}

export function useSubmitWeek() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (week: string) => submitWeek(week),
    onSuccess: (_data, week) => {
      qc.invalidateQueries({ queryKey: ['timesheet-week', week] })
      qc.invalidateQueries({ queryKey: ['timesheet-all-entries'] })
      qc.invalidateQueries({ queryKey: ['timesheet-drafts'] })
    },
  })
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchSkillRates, createSkillRate, updateSkillRate, deleteSkillRate } from './api'
import type { CreateSkillRatePayload, UpdateSkillRatePayload } from './types'

const QUERY_KEY = ['skill-rates'] as const

export function useSkillRates() {
  return useQuery({ queryKey: QUERY_KEY, queryFn: fetchSkillRates })
}

export function useCreateSkillRate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateSkillRatePayload) => createSkillRate(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useUpdateSkillRate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateSkillRatePayload }) =>
      updateSkillRate(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useDeleteSkillRate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteSkillRate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

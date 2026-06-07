import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchOrganizations,
  createOrganization,
  updateOrganization,
  deleteOrganization,
} from './api'
import type { CreateOrganizationPayload, UpdateOrganizationPayload } from './types'

const QUERY_KEY = ['organizations'] as const

export function useOrganizations() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: fetchOrganizations,
  })
}

export function useCreateOrganization() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateOrganizationPayload) => createOrganization(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useUpdateOrganization() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateOrganizationPayload }) =>
      updateOrganization(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useDeleteOrganization() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteOrganization(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

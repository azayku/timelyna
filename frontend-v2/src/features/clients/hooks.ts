import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchClients, createClient, updateClient, deleteClient } from './api'
import type { CreateClientPayload, UpdateClientPayload } from './types'

const QUERY_KEY = ['clients'] as const

export function useClients() {
  return useQuery({ queryKey: QUERY_KEY, queryFn: fetchClients })
}

export function useCreateClient() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateClientPayload) => createClient(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useUpdateClient() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateClientPayload }) =>
      updateClient(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useDeleteClient() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteClient(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

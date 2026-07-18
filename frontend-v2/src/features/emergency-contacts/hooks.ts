import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchAllContacts,
  fetchEmployeeContacts,
  createContact,
  updateContact,
  deleteContact,
} from './api'
import type { UpdateEmergencyContactPayload } from './types'

export function useAllContacts() {
  return useQuery({
    queryKey: ['emergencyContacts', 'all'],
    queryFn: fetchAllContacts,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  })
}

export function useEmployeeContacts(employeeId: number) {
  return useQuery({
    queryKey: ['emergencyContacts', employeeId],
    queryFn: () => fetchEmployeeContacts(employeeId),
    enabled: !!employeeId,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  })
}

export function useCreateContact() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createContact,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emergencyContacts'] })
    },
  })
}

export function useUpdateContact() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ contactId, payload }: { contactId: number; payload: UpdateEmergencyContactPayload }) =>
      updateContact(contactId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emergencyContacts'] })
    },
  })
}

export function useDeleteContact() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteContact,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emergencyContacts'] })
    },
  })
}

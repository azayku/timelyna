import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMFAStatus, setupMFA, enableMFA, disableMFA } from './api'

export function useMFAStatus() {
  return useQuery({ queryKey: ['mfa-status'], queryFn: getMFAStatus })
}

export function useSetupMFA() {
  return useMutation({ mutationFn: setupMFA })
}

export function useEnableMFA() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: enableMFA,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['mfa-status'] }),
  })
}

export function useDisableMFA() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: disableMFA,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['mfa-status'] }),
  })
}

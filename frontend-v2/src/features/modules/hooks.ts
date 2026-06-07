import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchAllModulesStatus, startModuleTrial } from './api'

const KEY = ['module-licenses', 'status'] as const

export function useAllModulesStatus() {
  return useQuery({
    queryKey: KEY,
    queryFn: fetchAllModulesStatus,
    staleTime: 2 * 60 * 1000,
    retry: false,
  })
}

export function useStartModuleTrial() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (moduleName: string) => startModuleTrial(moduleName),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEY })
      qc.invalidateQueries({ queryKey: ['finance-license', 'status'] })
    },
  })
}

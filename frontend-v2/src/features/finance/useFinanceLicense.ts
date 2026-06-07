import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../../lib/apiClient'
import { useAuthStore } from '../../lib/authStore'

interface FinanceLicenseStatus {
  active: boolean
  expiry_date: string | null
  days_remaining: number | null
  error: string | null
}

const KEY = ['finance-license', 'status'] as const

export function useFinanceLicense() {
  const role = useAuthStore((s) => s.user?.role ?? 'employee')
  const isAdminOrFinance = ['admin', 'finance'].includes(role)

  const { data, isLoading, error } = useQuery<FinanceLicenseStatus>({
    queryKey: KEY,
    queryFn: async () => {
      try {
        return await apiClient.get<FinanceLicenseStatus>('/admin/finance-license/status')
      } catch {
        return { active: false, expiry_date: null, days_remaining: null, error: null }
      }
    },
    enabled: isAdminOrFinance,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 2 * 60 * 1000,
    retry: false,
  })

  return {
    isActive: data?.active ?? false,
    expiresAt: data?.expiry_date ?? null,
    daysLeft: data?.days_remaining ?? null,
    isLoading,
    error,
  }
}

export function useActivateFinanceLicense() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (license_key: string) =>
      apiClient.post('/admin/finance-license/activate', { license_key }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['finance-license', 'status'] }),
  })
}

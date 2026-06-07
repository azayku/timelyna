import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchLicenseStatus, activateLicense } from './api'
import { useAuthStore } from '../../lib/authStore'

const KEY = ['license-status'] as const

export function useLicenseStatus() {
  const role = useAuthStore((s) => s.user?.role ?? 'employee')
  const isAdmin = role === 'admin'
  return useQuery({
    queryKey: KEY,
    queryFn: fetchLicenseStatus,
    staleTime: 5 * 60 * 1000,
    enabled: isAdmin,
  })
}

export function useActivateLicense() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (token: string) => activateLicense(token),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}

/** Convenience: returns true if the given feature flag is enabled */
export function useCanUseFeature(feature: string): boolean {
  const { data } = useLicenseStatus()
  return data?.features[feature] === true
}

/** Convenience: returns days until expiry (9999 if unknown) */
export function useDaysUntilExpiry(): number {
  const { data } = useLicenseStatus()
  return data?.days_until_expiry ?? 9999
}

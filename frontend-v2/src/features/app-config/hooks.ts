import { useQuery } from '@tanstack/react-query'
import { fetchAppConfig } from './api'

/**
 * Hook to fetch and cache the application configuration.
 * Caches for 10 minutes since branding doesn't change often.
 */
export function useAppConfig() {
  return useQuery({
    queryKey: ['appConfig'],
    queryFn: fetchAppConfig,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
  })
}

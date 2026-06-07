import { useQuery } from '@tanstack/react-query'
import { getBudgetOverview, getProjectBudget } from './api'

export function useBudgetOverview() {
  return useQuery({
    queryKey: ['budget-overview'],
    queryFn: getBudgetOverview,
    staleTime: 5 * 60 * 1000,
  })
}

export function useProjectBudget(projectId: number) {
  return useQuery({
    queryKey: ['project-budget', projectId],
    queryFn: () => getProjectBudget(projectId),
    enabled: !!projectId,
  })
}

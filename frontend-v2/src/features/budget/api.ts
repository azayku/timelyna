import { apiClient } from '../../lib/apiClient'

export interface ProjectBudgetStatus {
  project_id: number
  project_name: string
  client_id: number | null
  client_name: string | null
  manager_id: number | null
  manager_name: string | null
  budget_hours: number | null
  consumed_hours: number
  remaining_hours: number | null
  consumption_percentage: number | null
  alert: boolean
}

export async function getBudgetOverview(): Promise<ProjectBudgetStatus[]> {
  return apiClient.get<ProjectBudgetStatus[]>('/projects/budget-overview')
}

export async function getProjectBudget(projectId: number): Promise<ProjectBudgetStatus> {
  return apiClient.get<ProjectBudgetStatus>(`/projects/${projectId}/budget`)
}

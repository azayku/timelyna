import { apiClient } from '../../lib/apiClient'
import type { Project, CreateProjectPayload, UpdateProjectPayload } from './types'

export async function fetchProjects(): Promise<Project[]> {
  const data = await apiClient.get<Array<Omit<Project, 'budget_hours' | 'billing_rate' | 'budget_amount'> & { budget_hours: string | null; billing_rate: string; budget_amount: string | null }>>('/admin/projects?limit=500')
  return data.map(p => ({
    ...p,
    budget_hours: p.budget_hours != null ? Number(p.budget_hours) : null,
    billing_rate: Number(p.billing_rate),
    budget_amount: p.budget_amount != null ? Number(p.budget_amount) : null,
  }))
}

export function createProject(payload: CreateProjectPayload): Promise<Project> {
  return apiClient.post<Project>('/admin/projects/with-skills', payload)
}

export function updateProject(id: number, payload: UpdateProjectPayload): Promise<Project> {
  return apiClient.put<Project>(`/admin/projects/${id}/with-skills`, payload)
}

export function deleteProject(id: number): Promise<void> {
  return apiClient.delete(`/admin/projects/${id}`)
}

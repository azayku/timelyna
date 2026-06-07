import { apiClient } from '../../lib/apiClient'

export interface SuggestedEmployee {
  employee_id: number
  full_name: string
  org_name: string
  matching_skills: string[]
  matching_skill_count: number
}

export function fetchSuggestedEmployees(projectId: number): Promise<SuggestedEmployee[]> {
  return apiClient.get<SuggestedEmployee[]>(
    `/admin/projects/${projectId}/suggested-employees`,
  )
}

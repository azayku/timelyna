import { apiClient } from '../../lib/apiClient'

export interface EntryTemplate {
  template_id: number
  employee_id: number
  name: string
  project_id: number | null
  task_type: string | null
  description: string | null
  default_hours: number | null
  is_favorite: boolean
  created_at: string
}

export interface EntryTemplateCreate {
  name: string
  project_id?: number
  task_type?: string
  description?: string
  default_hours?: number
  is_favorite?: boolean
}

export async function getMyTemplates(): Promise<EntryTemplate[]> {
  return await apiClient.get<EntryTemplate[]>('/entry-templates/')
}

export async function createTemplate(data: EntryTemplateCreate): Promise<EntryTemplate> {
  return await apiClient.post<EntryTemplate>('/entry-templates/', data)
}

export async function deleteTemplate(templateId: number): Promise<void> {
  await apiClient.delete(`/entry-templates/${templateId}`)
}

export async function updateTemplate(
  templateId: number,
  data: Partial<EntryTemplateCreate>
): Promise<EntryTemplate> {
  return await apiClient.put<EntryTemplate>(`/entry-templates/${templateId}`, data)
}

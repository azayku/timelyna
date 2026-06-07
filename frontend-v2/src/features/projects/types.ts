export interface Project {
  project_id: number
  client_id: number
  project_name: string
  project_code: string
  description: string | null
  status: 'draft' | 'planning' | 'active' | 'paused' | 'completed' | 'cancelled'
  start_date: string
  end_date: string | null
  budget_hours: number | null
  budget_amount: number | null
  billing_rate: number
  manager_id: number
  team_members: number[] | null
}

export interface CreateProjectPayload {
  client_id: number
  project_name: string
  project_code?: string
  description?: string
  status?: Project['status']
  start_date: string
  end_date?: string
  budget_hours?: number
  billing_rate: number
  manager_id: number
  required_skills?: { skill_rate_id: number; quantity: number }[]
}

export interface UpdateProjectPayload {
  project_name?: string
  description?: string
  status?: Project['status']
  end_date?: string
  budget_hours?: number
  billing_rate?: number
  manager_id?: number
  required_skills?: { skill_rate_id: number; quantity: number }[]
}

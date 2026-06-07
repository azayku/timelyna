export interface SkillRate {
  id: number
  org_id: number
  skill_name: string
  billing_rate: number
  description: string | null
  created_at: string | null
}

export interface CreateSkillRatePayload {
  skill_name: string
  billing_rate: number
  description?: string
}

export interface UpdateSkillRatePayload {
  skill_name?: string
  billing_rate?: number
  description?: string
}

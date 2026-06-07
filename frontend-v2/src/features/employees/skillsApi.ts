import { apiClient } from '../../lib/apiClient'

export interface EmployeeSkill {
  id: number
  employee_id: number
  skill_rate_id: number
  skill_name: string
  assigned_at: string
}

export interface SkillRate {
  id: number
  skill_name: string
  org_id: number
}

export function fetchEmployeeSkills(employeeId: number): Promise<EmployeeSkill[]> {
  return apiClient.get<EmployeeSkill[]>(`/admin/employees/${employeeId}/skills`)
}

export function addEmployeeSkill(
  employeeId: number,
  skillRateId: number,
): Promise<EmployeeSkill> {
  return apiClient.post<EmployeeSkill>(`/admin/employees/${employeeId}/skills`, {
    skill_rate_id: skillRateId,
  })
}

export function removeEmployeeSkill(
  employeeId: number,
  skillRateId: number,
): Promise<void> {
  return apiClient.delete(`/admin/employees/${employeeId}/skills/${skillRateId}`)
}

/** Fetch all available skill rates (used to populate the add-skill selector). */
export function fetchSkillRates(): Promise<SkillRate[]> {
  return apiClient.get<SkillRate[]>('/admin/skill-rates')
}

import { apiClient } from '../../lib/apiClient'
import type { SkillRate, CreateSkillRatePayload, UpdateSkillRatePayload } from './types'

export function fetchSkillRates(): Promise<SkillRate[]> {
  return apiClient.get<SkillRate[]>('/admin/skill-rates')
}

export function createSkillRate(payload: CreateSkillRatePayload): Promise<SkillRate> {
  return apiClient.post<SkillRate>('/admin/skill-rates', payload)
}

export function updateSkillRate(id: number, payload: UpdateSkillRatePayload): Promise<SkillRate> {
  return apiClient.put<SkillRate>(`/admin/skill-rates/${id}`, payload)
}

export function deleteSkillRate(id: number): Promise<void> {
  return apiClient.delete(`/admin/skill-rates/${id}`)
}

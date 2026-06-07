import { apiClient } from '../../lib/apiClient'

export interface ModuleStatus {
  active: boolean
  expires_at: string | null
  expires_ts: number | null
  days_remaining: number | null
}

export interface AllModulesStatus {
  modules: Record<string, ModuleStatus>
}

export interface TrialResult {
  module: string
  trial: boolean
  expires_at: string
  expires_ts: number
  days_remaining: number
}

export function fetchAllModulesStatus(): Promise<AllModulesStatus> {
  return apiClient.get<AllModulesStatus>('/admin/module-licenses/status')
}

export function startModuleTrial(moduleName: string): Promise<TrialResult> {
  return apiClient.post<TrialResult>(`/admin/module-licenses/${moduleName}/trial`, {})
}

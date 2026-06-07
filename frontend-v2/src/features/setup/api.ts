import { apiClient } from '../../lib/apiClient'

export interface SetupStatus {
  is_installed: boolean
  app_name: string
}

export interface SetupPayload {
  company_name: string
  app_name: string
  company_logo?: string | null
  admin_email: string
  admin_first_name: string
  admin_last_name: string
  admin_password: string
}

export interface SetupResult {
  message: string
  company_name: string
  app_name: string
}

export async function fetchSetupStatus(): Promise<SetupStatus> {
  return apiClient.get<SetupStatus>('/setup/status')
}

export async function runSetup(payload: SetupPayload): Promise<SetupResult> {
  return apiClient.post<SetupResult>('/setup', payload)
}

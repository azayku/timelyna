import { apiClient } from '../../lib/apiClient'

export interface AppConfig {
  app_name: string
  company_name: string
  company_logo: string | null
}

/**
 * Fetch the application configuration (branding, logos, etc.)
 * This is used throughout the app to display consistent branding.
 */
export async function fetchAppConfig(): Promise<AppConfig> {
  return apiClient.get<AppConfig>('/setup/config')
}

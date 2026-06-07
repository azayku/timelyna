import { apiClient } from '../../lib/apiClient'
import type { LicenseStatus } from './types'

export function fetchLicenseStatus(): Promise<LicenseStatus> {
  return apiClient.get<LicenseStatus>('/admin/license/status')
}

export function activateLicense(license_token: string): Promise<void> {
  return apiClient.post('/admin/license/activate', { license_token })
}

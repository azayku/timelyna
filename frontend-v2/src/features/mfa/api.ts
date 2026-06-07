import { apiClient } from '../../lib/apiClient'

export interface MFAStatus {
  mfa_enabled: boolean
}

export interface MFASetup {
  secret: string
  qr_code_base64: string
  totp_uri: string
}

export async function getMFAStatus(): Promise<MFAStatus> {
  return apiClient.get<MFAStatus>('/mfa/status')
}

export async function setupMFA(): Promise<MFASetup> {
  return apiClient.post<MFASetup>('/mfa/setup', {})
}

export async function enableMFA(code: string): Promise<void> {
  await apiClient.post<void>('/mfa/enable', { code })
}

export async function disableMFA(code: string): Promise<void> {
  await apiClient.post<void>('/mfa/disable', { code })
}

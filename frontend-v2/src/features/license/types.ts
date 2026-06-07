export interface LicenseStatus {
  pack?: string
  validation_status: 'valid' | 'expired' | 'invalid' | 'no_license'
  days_until_expiry: number | null
  expires_at: string | null
  features: Record<string, boolean>
  limits: Record<string, number>
  usage?: Record<string, number>
  status?: string
}

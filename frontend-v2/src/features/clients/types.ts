export interface Client {
  client_id: number
  client_name: string
  company_name: string | null
  email: string
  phone: string | null
  address: string | null
  default_billing_rate: number
  currency: string
  tax_id: string | null
  client_status: 'active' | 'inactive'
}

export interface CreateClientPayload {
  client_name: string
  company_name?: string
  email: string
  phone?: string
  address?: string
  default_billing_rate: number
  currency?: string
  tax_id?: string
}

export interface UpdateClientPayload {
  client_name?: string
  company_name?: string
  email?: string
  phone?: string
  address?: string
  default_billing_rate?: number
  currency?: string
  tax_id?: string
  client_status?: 'active' | 'inactive'
}

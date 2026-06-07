import { apiClient } from '../../lib/apiClient'
import type { Client, CreateClientPayload, UpdateClientPayload } from './types'

export async function fetchClients(): Promise<Client[]> {
  const data = await apiClient.get<Array<Omit<Client, 'default_billing_rate'> & { default_billing_rate: string }>>('/admin/clients?limit=500')
  return data.map(c => ({ ...c, default_billing_rate: Number(c.default_billing_rate) }))
}

export function createClient(payload: CreateClientPayload): Promise<Client> {
  return apiClient.post<Client>('/admin/clients', payload)
}

export function updateClient(id: number, payload: UpdateClientPayload): Promise<Client> {
  return apiClient.put<Client>(`/admin/clients/${id}`, payload)
}

export function deleteClient(id: number): Promise<void> {
  return apiClient.delete(`/admin/clients/${id}`)
}

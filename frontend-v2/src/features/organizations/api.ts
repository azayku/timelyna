import { apiClient } from '../../lib/apiClient'
import type { Organization, CreateOrganizationPayload, UpdateOrganizationPayload } from './types'

export function fetchOrganizations(): Promise<Organization[]> {
  return apiClient.get<Organization[]>('/admin/organizations')
}

export function createOrganization(payload: CreateOrganizationPayload): Promise<Organization> {
  return apiClient.post<Organization>('/admin/organizations', payload)
}

export function updateOrganization(
  id: number,
  payload: UpdateOrganizationPayload,
): Promise<Organization> {
  return apiClient.put<Organization>(`/admin/organizations/${id}`, payload)
}

export function deleteOrganization(id: number): Promise<void> {
  return apiClient.delete(`/admin/organizations/${id}`)
}

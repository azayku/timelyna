import { apiClient } from '../../lib/apiClient'
import type {
  EmergencyContact,
  CreateEmergencyContactPayload,
  UpdateEmergencyContactPayload,
} from './types'

export async function fetchAllContacts(): Promise<EmergencyContact[]> {
  return apiClient.get<EmergencyContact[]>('/emergency-contacts')
}

export async function fetchEmployeeContacts(employeeId: number): Promise<EmergencyContact[]> {
  return apiClient.get<EmergencyContact[]>(`/emergency-contacts/employee/${employeeId}`)
}

export async function createContact(payload: CreateEmergencyContactPayload): Promise<EmergencyContact> {
  return apiClient.post<EmergencyContact>('/emergency-contacts', payload)
}

export async function updateContact(
  contactId: number,
  payload: UpdateEmergencyContactPayload,
): Promise<EmergencyContact> {
  return apiClient.put<EmergencyContact>(`/emergency-contacts/${contactId}`, payload)
}

export async function deleteContact(contactId: number): Promise<void> {
  return apiClient.delete(`/emergency-contacts/${contactId}`)
}

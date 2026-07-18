import type { Employee } from '../employees/types'

export interface EmergencyContact {
  contact_id: number
  employee_id: number
  contact_name: string
  phone_number: string
  contact_type: 'urgence' | 'manager' | 'patron' | 'client' | 'autre'
  tags: string | null  // JSON array as string
  notes: string | null
  created_by: number
  is_active: boolean
  deleted_at: string | null
  created_at: string
  updated_at: string
}

export interface EmployeeWithContacts extends Employee {
  emergency_contacts: EmergencyContact[]
}

export interface CreateEmergencyContactPayload {
  employee_id: number
  contact_name: string
  phone_number: string
  contact_type: 'urgence' | 'manager' | 'patron' | 'client' | 'autre'
  tags?: string
  notes?: string
}

export interface UpdateEmergencyContactPayload {
  contact_name?: string
  phone_number?: string
  contact_type?: string
  tags?: string
  notes?: string
  is_active?: boolean
}

export const CONTACT_TYPES = [
  { value: 'urgence', label: 'Urgence' },
  { value: 'manager', label: 'Manager' },
  { value: 'patron', label: 'Patron' },
  { value: 'client', label: 'Client' },
  { value: 'autre', label: 'Autre' },
]

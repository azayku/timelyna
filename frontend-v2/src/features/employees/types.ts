export interface Employee {
  employee_id: number
  first_name: string
  last_name: string
  email: string
  username: string | null
  role: 'employee' | 'manager' | 'admin' | 'finance' | 'payroll'
  employment_status: 'active' | 'inactive'
  org_id: number
  org_name?: string
  birth_date: string | null
  address: string | null
  deactivation_scheduled_at: string | null
  hire_date?: string | null
  created_at?: string
  must_change_password?: boolean
  preferred_language?: string
  manager_id?: number | null
}

export interface CreateEmployeePayload {
  first_name: string
  last_name: string
  email: string
  role: Employee['role']
  org_id: number
  birth_date?: string
  address?: string
  hire_date?: string
}

export interface UpdateEmployeePayload {
  first_name?: string
  last_name?: string
  email?: string
  role?: Employee['role']
  org_id?: number
  birth_date?: string
  address?: string
  employment_status?: Employee['employment_status']
}

export interface PendingEmployee {
  id: number
  full_name: string
  email: string
  role: Employee['role']
  org_id: number
  hire_date: string
  account_creation_date: string
  created_at: string
}

export interface ScheduleDeactivationPayload {
  scheduled_at: string
}

export interface MutationLog {
  id: number
  employee_id: number
  from_org_id: number
  to_org_id: number
  mutated_by: number
  mutated_at: string
  reason: string | null
}

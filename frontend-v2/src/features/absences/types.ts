export interface Absence {
  absence_id: number
  employee_id: number
  employee_name: string
  org_name: string
  absence_type: string
  start_date: string
  end_date: string
  status: 'pending' | 'approved' | 'rejected'
  notes: string | null
  rejection_reason: string | null
  created_at: string
  // Leave balance info
  annual_leave_days: number
  days_taken_this_year: number
  days_remaining: number
  last_leave_date: string | null
  last_leave_days: number
}

export interface CreateAbsencePayload {
  absence_type: string
  start_date: string
  end_date: string
  notes?: string
}

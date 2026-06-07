export interface TimesheetEntry {
  timesheet_entry_id: number
  employee_id: number
  project_id: number
  project_name?: string
  work_date: string
  hours_worked: number
  description: string
  task_type: string
  entry_type: 'normal' | 'overtime' | 'travel' | 'night'
  billable_flag: boolean
  billing_rate: number | null
  notes: string | null
  status: 'draft' | 'submitted' | 'approved' | 'rejected' | 'invoiced'
  proxy_admin_id: number | null
}

export interface WeekData {
  week: string
  entries: Record<string, TimesheetEntry[]>
  daily_totals: Record<string, number>
  week_total: number
}

export interface CreateEntryPayload {
  project_id: number
  work_date: string
  hours_worked: number
  description: string
  task_type?: string
  entry_type?: TimesheetEntry['entry_type']
  billable_flag?: boolean
  billing_rate?: number
  notes?: string
}

export interface UpdateEntryPayload {
  hours_worked?: number
  description?: string
  task_type?: string
  billable_flag?: boolean
  billing_rate?: number
  notes?: string
}

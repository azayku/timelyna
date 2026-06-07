export interface Approval {
  approval_id: number
  employee_id: number
  employee_name?: string
  week_start: string
  total_hours?: number
  status: 'pending' | 'approved' | 'rejected' | 'invoiced'
  submitted_at: string
  decided_at: string | null
  rejection_reason: string | null
  notes: string | null
}

export interface ApprovalEntry {
  timesheet_entry_id: number
  work_date: string
  project_name: string
  entry_type: string
  hours_worked: number
  description: string
  notes: string | null
  billable_flag: boolean
  status: string
}

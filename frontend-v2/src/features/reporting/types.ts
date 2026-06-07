export interface ProjectBreakdown {
  project_id: number
  project_name: string
  hours: number
}

export interface TaskTypeBreakdown {
  task_type: string
  hours: number
}

export interface WeeklyTrend {
  week: string
  hours: number
}

export interface EmployeeStatistics {
  period: string
  start_date: string
  end_date: string
  total_hours: number
  billable_hours: number
  billable_pct: number
  days_worked: number
  approved_count: number
  submitted_count: number
  project_breakdown: ProjectBreakdown[]
  task_type_breakdown: TaskTypeBreakdown[]
  weekly_trend: WeeklyTrend[]
}

export interface HoursReportRow {
  period_key: string
  employee_id: number
  employee_name: string
  project_id: number
  project_name: string
  work_date: string
  entry_type: 'normal' | 'overtime' | 'travel' | 'night'
  normal_hours: number
  overtime_hours: number
  travel_hours: number
  night_hours: number
  total_hours: number
}

export interface HoursReportParams {
  date_from: string
  date_to: string
  employee_id?: number
  project_id?: number
  group_by?: 'day' | 'project' | 'employee' | 'entry_type'
}

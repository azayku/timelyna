export interface Organization {
  org_id: number
  org_name: string
  manager_id: number | null
  employee_count: number
  created_at: string
}

export interface CreateOrganizationPayload {
  org_name: string
  manager_id: number
}

export interface UpdateOrganizationPayload {
  org_name?: string
  manager_id?: number
}

// ─── Dashboard Types ──────────────────────────────────────────────────────────

export interface DashboardKpis {
  total_revenue: number
  total_revenue_trend: number
  billed_hours: number
  billed_hours_trend: number
  gross_margin: number
  gross_margin_trend: number
  invoice_count: number
  invoice_count_trend: number
}

export interface MonthlyRevenue {
  month: string
  revenue: number
  hours: number
}

export interface ClientRevenue {
  client_name: string
  revenue: number
}

export interface BurnRateItem {
  project_id: number
  project_name: string
  budget_hours: number
  billed_hours: number
}

export interface RecentInvoiceItem {
  invoice_id: number
  invoice_number: string
  client_name: string
  total_amount: number
  currency: string
  status: string
  created_at: string | null
  due_date: string | null
}

export interface OverdueInvoiceItem {
  invoice_id: number
  invoice_number: string
  client_name: string
  total_amount: number
  currency: string
  due_date: string
  days_overdue: number
}

export interface DashboardData {
  period: string
  start_date: string
  end_date: string
  kpis: DashboardKpis
  monthly_revenue: MonthlyRevenue[]
  client_revenue: ClientRevenue[]
  burn_rate: BurnRateItem[]
  recent_invoices: RecentInvoiceItem[]
  overdue_invoices: OverdueInvoiceItem[]
}

// ─── Reports Types ────────────────────────────────────────────────────────────

export interface PnLReport {
  period: string
  start_date: string
  end_date: string
  revenue: number
  costs: number
  gross_margin: number
  gross_margin_pct: number
  net_margin: number
  net_margin_pct: number
}

export interface ProjectProfitability {
  project_id: number
  project_name: string
  client_name: string
  budget_hours: number
  actual_hours: number
  hours_variance: number
  revenue: number
  internal_cost: number
  margin: number
  margin_pct: number
}

export interface AgingBucket {
  invoice_id: number
  invoice_number: string
  client_name: string
  total_amount: number
  currency: string
  due_date: string
  days_overdue: number
}

export interface AgingReport {
  buckets: {
    '0_30': AgingBucket[]
    '31_60': AgingBucket[]
    '61_90': AgingBucket[]
    'over_90': AgingBucket[]
  }
  totals: {
    '0_30': number
    '31_60': number
    '61_90': number
    'over_90': number
  }
  grand_total: number
}

export interface CashflowForecast {
  month: string
  expected_amount: number
  invoice_count: number
}

// ─── Invoice Audit Types ──────────────────────────────────────────────────────

export interface InvoiceAuditLog {
  log_id: number
  invoice_id: number
  action: string
  performed_by: number
  performed_by_name: string
  timestamp: string
  details: Record<string, unknown> | null
}

// ─── Period Type ──────────────────────────────────────────────────────────────

export type Period = 'this_month' | 'last_month' | 'quarter' | 'year'

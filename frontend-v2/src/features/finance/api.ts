import { apiClient } from '../../lib/apiClient'
import type {
  DashboardData,
  PnLReport,
  ProjectProfitability,
  AgingReport,
  CashflowForecast,
  InvoiceAuditLog,
  Period,
} from './types'

// ─── Dashboard ────────────────────────────────────────────────────────────────

export function fetchFinanceDashboard(period: Period = 'this_month'): Promise<DashboardData> {
  return apiClient.get<DashboardData>(`/finance/dashboard?period=${period}`)
}

// ─── Reports ──────────────────────────────────────────────────────────────────

export function fetchPnL(period: Period = 'this_month'): Promise<PnLReport> {
  return apiClient.get<PnLReport>(`/finance/reports/pnl?period=${period}`)
}

export function fetchProjectProfitability(): Promise<ProjectProfitability[]> {
  return apiClient.get<ProjectProfitability[]>('/finance/reports/profitability')
}

export function fetchAgingReport(): Promise<AgingReport> {
  return apiClient.get<AgingReport>('/finance/reports/aging')
}

export function fetchCashflowForecast(months: number = 3): Promise<CashflowForecast[]> {
  return apiClient.get<CashflowForecast[]>(`/finance/reports/cashflow?months=${months}`)
}

// ─── Invoice Actions ──────────────────────────────────────────────────────────

export function markInvoicePaid(invoiceId: number): Promise<void> {
  return apiClient.post(`/finance/invoices/${invoiceId}/mark-paid`, {})
}

export function fetchInvoiceAuditLogs(invoiceId: number): Promise<InvoiceAuditLog[]> {
  return apiClient.get<InvoiceAuditLog[]>(`/finance/invoices/${invoiceId}/audit-logs`)
}

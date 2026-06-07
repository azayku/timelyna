import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchFinanceDashboard,
  fetchPnL,
  fetchProjectProfitability,
  fetchAgingReport,
  fetchCashflowForecast,
  markInvoicePaid,
  fetchInvoiceAuditLogs,
} from './api'
import type { Period } from './types'

// ─── Query Keys ───────────────────────────────────────────────────────────────

const KEYS = {
  dashboard: (period: Period) => ['finance-dashboard', period] as const,
  pnl: (period: Period) => ['finance-pnl', period] as const,
  profitability: ['finance-profitability'] as const,
  aging: ['finance-aging'] as const,
  cashflow: (months: number) => ['finance-cashflow', months] as const,
  auditLogs: (invoiceId: number) => ['finance-invoice-audit', invoiceId] as const,
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export function useFinanceDashboard(period: Period = 'this_month') {
  return useQuery({
    queryKey: KEYS.dashboard(period),
    queryFn: () => fetchFinanceDashboard(period),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// ─── Reports ──────────────────────────────────────────────────────────────────

export function useFinancePnL(period: Period = 'this_month') {
  return useQuery({
    queryKey: KEYS.pnl(period),
    queryFn: () => fetchPnL(period),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useProjectProfitability() {
  return useQuery({
    queryKey: KEYS.profitability,
    queryFn: fetchProjectProfitability,
    staleTime: 5 * 60 * 1000,
  })
}

export function useAgingReport() {
  return useQuery({
    queryKey: KEYS.aging,
    queryFn: fetchAgingReport,
    staleTime: 5 * 60 * 1000,
  })
}

export function useCashflowForecast(months: number = 3) {
  return useQuery({
    queryKey: KEYS.cashflow(months),
    queryFn: () => fetchCashflowForecast(months),
    staleTime: 5 * 60 * 1000,
  })
}

// ─── Invoice Actions ──────────────────────────────────────────────────────────

export function useMarkInvoicePaid() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (invoiceId: number) => markInvoicePaid(invoiceId),
    onSuccess: () => {
      // Invalidate all finance queries that might show invoice status
      qc.invalidateQueries({ queryKey: ['finance-dashboard'] })
      qc.invalidateQueries({ queryKey: ['finance-aging'] })
      qc.invalidateQueries({ queryKey: ['invoices'] })
    },
  })
}

export function useInvoiceAuditLogs(invoiceId: number) {
  return useQuery({
    queryKey: KEYS.auditLogs(invoiceId),
    queryFn: () => fetchInvoiceAuditLogs(invoiceId),
    enabled: invoiceId > 0,
  })
}

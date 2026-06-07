import { apiClient } from '../../lib/apiClient'
import type { Invoice, InvoiceDetail, CreateInvoiceRequest } from './types'

export const invoicingApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return apiClient.get<Invoice[]>(`/finance/invoices${qs}`)
  },

  getById: (id: number) =>
    apiClient.get<InvoiceDetail>(`/finance/invoices/${id}`),

  create: (data: CreateInvoiceRequest) =>
    apiClient.post<Invoice>('/finance/invoices', data),

  finalize: (id: number) =>
    apiClient.post<Invoice>(`/finance/invoices/${id}/finalize`, {}),

  send: (id: number) =>
    apiClient.post<Invoice>(`/finance/invoices/${id}/send`, {}),

  markPaid: (id: number, paid_at?: string) =>
    apiClient.post<Invoice>(`/finance/invoices/${id}/mark-paid`, { paid_at }),

  getAuditLogs: (id: number) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    apiClient.get<any[]>(`/finance/invoices/${id}/audit-logs`),
}

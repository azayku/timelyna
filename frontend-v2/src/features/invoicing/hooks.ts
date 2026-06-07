import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { invoicingApi } from './api'
import type { Invoice, InvoiceDetail, CreateInvoiceRequest } from './types'

export function useInvoices(params?: Record<string, any>) {
  return useQuery<Invoice[]>({
    queryKey: ['invoices', params],
    queryFn: () => invoicingApi.list(params),
    staleTime: 2 * 60 * 1000,
  })
}

export function useInvoice(id: number) {
  return useQuery<InvoiceDetail>({
    queryKey: ['invoice', id],
    queryFn: () => invoicingApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateInvoice() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateInvoiceRequest) => invoicingApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices'] })
    },
  })
}

export function useFinalizeInvoice() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => invoicingApi.finalize(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['invoice', id] })
    },
  })
}

export function useSendInvoice() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => invoicingApi.send(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['invoice', id] })
    },
  })
}

export function useMarkInvoicePaid() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, paid_at }: { id: number; paid_at?: string }) =>
      invoicingApi.markPaid(id, paid_at),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['invoice', id] })
      qc.invalidateQueries({ queryKey: ['finance-dashboard'] })
    },
  })
}

export function useInvoiceAuditLogs(id: number) {
  return useQuery({
    queryKey: ['invoice-audit-logs', id],
    queryFn: () => invoicingApi.getAuditLogs(id),
    enabled: !!id,
  })
}

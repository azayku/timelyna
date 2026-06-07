export interface Invoice {
  invoice_id: number
  invoice_number: string
  client_id: number
  client_name?: string
  period_start: string
  period_end: string
  subtotal_ht: number
  tax_rate: number
  tax_amount: number
  total_ttc: number
  currency: string
  status: 'draft' | 'ready' | 'sent' | 'paid' | 'overdue'
  due_date: string | null
  paid_at: string | null
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface InvoiceLineItem {
  line_item_id: number
  invoice_id: number
  description: string
  quantity: number
  unit_price: number
  total_price: number
}

export interface InvoiceDetail extends Invoice {
  line_items: InvoiceLineItem[]
}

export interface CreateInvoiceRequest {
  client_id: number
  period_start: string
  period_end: string
  tax_rate?: number
  currency?: string
}

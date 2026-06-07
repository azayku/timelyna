# Design — Invoicing

## Data Model
```sql
CREATE TABLE invoices (
  invoice_id BIGSERIAL PRIMARY KEY,
  client_id BIGINT NOT NULL REFERENCES clients(client_id),
  invoice_number VARCHAR(50) UNIQUE NOT NULL,  -- INV-2025-0042
  period VARCHAR(10) NOT NULL,                 -- "2025-03" or "2025-Q1"
  total_hours DECIMAL(10,2),
  total_amount DECIMAL(12,2) NOT NULL,
  tax_rate DECIMAL(5,2) DEFAULT 20.00,
  tax_amount DECIMAL(12,2),
  currency VARCHAR(3) DEFAULT 'EUR',
  line_items JSONB,   -- [{ project_id, project_name, hours, rate, subtotal }]
  status VARCHAR(50) NOT NULL DEFAULT 'draft',  -- draft|ready|sent|paid
  pdf_s3_url VARCHAR(500),
  created_by BIGINT REFERENCES employees(employee_id),
  created_at TIMESTAMP DEFAULT NOW(),
  sent_at TIMESTAMP,
  paid_at TIMESTAMP
);
```

## API
```
POST /api/v1/finance/invoices                    body: { client_id, period }
GET  /api/v1/finance/invoices                    ?client_id=X&status=draft
GET  /api/v1/finance/invoices/{id}
POST /api/v1/finance/invoices/{id}/finalize
POST /api/v1/finance/invoices/{id}/send
GET  /api/v1/finance/invoices/{id}/download
```

## Service Logic
### `InvoicingService.create_draft(client_id, period, created_by)`
1. Collect approved entries for client in period
2. If none → 400
3. Group by project → compute subtotals
4. Auto-generate invoice number (sequential per client)
5. Insert `invoices` record with `status = 'draft'`

### `InvoicingService.finalize(invoice_id)`
1. Load invoice (must be `draft`)
2. Set `status = 'ready'`
3. Batch update all referenced entry IDs to `status = 'invoiced'`

### `InvoicingService.send(invoice_id)`
1. Generate PDF via Celery (WeasyPrint template)
2. Upload to S3 → update `pdf_s3_url`
3. Send email to client with PDF attached
4. Set `status = 'sent'`, record `sent_at`

## Frontend
- `InvoicesPage.tsx` — list with filters
- `CreateInvoiceModal.tsx` — client + period selector → preview line items
- `InvoiceDetailPage.tsx` — line items table, totals, finalize/send buttons

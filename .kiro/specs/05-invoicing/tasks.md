# Tasks — Invoicing

- [x] **5.1** Write Alembic migration: `invoices` table
- [x] **5.2** Create `Invoice` SQLAlchemy model
- [x] **5.3** `InvoicingRepository`: `create`, `get_by_id`, `list`, `update_status`
- [x] **5.4** `InvoicingService.create_draft()` — collect entries, compute line items, auto invoice number
- [x] **5.5** `InvoicingService.finalize()` — status guard + batch mark entries as `invoiced`
- [x] **5.6** `InvoicingService.send()` — Celery PDF generation + S3 upload + email
- [x] **5.7** Celery task `generate_invoice_pdf(invoice_id)` using WeasyPrint + Jinja2 template
- [x] **5.8** Register all finance invoice routes with `require_role('finance', 'admin')`
- [x] **5.9** Unit test: `create_draft` — no approved entries, success with line item calculation
- [x] **5.10** Unit test: `finalize` — entries marked invoiced and immutable
- [x] **5.11** Integration test: create → finalize → entries cannot be edited
- [x] **5.12** Create `InvoicesPage.tsx` with status filter and client filter
- [x] **5.13** Create `CreateInvoiceModal.tsx` with live line item preview
- [x] **5.14** Create `InvoiceDetailPage.tsx` with finalize/send action buttons

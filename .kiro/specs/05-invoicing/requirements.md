# Requirements — Invoicing

## Feature Overview
Generate client invoices from approved, non-invoiced timesheets. Mark invoiced timesheets as immutable.

---

## Acceptance Criteria

### US-01 — Create Draft Invoice
- WHEN finance selects a client + period THE SYSTEM SHALL auto-collect all `approved` non-invoiced entries
- WHEN no approved entries exist THE SYSTEM SHALL return a 400 error
- THE SYSTEM SHALL compute line items: per project → hours × billing_rate → subtotal

### US-02 — Review & Finalize
- WHEN a draft invoice is viewed THE SYSTEM SHALL show line items, totals, tax
- WHEN finance confirms the invoice THE SYSTEM SHALL set status to `ready` and mark all entries as `invoiced`
- WHEN an entry is marked `invoiced` THE SYSTEM SHALL prevent any further edits

### US-03 — Send Invoice
- WHEN finance sends an invoice THE SYSTEM SHALL generate a PDF and email it to the client
- WHEN sent THE SYSTEM SHALL set status to `sent` and record `sent_at`

### US-04 — Invoice History
- THE SYSTEM SHALL list all invoices filterable by client, status, period
- THE SYSTEM SHALL allow re-downloading any invoice PDF

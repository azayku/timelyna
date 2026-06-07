# Design — Approvals Workflow

## Data Model

```sql
CREATE TABLE approvals (
  approval_id BIGSERIAL PRIMARY KEY,
  timesheet_entries JSONB NOT NULL,         -- array of timesheet_entry_ids
  submitted_by BIGINT NOT NULL REFERENCES employees(employee_id),
  submitted_at TIMESTAMP DEFAULT NOW(),
  submitted_period VARCHAR(10) NOT NULL,     -- ISO week e.g. "2025-W12"
  reviewed_by BIGINT REFERENCES employees(employee_id),
  reviewed_at TIMESTAMP,
  approval_status VARCHAR(50) NOT NULL DEFAULT 'pending',
  -- pending | approved | rejected | cancelled | invoiced
  rejection_reason VARCHAR(500),
  approval_notes VARCHAR(500),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_submitted_by (submitted_by),
  INDEX idx_status (approval_status),
  INDEX idx_period (submitted_period)
);
```

## Status State Machine
```
[draft entries] → submit_week() → pending
pending → approve() → approved  (entries: approved)
pending → reject()  → rejected  (entries: draft, re-editable)
pending → cancel()  → cancelled (entries: draft)
approved → invoice() → invoiced (entries: invoiced) [triggered by invoicing spec]
```

## API Endpoints

```
GET  /api/v1/manager/approvals              ?status=pending&page=1
GET  /api/v1/manager/approvals/{id}
POST /api/v1/manager/approvals/{id}/approve body: { notes? }
POST /api/v1/manager/approvals/{id}/reject  body: { rejection_reason }

GET  /api/v1/employee/submissions           ?status=all&page=1
POST /api/v1/employee/submissions/{id}/cancel

GET  /api/v1/admin/approvals               (all orgs)
POST /api/v1/admin/approvals/{id}/approve  (override)
```

## Service Logic

### `ApprovalService.approve(manager_id, approval_id, notes?)`
1. Load approval — 404 if not found
2. Check `submitted_by` reports to `manager_id` (or role is admin) — 403 otherwise
3. Check status is `pending` — 409 otherwise
4. Set `approval_status = 'approved'`, `reviewed_by`, `reviewed_at`
5. Batch update all entry IDs to `status = 'approved'`
6. Dispatch Celery: `send_approval_notification(approval_id, 'approved')`
7. Write to `audit_logs`

### `ApprovalService.reject(manager_id, approval_id, reason)`
1. Same auth checks as approve
2. Validate `reason` length ≥ 10 chars
3. Set `approval_status = 'rejected'`
4. Batch update all entry IDs back to `status = 'draft'`
5. Dispatch Celery: `send_approval_notification(approval_id, 'rejected', reason)`
6. Write to `audit_logs`

## Frontend Components

**`src/features/approvals/`**
- `ApprovalsPage.tsx` — Manager view: table of pending submissions
- `ApprovalDetail.tsx` — Drill-down: entry list, hours breakdown, approve/reject buttons
- `RejectionModal.tsx` — Modal with reason textarea (min 10 chars)
- `SubmissionsPage.tsx` — Employee view: own submission history
- `SubmissionStatusBadge.tsx` — Color-coded badge (pending=yellow, approved=green, rejected=red)
- `useManagerApprovals.ts` — React Query: GET /manager/approvals
- `useApproveSubmission.ts`, `useRejectSubmission.ts`

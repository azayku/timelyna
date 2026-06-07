# Design — Reporting & Analytics

## API Endpoints
```
GET /api/v1/employee/statistics?period=this_month
GET /api/v1/manager/team-statistics?period=this_month
GET /api/v1/admin/organization-statistics?period=this_month
GET /api/v1/finance/client-report?client_id=X&period=2025-Q1
GET /api/v1/finance/project-report?project_id=X

POST /api/v1/exports                body: { report_type, filters, format: "pdf"|"csv" }
GET  /api/v1/exports/{id}/download
```

## Query Strategy
All reports use raw SQL aggregates via SQLAlchemy `text()` for performance — do NOT load all ORM objects into memory.

### Personal Stats Query (example)
```sql
SELECT
  SUM(hours_worked) AS total_hours,
  SUM(CASE WHEN billable_flag THEN hours_worked ELSE 0 END) AS billable_hours,
  COUNT(DISTINCT work_date) AS days_worked
FROM timesheet_entries
WHERE employee_id = :employee_id
  AND work_date BETWEEN :start_date AND :end_date
  AND status IN ('approved', 'invoiced')
  AND deleted_at IS NULL
```

### Financial Report Query
```sql
SELECT
  p.project_id,
  p.project_name,
  p.budget_hours,
  p.budget_amount,
  SUM(te.hours_worked) AS actual_hours,
  SUM(te.hours_worked * COALESCE(te.billing_rate, p.billing_rate)) AS revenue,
  SUM(te.hours_worked * e.hourly_cost) AS internal_cost
FROM timesheet_entries te
JOIN projects p ON te.project_id = p.project_id
JOIN employees e ON te.employee_id = e.employee_id
WHERE te.status IN ('approved', 'invoiced')
  AND te.deleted_at IS NULL
GROUP BY p.project_id, p.project_name, p.budget_hours, p.budget_amount
```

## Export Architecture
```
POST /exports → Celery task queued → returns { export_id, status: "pending" }
Celery worker → generate PDF (WeasyPrint) or CSV → upload to S3
→ update export record status to "ready" → push in-app notification
GET /exports/{id}/download → redirect to signed S3 URL (1h TTL)
```

## Frontend Components
- `StatisticsPage.tsx` — period selector tabs + 4 metric cards + 3 charts
- `HoursTrendChart.tsx` — Recharts LineChart (weekly hours)
- `ProjectBreakdownChart.tsx` — Recharts PieChart
- `TeamStatisticsPage.tsx` — table per employee with mini sparklines
- `FinancialReportPage.tsx` — client accordion → project rows with margin %
- `ExportButton.tsx` — triggers async export, polls status, shows download when ready

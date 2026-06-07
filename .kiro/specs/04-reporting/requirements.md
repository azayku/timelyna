# Requirements — Reporting & Analytics

## Feature Overview
Multi-dimensional analytics for employees (personal stats), managers (team stats), and admins/finance (org-wide + financial reports).

---

## User Stories & Acceptance Criteria

### US-01 — Personal Statistics (Employee)
**As an** employee,  
**I want to** view my own stats for a period,  
**So that** I can track my productivity and billable %.

**Acceptance Criteria:**
- WHEN an employee requests stats THE SYSTEM SHALL return: total hours, billable hours, billable %, approval rate, avg hours/week
- THE SYSTEM SHALL support periods: `this_month`, `last_month`, `quarter`, `year`, `all`
- THE SYSTEM SHALL return a breakdown by project and by task_type
- THE SYSTEM SHALL return a weekly trend (hours per week) as a time series

### US-02 — Team Statistics (Manager)
**As a** manager,  
**I want to** see stats for my entire team,  
**So that** I can spot under/over-utilization.

**Acceptance Criteria:**
- WHEN a manager requests team stats THE SYSTEM SHALL aggregate data for all direct reports
- THE SYSTEM SHALL return per-employee summary: total hours, billable %, pending submissions count
- THE SYSTEM SHALL include utilization rate (hours worked / contracted hours if available)

### US-03 — Financial Reports (Admin/Finance)
**As a** finance user,  
**I want to** see revenue, cost, and margin per client and project,  
**So that** I can report financial performance.

**Acceptance Criteria:**
- THE SYSTEM SHALL return for each client: total hours, revenue (hours × billing_rate), internal cost (hours × hourly_cost), gross margin
- THE SYSTEM SHALL return for each project: budget hours vs actual, budget € vs revenue, burn rate
- WHEN a project exceeds 80% of budget hours THE SYSTEM SHALL flag it with a `budget_warning`

### US-04 — Export
**As a** user,  
**I want to** export my stats or reports,  
**So that** I can share them or archive them.

**Acceptance Criteria:**
- THE SYSTEM SHALL support export as PDF and CSV for all report views
- WHEN an export is requested THE SYSTEM SHALL generate it asynchronously and notify the user when ready
- THE SYSTEM SHALL store generated exports for 30 days and provide a download link

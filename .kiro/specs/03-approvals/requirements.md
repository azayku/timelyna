# Requirements — Approvals Workflow

## Feature Overview
Structured manager approval process for submitted timesheets: pending → approved/rejected → invoiced.

---

## User Stories & Acceptance Criteria

### US-01 — View Pending Approvals (Manager)
**As a** manager,  
**I want to** see all pending timesheets from my direct reports,  
**So that** I can review and approve them promptly.

**Acceptance Criteria:**
- WHEN a manager views their approvals THE SYSTEM SHALL return only submissions from their direct reports
- THE SYSTEM SHALL show: employee name, week period, total hours, billable %, submitted date
- WHEN no pending approvals exist THE SYSTEM SHALL return an empty state

### US-02 — Approve Timesheet
**As a** manager,  
**I want to** approve a submitted timesheet,  
**So that** the hours are validated and can be invoiced.

**Acceptance Criteria:**
- WHEN a manager approves a submission THE SYSTEM SHALL set `approval_status = 'approved'` and all linked entries to `status = 'approved'`
- WHEN approved THE SYSTEM SHALL notify the employee by email and in-app
- WHEN a manager tries to approve a submission not from their team THE SYSTEM SHALL return a 403 error
- WHEN a submission is already approved THE SYSTEM SHALL return a 409 error

### US-03 — Reject Timesheet
**As a** manager,  
**I want to** reject a timesheet with a reason,  
**So that** the employee can fix it and resubmit.

**Acceptance Criteria:**
- WHEN a manager rejects a submission THE SYSTEM SHALL require a `rejection_reason` (min 10 chars)
- WHEN rejected THE SYSTEM SHALL set `approval_status = 'rejected'` and all linked entries back to `status = 'draft'`
- WHEN rejected THE SYSTEM SHALL notify the employee with the rejection reason
- WHEN a submission is already approved THE SYSTEM SHALL prevent rejection

### US-04 — Employee Submission History
**As an** employee,  
**I want to** see all my past submissions and their status,  
**So that** I know which weeks are pending, approved, or rejected.

**Acceptance Criteria:**
- THE SYSTEM SHALL return all submissions for the current employee, paginated (20/page)
- WHEN a submission is rejected THE SYSTEM SHALL show the rejection reason
- THE SYSTEM SHALL allow filtering by status: all, pending, approved, rejected, invoiced

### US-05 — Cancel Submission (Employee)
**As an** employee,  
**I want to** cancel a pending submission,  
**So that** I can correct errors before my manager reviews it.

**Acceptance Criteria:**
- WHEN an employee cancels a `pending` submission THE SYSTEM SHALL set it to `cancelled` and reset entries to `draft`
- WHEN submission is not `pending` THE SYSTEM SHALL return a 400 error

### US-06 — Admin Override
**As an** admin,  
**I want to** approve or reject any submission,  
**So that** I can handle escalations and edge cases.

**Acceptance Criteria:**
- WHEN an admin approves/rejects any submission THE SYSTEM SHALL apply the same rules as a manager approval
- THE SYSTEM SHALL log the admin override in `audit_logs`

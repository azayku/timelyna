# Requirements — Core Timesheet (Employees, Clients, Projects, Entries)

## Feature Overview
The core data model and timesheet entry CRUD. This is the central feature employees interact with daily.

---

## User Stories & Acceptance Criteria

### US-01 — Weekly Timesheet View
**As an** employee,  
**I want to** view my timesheet for any given week,  
**So that** I can track and edit my hours before submitting.

**Acceptance Criteria:**
- WHEN an employee requests a week view THE SYSTEM SHALL return all their timesheet entries for that ISO week
- THE SYSTEM SHALL display entries grouped by day (Mon–Sun)
- THE SYSTEM SHALL show the total hours per day and for the week
- WHEN no entries exist for a day THE SYSTEM SHALL show an empty state with an "Add" prompt

### US-02 — Create Timesheet Entry
**As an** employee,  
**I want to** log hours on a project for a given day,  
**So that** my work is recorded for approval and billing.

**Acceptance Criteria:**
- WHEN an employee submits an entry with valid data THE SYSTEM SHALL create it with status `draft`
- THE SYSTEM SHALL require: `project_id`, `work_date`, `hours_worked`, `description`, `task_type`
- WHEN `hours_worked` is not between 0.25 and 16 THE SYSTEM SHALL return a 422 validation error
- WHEN `work_date` is in the future THE SYSTEM SHALL return a 422 validation error
- WHEN an entry already exists for (employee, project, work_date) THE SYSTEM SHALL return a 409 conflict error
- WHEN the total hours for an employee on a given day exceed 16 THE SYSTEM SHALL return a 422 error
- WHEN the project is not active THE SYSTEM SHALL return a 422 error

### US-03 — Edit Timesheet Entry
**As an** employee,  
**I want to** edit a draft timesheet entry,  
**So that** I can correct mistakes before submission.

**Acceptance Criteria:**
- WHEN an employee edits a `draft` entry THE SYSTEM SHALL update it and record `updated_at`
- WHEN an employee tries to edit a `submitted` or `approved` entry THE SYSTEM SHALL return a 403 error
- WHEN an employee tries to edit another employee's entry THE SYSTEM SHALL return a 403 error
- WHEN an entry is `invoiced` THE SYSTEM SHALL return a 403 error (immutable)

### US-04 — Delete Timesheet Entry
**As an** employee,  
**I want to** delete a draft entry,  
**So that** I can remove accidental entries.

**Acceptance Criteria:**
- WHEN an employee deletes a `draft` entry THE SYSTEM SHALL soft-delete it (set `deleted_at`)
- WHEN an entry is not in `draft` status THE SYSTEM SHALL return a 403 error
- WHEN an entry is `approved` or `invoiced` THE SYSTEM SHALL never be physically deleted

### US-05 — Submit Week for Approval
**As an** employee,  
**I want to** submit my week's timesheet for approval,  
**So that** my manager can review and approve my hours.

**Acceptance Criteria:**
- WHEN an employee submits a week THE SYSTEM SHALL create an `approval` record and set all `draft` entries for that week to `submitted`
- WHEN a week has no draft entries THE SYSTEM SHALL return a 400 error
- WHEN an employee submits a week that was already submitted THE SYSTEM SHALL return a 409 error
- WHEN submission succeeds THE SYSTEM SHALL send a notification to the employee's manager

### US-06 — Project & Client Reference Data
**As an** employee,  
**I want to** select from a list of active projects,  
**So that** I log hours against the correct project.

**Acceptance Criteria:**
- WHEN an employee loads the timesheet form THE SYSTEM SHALL return all active projects they are a member of (or all active projects for admins)
- THE SYSTEM SHALL include the client name with each project for display
- WHEN no active projects exist THE SYSTEM SHALL return an empty list

### US-07 — Admin CRUD for Entities
**As an** admin,  
**I want to** manage employees, clients, and projects,  
**So that** the organization data stays up to date.

**Acceptance Criteria:**
- THE SYSTEM SHALL provide full CRUD for `employees`, `clients`, and `projects` (admin only)
- WHEN a client is deactivated THE SYSTEM SHALL deactivate all their active projects
- WHEN a project is deactivated THE SYSTEM SHALL prevent new timesheet entries on it
- WHEN an employee is deactivated THE SYSTEM SHALL prevent new timesheet entries by them

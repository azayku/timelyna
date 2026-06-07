# Design — Core Timesheet

## Data Models

```sql
CREATE TABLE employees (
  employee_id BIGSERIAL PRIMARY KEY,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  role VARCHAR(50) NOT NULL DEFAULT 'employee',  -- employee|manager|admin|finance
  department VARCHAR(100),
  manager_id BIGINT REFERENCES employees(employee_id),
  hourly_cost DECIMAL(10,2),
  employment_status VARCHAR(50) NOT NULL DEFAULT 'active',  -- active|inactive|terminated
  hire_date DATE,
  deleted_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE clients (
  client_id BIGSERIAL PRIMARY KEY,
  client_name VARCHAR(255) NOT NULL,
  company_name VARCHAR(255),
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  address TEXT,
  default_billing_rate DECIMAL(10,2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'EUR',
  tax_id VARCHAR(50),
  client_status VARCHAR(50) NOT NULL DEFAULT 'active',
  deleted_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE projects (
  project_id BIGSERIAL PRIMARY KEY,
  client_id BIGINT NOT NULL REFERENCES clients(client_id),
  project_name VARCHAR(255) NOT NULL,
  project_code VARCHAR(50) UNIQUE NOT NULL,
  description TEXT,
  status VARCHAR(50) NOT NULL DEFAULT 'active',  -- planning|active|paused|completed
  start_date DATE NOT NULL,
  end_date DATE,
  budget_hours DECIMAL(10,2),
  budget_amount DECIMAL(12,2),
  billing_rate DECIMAL(10,2) NOT NULL,
  manager_id BIGINT NOT NULL REFERENCES employees(employee_id),
  team_members JSONB,  -- array of employee_ids
  deleted_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_client (client_id),
  INDEX idx_status (status)
);

CREATE TABLE timesheet_entries (
  timesheet_entry_id BIGSERIAL PRIMARY KEY,
  employee_id BIGINT NOT NULL REFERENCES employees(employee_id),
  project_id BIGINT NOT NULL REFERENCES projects(project_id),
  work_date DATE NOT NULL,
  hours_worked DECIMAL(5,2) NOT NULL CHECK (hours_worked BETWEEN 0.25 AND 16),
  description VARCHAR(500) NOT NULL,
  task_type VARCHAR(50) NOT NULL DEFAULT 'other',  -- dev|design|testing|doc|meeting|other
  billable_flag BOOLEAN NOT NULL DEFAULT true,
  billing_rate DECIMAL(10,2),  -- overrides project rate if set
  status VARCHAR(50) NOT NULL DEFAULT 'draft',  -- draft|submitted|approved|rejected|invoiced
  notes VARCHAR(500),
  deleted_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  submitted_at TIMESTAMP,
  approved_at TIMESTAMP,
  UNIQUE (employee_id, project_id, work_date),
  INDEX idx_employee_date (employee_id, work_date),
  INDEX idx_project (project_id),
  INDEX idx_status (status)
);
```

---

## API Endpoints

### Timesheet Entries (Employee)
```
GET    /api/v1/employee/timesheet/week?week=2025-W12
POST   /api/v1/employee/timesheet/entries
PUT    /api/v1/employee/timesheet/entries/{id}
DELETE /api/v1/employee/timesheet/entries/{id}
POST   /api/v1/employee/timesheet/submit          body: { week: "2025-W12" }
```

### Reference Data
```
GET    /api/v1/projects?active=true              (employee: filtered to their projects)
GET    /api/v1/clients                           (admin/finance only)
```

### Admin CRUD
```
GET/POST         /api/v1/admin/employees
GET/PUT/DELETE   /api/v1/admin/employees/{id}
GET/POST         /api/v1/admin/clients
GET/PUT/DELETE   /api/v1/admin/clients/{id}
GET/POST         /api/v1/admin/projects
GET/PUT/DELETE   /api/v1/admin/projects/{id}
```

---

## Service Layer Logic

### `TimesheetService.get_week(employee_id, week_str)`
1. Parse ISO week string → `start_date`, `end_date`
2. Query entries `WHERE employee_id = X AND work_date BETWEEN start AND end AND deleted_at IS NULL`
3. Group by `work_date`, return with daily totals

### `TimesheetService.create_entry(employee_id, data)`
1. Validate `hours_worked` range, `work_date <= today`
2. Check project is `active`
3. Check unique (employee, project, date) — raises 409 if exists
4. Check total hours for that day ≤ 16 (sum existing + new)
5. Insert with `status = 'draft'`

### `TimesheetService.submit_week(employee_id, week_str)`
1. Load all `draft` entries for employee + week
2. If none → raise 400
3. Check no existing `pending`/`approved` approval for same week → raise 409 if exists
4. Create `approval` record with `status = 'pending'`
5. Set all entries to `status = 'submitted'`
6. Dispatch notification to manager (async Celery task)

---

## Frontend Components

**`src/features/timesheet/`**
- `TimesheetWeekPage.tsx` — main weekly grid view
- `TimesheetWeekGrid.tsx` — Mon–Sun columns, projects as rows
- `EntryCell.tsx` — inline editable cell (hours input)
- `EntryFormModal.tsx` — full entry form (project, hours, description, task type)
- `DailySummary.tsx` — shows total hours per day (red if >8)
- `WeekSummary.tsx` — total + billable % + submit button
- `useTimesheetWeek.ts` — React Query hook for week data
- `useCreateEntry.ts`, `useUpdateEntry.ts`, `useDeleteEntry.ts`

**Week navigation:** `◄ Week ►` buttons, URL param `?week=2025-W12`

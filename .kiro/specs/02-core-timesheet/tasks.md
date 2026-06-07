# Tasks — Core Timesheet

### Phase A — Migrations & Models
- [x] **2.1** Write Alembic migration: `employees` table (extends from auth spec)
- [x] **2.2** Write Alembic migration: `clients` table
- [x] **2.3** Write Alembic migration: `projects` table
- [x] **2.4** Write Alembic migration: `timesheet_entries` table (with unique constraint + check constraint)
- [x] **2.5** Create SQLAlchemy models: `Employee`, `Client`, `Project`, `TimesheetEntry`

### Phase B — Repositories
- [x] **2.6** `EmployeeRepository`: `get_by_id`, `get_by_email`, `list_active`, `create`, `update`, `soft_delete`
- [x] **2.7** `ClientRepository`: `get_by_id`, `list_active`, `create`, `update`, `deactivate`
- [x] **2.8** `ProjectRepository`: `get_by_id`, `list_active_for_employee`, `create`, `update`, `deactivate`
- [x] **2.9** `TimesheetRepository`: `get_week`, `get_by_id`, `create`, `update`, `soft_delete`, `get_daily_total`

### Phase C — Services
- [x] **2.10** `TimesheetService.get_week(employee_id, week_str)` — parse ISO week, group by day
- [x] **2.11** `TimesheetService.create_entry(employee_id, data)` — all validations (range, date, unique, daily max, project active)
- [x] **2.12** `TimesheetService.update_entry(employee_id, entry_id, data)` — ownership + status guard
- [x] **2.13** `TimesheetService.delete_entry(employee_id, entry_id)` — draft-only soft delete
- [x] **2.14** `TimesheetService.submit_week(employee_id, week_str)` — create approval + update statuses + dispatch notification

### Phase D — API Routes
- [x] **2.15** `GET /api/v1/employee/timesheet/week`
- [x] **2.16** `POST /api/v1/employee/timesheet/entries`
- [x] **2.17** `PUT /api/v1/employee/timesheet/entries/{id}`
- [x] **2.18** `DELETE /api/v1/employee/timesheet/entries/{id}`
- [x] **2.19** `POST /api/v1/employee/timesheet/submit`
- [x] **2.20** `GET /api/v1/projects` (employee: filtered, admin: all)
- [x] **2.21** Admin CRUD routes: employees, clients, projects

### Phase E — Backend Tests
- [x] **2.22** Unit test: `create_entry` — all validation paths (range, future date, duplicate, daily max, inactive project)
- [x] **2.23** Unit test: `submit_week` — no entries, already submitted, success
- [x] **2.24** Integration test: full week create → submit flow
- [x] **2.25** Integration test: RBAC — employee cannot access admin routes

### Phase F — Frontend
- [x] **2.26** Create `TimesheetWeekPage.tsx` with week navigator (URL param `?week=`)
- [x] **2.27** Create `TimesheetWeekGrid.tsx` — projects × days matrix
- [x] **2.28** Create `EntryFormModal.tsx` with Zod validation
- [x] **2.29** Create `DailySummary.tsx` — total hours with red if >8
- [x] **2.30** Implement `useTimesheetWeek` React Query hook (invalidates on create/update/delete)
- [x] **2.31** Create admin pages: `EmployeesPage`, `ClientsPage`, `ProjectsPage` with CRUD tables
- [x] **2.32** Add timesheet navigation item to sidebar

### Phase G — Améliorations post-spec
- [x] **2.33** Ajout du champ `entry_type` sur `timesheet_entries` (normal / overtime / travel) — comptabilisation séparée
- [x] **2.34** Contrainte UNIQUE mise à jour : `(employee_id, project_id, work_date, entry_type)` — permet plusieurs types le même jour
- [x] **2.35** Suppression de la limite 16h/jour hardcodée — remplacée par `OrgSettings.max_hours_per_day`
- [x] **2.36** Saisie d'heures pour n'importe quel jour passé (sélecteur de date sur `TimesheetEntryPage`)
- [x] **2.37** Soumission semaine : autorisée uniquement pour les semaines passées (lundi suivant)
- [x] **2.38** Messages d'erreur traduits en français (utilitaire `getErrorMessage` dans `lib/errors.ts`)
- [x] **2.39** Handler global FastAPI pour convertir les exceptions non catchées en réponses JSON propres
- [x] **2.40** Migration `migrate_add_columns.py` et `migrate_fix_unique.py` pour les DB existantes

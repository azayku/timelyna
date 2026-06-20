---
inclusion: always
---

# Timelyna — Project Structure

## Repository Layout
```
timelyna/
├── .kiro/
│   ├── steering/          # Always-on project context
│   └── specs/             # Feature specs (requirements, design, tasks)
├── backend/
│   ├── app/
│   │   ├── api/v1/        # Route handlers, grouped by domain
│   │   ├── core/          # Config, security, dependencies
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response models
│   │   ├── services/      # Business logic (no DB calls here directly)
│   │   ├── repositories/  # DB access layer (SQLAlchemy queries)
│   │   ├── tasks/         # Celery async tasks
│   │   └── utils/         # Shared helpers (JWT, email, PDF, etc.)
│   ├── migrations/        # Alembic migration files
│   ├── tests/             # pytest test suite
│   └── Dockerfile
├── frontend-v2/           # Active frontend (React 18 + Vite + Tailwind)
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Route-level page components
│   │   ├── features/      # Feature-specific logic (hooks, stores, api calls)
│   │   ├── lib/           # Shared utilities (api client, formatters)
│   │   ├── types/         # TypeScript type definitions
│   │   └── styles/        # Global CSS, Tailwind config
│   ├── public/
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Naming Conventions
- **Files:** `snake_case.py` (backend), `PascalCase.tsx` (React components), `camelCase.ts` (hooks/utils)
- **API routes:** plural nouns, kebab-case — `/api/v1/timesheet-entries`
- **DB tables:** `snake_case` plural — `timesheet_entries`
- **React components:** PascalCase — `TimesheetWeekView`
- **Hooks:** `use` prefix — `useTimesheetEntries`
- **Celery tasks:** `snake_case` verbs — `send_approval_notification`

## Architecture Patterns
- **Backend:** Repository pattern (data access) + Service layer (business logic) + Router (HTTP)
- **Frontend:** Feature-sliced structure; each feature folder has its own `api.ts`, `hooks.ts`, `types.ts`
- **Auth:** JWT stored in httpOnly cookie (not localStorage)
- **Error handling:** Standardized `{ detail: string, code: string }` error response

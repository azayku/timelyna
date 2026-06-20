# Timelyna — Pilotage Project Rules

This document defines the core principles, architecture, and technology stack for the Timelyna project. All code generation and suggestions must adhere to these rules.

## 🚀 Product Overview
Timelyna is a SaaS application for managing worked hours with a **modular plugin ecosystem**.
- **Targets:** SMEs of 10–500 employees.
- **Key Flow:** Daily/weekly logs -> Manager Approval -> Finance Invoicing -> Plugin Extension.
- **Constraints:**
  - No physical deletion of approved timesheets (Soft deletes).
  - No modification of invoiced timesheets.
  - GDPR-compliant audit logs (90-day retention).

## 📁 Project Structure
- `backend/`: FastAPI application.
  - `app/api/v1/`: Domain-specific routes.
  - `app/models/`: SQLAlchemy ORM models.
  - `app/schemas/`: Pydantic V2 schemas.
  - `app/services/`: Business logic.
  - `app/repositories/`: Data access layer.
- `frontend-v2/`: React 18+ (Vite, Tailwind, TypeScript).
  - `src/features/`: Feature-sliced logic.
  - `src/components/`: Reusable UI.

## 🛠 Tech Stack
### Backend
- **Framework:** FastAPI / Python 3.11+.
- **ORM:** SQLAlchemy 2.x (async).
- **Validation:** Pydantic v2.
- **Tasks:** Celery + Redis.
- **Testing:** pytest.

### Frontend
- **Framework:** React 18 / TypeScript / Vite.
- **Styling:** Tailwind CSS.
- **Data Fetching:** TanStack Query v5.
- **State:** Zustand.
- **Icons:** Lucide React.
- **Grids:** AG Grid.

## 📏 Conventions
- **Naming:**
  - Python: `snake_case`.
  - React Components: `PascalCase`.
  - Hooks: `usePrefix`.
  - API Routes: `/api/v1/plural-kebab-case`.
- **Database:**
  - Tables: plural `snake_case`.
  - IDs: `BIGINT` (core) or UUID (plugins).
  - Soft deletes: `deleted_at` timestamp.
- **Architecture:**
  - Backend: Route -> Service -> Repository.
  - Frontend: Component -> Hook -> API Feature.
- **Auth:** JWT in httpOnly cookie.
- **Errors:** `{ "detail": "message", "code": "ERROR_CODE" }`.

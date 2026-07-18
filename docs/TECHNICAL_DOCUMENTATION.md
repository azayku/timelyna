# Timelyna — Documentation Technique (par fonctionnalité)

Ce document donne une vue technique pragmatique de l'application Timelyna, feature par feature : responsabilité backend, schémas, endpoints, composants frontend principaux, hooks React Query, queues / tâches, tests et notes d'exploitation.

---

## Sommaire
- Vue d'ensemble
- Authentification
- Employés
- Timesheets
- Absences
- Approvals (validations)
- Notifications / In-app
- Projets & Clients
- Compétences / Skill Rates
- Invoicing / Finance
- Reporting
- UI / Composants réutilisables
- API client et hooks
- Tests
- Déploiement & environnements (dev/uat/prod)
- CI/CD (GitHub Actions)
- Variables d'environnement et secrets
- Commands utiles / runbook

---

## Vue d'ensemble
- Stack backend : FastAPI (Python 3.11+), SQLAlchemy 2.x (async), Pydantic v2, Celery + Redis pour tâches asynchrones.
- Stack frontend : React + TypeScript (Vite), Tailwind CSS, TanStack Query v5, Zustand pour certains stores.
- Containerisation : Docker Compose; architecture multi-env: `docker-compose.yml` (base) + `docker-compose.uat.yml` (overrides) + `docker-compose.proxy.yml` (top-level nginx proxy).

---

## Authentification
Responsabilité : `backend/app/api/v1/auth` (routes), `backend/app/services/auth_service.py`.

Backend
- Endpoints typiques : `/auth/login`, `/auth/logout`, `/auth/refresh`.
- Méthode : JWT en cookie httpOnly (clé signée par `SECRET_KEY`).
- Schémas : `backend/app/schemas/auth/*.py` (Pydantic v2).

Frontend
- Composants : pages de login, hooks dans `frontend-v2/src/lib/authStore.ts`.
- Appel à l'API via `apiClient.post('/auth/login', ...)`.

Tests
- `backend/tests/test_auth_*.py` — vérifie refresh, rate-limiting, RBAC.

Notes d'exploitation
- Garder `SECRET_KEY` identique entre instances si on partage des tokens.

---

## Employés
Responsabilité : `backend/app/models/employee.py`, `backend/app/api/v1/employees`.

Fonctions
- CRUD employés, génération de username, onboarding, attributs: organisation, manager_id, roles.

Frontend
- Pages d'administration: `AdminClientsPage.tsx`, `Employee` panels.

Tests
- `tests/test_employee_creation.py`, `tests/test_pending_employees.py`.

---

## Timesheets
Responsabilité : `backend/app/services/timesheet_service.py`, `backend/app/api/v1/timesheets`.

Backend
- Opérations : create/update/delete entries, submit week, resubmit, drafts.
- Notification : envoi de notifications aux managers et admins (fan-out via helper `_notify_timesheet_submission`).
- Transactions et règles métier : interdictions sur timesheets approuvés/invoiced.

Frontend
- Hooks : `frontend-v2/src/features/timesheet/hooks.ts` — `useCreateEntry`, `useUpdateEntry`, `useDeleteEntry`, `useSubmitWeek`. Utilise `queryClient.invalidateQueries` pour invalidation des clés `['timesheet-week', week]`, `['timesheet-all-entries']`, `['timesheet-drafts']`.
- Composants : `QuickTimesheetModal.tsx`, `TimesheetEntryPage.tsx`.

Tests
- `tests/test_timesheet.py`.

Notes
- Description seulement requise pour `overtime` (UI enforce). Vérifier invalidations caches quand on touche aux drafts.

---

## Absences
Responsabilité : `backend/app/services/absence_service.py`, `backend/app/api/v1/absences`.

Backend
- CRUD demandes d'absence, approvals, rejects avec motif.
- Notification fan-out vers managers + org admins via `_notify_absence_submission`.

Frontend
- Pages + modals d'absence, appels via `apiClient`.

Tests
- `tests/test_absence_service.py` (approve/reject flows).

---

## Approvals (validations)
Responsabilité : `backend/app/services/*_service.py` (timesheet + absence), `backend/app/api/v1/approvals`.

Fonctions
- Créer une approbation, associer des entrées, notifier, changer statut.

Frontend
- UI manager : liste des approbations, actions approve/reject.

---

## Notifications / In-app
Responsabilité : `backend/app/models/notification.py`, helpers `run_create_in_app_notification`.

Fonctions
- Stockage des notifications en base (audit), distribution (manager + admins). Utilisé par timesheet/absence/service.

Frontend
- UI : badge notifications, liste, links.

---

## Projets & Clients
Responsabilité : `backend/app/api/v1/projects`, `.../clients`.

Frontend
- Modals : `CreateProjectModal.tsx`, `QuickProjectModal.tsx`, `ClientDetailModal.tsx`, `AdminClientsPage.tsx`.
- Dark-mode fixes appliqués aux labels, inputs, cards.

---

## Compétences / Skill Rates
- Backend endpoints CRUD pour skill rates.
- Frontend hooks `frontend-v2/src/features/skillRates/hooks.ts`: invalidate both `['skill-rates']` and `['manager-skill-rates']` après modifications.

---

## Invoicing / Finance
- Endpoints et services d'invoicing, licences et facturation.
- Tests : `tests/test_invoicing.py`, `tests/test_finance_license.py`.

---

## Reporting
- APIs et pages dédiées (reports), background tasks possible.

---

## UI / Composants réutilisables
- `frontend-v2/src/components/modals/*` : modals partagés.
- `frontend-v2/src/lib/apiClient.ts` : wrapper fetch/axios central, lit `import.meta.env.VITE_API_URL`.
- `frontend-v2/src/lib/tokenStore.ts` et `authStore.ts` pour gestion tokens.

---

## API client et hooks
- `apiClient` lit `VITE_API_URL` (par défaut `/api/v1`) ; en multi-env on construit l'image avec `VITE_API_URL=/uat/api/v1` ou `VITE_API_URL=http://host:8001`.
- React Query keys : conventions globaux (ex: `['timesheet-week', week]`, `['skill-rates']`).

---

## Tests
- Backend : `pytest` — dossier `backend/tests/` (unit + integration). Utiliser `.venv` Python.
- Frontend : `npm test` (si présent). `tsc --noEmit` pour vérif TypeScript.

---

## Déploiement & environnements
- `docker-compose.yml` : stack de base (postgres, redis, backend, celery, frontend).
- `docker-compose.uat.yml` : override paramétrable par `ENV_NAME`, `FRONTEND_HOST_PORT`, `BACKEND_HOST_PORT`, `DB_NAME`.
- `docker-compose.proxy.yml` + `nginx-proxy/nginx.conf` : router path-based (`/dev/`, `/uat/`, `/uat2/`).
- Build frontend : injecter `VITE_BASE_PATH` et `VITE_API_URL` au build.

---

## CI/CD (GitHub Actions)
- `test` job : tests backend + build frontend (type-check + build).
- `build-ovh-dev-images` : push dev images and SSH deploy to OVH (dev stack).
- `deploy-uat` : PR merge dev→uat triggers deploy to UAT; also `workflow_dispatch` to deploy `uat2/uat3`.
- Secrets utilisés : `OVH_HOST`, `OVH_USER`, `OVH_SSH_KEY`, `OVH_REPO_TOKEN`, `POSTGRES_PASSWORD`, optional `SECRET_KEY`.

---

## Variables d'environnement importantes
- `DATABASE_URL` (SQLAlchemy async)
- `REDIS_URL`
- `FRONTEND_URL`
- `APP_ENV` (dev/uat/prod)
- `SECRET_KEY` (JWT)
- Frontend build-time : `VITE_BASE_PATH`, `VITE_API_URL`

---

## Commands utiles (local)
```bash
# Backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r backend/requirements-dev.txt
cd backend
python -m pytest tests/

# Frontend
cd frontend-v2
npm ci
npx tsc --noEmit      # type-check
npm run build         # build

# Docker compose dev
docker compose up -d

# Start proxy
docker compose -f docker-compose.proxy.yml up -d
```

---

## Runbook rapide pour déployer une évolution sur OVH
1. Commit & push sur `dev` (le job `build-ovh-dev-images` s'exécute automatiquement).
2. Pour UAT : ouvrir PR `dev -> uat` et merger → `deploy-uat` se déclenche. Pour uat2/uat3 utiliser `workflow_dispatch` et choisir l'env.
3. Monitorer Actions et vérifier `http://SERVER_IP/<env>/health`.

---

## Prochaines améliorations suggérées
- Documenter schémas détaillés (Pydantic models) pour chaque endpoint (auto-générer via OpenAPI).
- Ajouter un README par domaine (`backend/README.md`, `frontend-v2/README.md`).
- Ajout d'un script de sanity-check pour le proxy (vérif mapping / ports).

---

Fin — demander si tu veux la version PDF, un README simplifié par rôle (dev / ops / QA), ou la génération automatique des endpoints OpenAPI dans `docs/`.

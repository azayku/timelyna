# Spec 15 — Tasks Breakdown

## Overview
32 tâches atomiques réparties en 2 voies parallèles (Backend / Frontend).

**Assignation:**
- Tasks 15.01–15.18 → `dev-backend-timesheet`
- Tasks 15.19–15.32 → `dev-frontend-timesheet`

---

## Backend Tasks (Agent: dev-backend-timesheet)

### 🔹 Voie B1: Exception Logging

#### 15.01 — Fix approval_service.py exceptions
- **File:** `backend/app/services/approval_service.py`
- **Action:** Lire le fichier entièrement, trouver tous les `except Exception: pass`, remplacer par `logger.warning(..., exc_info=True)`
- **Estimate:** 30min
- **AC:** Aucun `except: pass` restant dans ce fichier

#### 15.02 — Fix timesheet_service.py exceptions
- **File:** `backend/app/services/timesheet_service.py`
- **Action:** Lire le fichier, trouver `except Exception: pass`, remplacer par log warning
- **Estimate:** 20min
- **AC:** Aucun `except: pass` restant

#### 15.03 — Fix auth_service.py exceptions
- **File:** `backend/app/services/auth_service.py`
- **Action:** Lire le fichier, trouver `except Exception: pass`, remplacer par log warning
- **Estimate:** 30min
- **AC:** Aucun `except: pass` restant

#### 15.04 — Fix email_template_service.py exceptions
- **File:** `backend/app/services/email_template_service.py`
- **Action:** Lire le fichier, trouver `except Exception: pass`, remplacer par log warning
- **Estimate:** 15min
- **AC:** Aucun `except: pass` restant

#### 15.05 — Fix license_service.py exceptions
- **File:** `backend/app/services/license_service.py`
- **Action:** Lire le fichier, trouver `except Exception: pass`, remplacer par log warning
- **Estimate:** 15min
- **AC:** Aucun `except: pass` restant

#### 15.06 — Fix project_availability_service.py exceptions
- **File:** `backend/app/services/project_availability_service.py`
- **Action:** Lire le fichier, trouver `except Exception: pass`, remplacer par log warning
- **Estimate:** 20min
- **AC:** Aucun `except: pass` restant

#### 15.07 — Verify backend imports non-regression
- **File:** All modified services
- **Action:** Tester `python -c "from app.services.XXX import XXX"` pour chaque service modifié
- **Estimate:** 10min
- **AC:** Tous les imports fonctionnent

---

### 🔹 Voie B2: N+1 Query Fix

#### 15.08 — Analyze timesheet_service.py query patterns
- **File:** `backend/app/services/timesheet_service.py`
- **Action:** Lire tout le fichier, identifier les boucles qui font des requêtes DB par ID
- **Estimate:** 15min
- **AC:** Liste complète des méthodes concernées (minimum 2)

#### 15.09 — Fix get_draft_entries() N+1
- **File:** `backend/app/services/timesheet_service.py`
- **Action:** Remplacer la boucle project load par un `select().where(...in_(project_ids))`
- **Estimate:** 30min
- **AC:** Méthode charge tous les projets en 1 query

#### 15.10 — Fix get_all_entries() N+1
- **File:** `backend/app/services/timesheet_service.py`
- **Action:** Remplacer la boucle project load par un bulk load IN
- **Estimate:** 30min
- **AC:** Méthode charge tous les projets en 1 query

#### 15.11 — Add SQLAlchemy imports if needed
- **File:** `backend/app/services/timesheet_service.py`
- **Action:** Vérifier que `from sqlalchemy import select` est présent, l'ajouter sinon
- **Estimate:** 5min
- **AC:** Import présent, pas de duplication

#### 15.12 — Verify timesheet_service imports
- **File:** `backend/app/services/timesheet_service.py`
- **Action:** `python -c "from app.services.timesheet_service import TimesheetService"`
- **Estimate:** 5min
- **AC:** Import fonctionne

---

### 🔹 Voie B3: Response Model Typing

#### 15.13 — Read existing timesheet schemas
- **File:** `backend/app/schemas/timesheet.py`
- **Action:** Lire le fichier pour voir les schémas existants
- **Estimate:** 10min
- **AC:** Comprendre la structure actuelle

#### 15.14 — Create TimesheetEntryResponse schema
- **File:** `backend/app/schemas/timesheet.py`
- **Action:** Ajouter `TimesheetEntryResponse` avec champs : entry_id, employee_id, project_id, work_date, hours_worked, description, status, created_at
- **Estimate:** 20min
- **AC:** Schéma créé, `model_config = ConfigDict(from_attributes=True)`

#### 15.15 — Read timesheet.py routes
- **File:** `backend/app/api/v1/timesheet.py`
- **Action:** Lire le fichier pour identifier toutes les routes GET qui retournent des lists
- **Estimate:** 10min
- **AC:** Liste des routes à typer

#### 15.16 — Add response_model to GET routes
- **File:** `backend/app/api/v1/timesheet.py`
- **Action:** Ajouter `response_model=list[TimesheetEntryResponse]` aux routes GET concernées
- **Estimate:** 15min
- **AC:** Au moins 2 routes typées

#### 15.17 — Import schema in routes
- **File:** `backend/app/api/v1/timesheet.py`
- **Action:** Ajouter `from app.schemas.timesheet import TimesheetEntryResponse` en haut du fichier
- **Estimate:** 5min
- **AC:** Import présent

#### 15.18 — Verify backend response models
- **File:** `backend/app/api/v1/timesheet.py`
- **Action:** Démarrer uvicorn, aller sur `/docs`, vérifier que les schémas apparaissent correctement
- **Estimate:** 10min
- **AC:** OpenAPI doc affiche `TimesheetEntryResponse[]` pour les routes GET

---

## Frontend Tasks (Agent: dev-frontend-timesheet)

### 🔹 Voie F1: Error Boundary

#### 15.19 — Create ErrorBoundary component
- **File:** `frontend-v2/src/components/ErrorBoundary.tsx` (nouveau)
- **Action:** Créer le class component avec getDerivedStateFromError et componentDidCatch
- **Estimate:** 30min
- **AC:** Composant compile, affiche fallback UI avec icône AlertTriangle

#### 15.20 — Add fallback UI to ErrorBoundary
- **File:** `frontend-v2/src/components/ErrorBoundary.tsx`
- **Action:** Ajouter le JSX du fallback (icône, message, bouton Réessayer)
- **Estimate:** 15min
- **AC:** Tailwind classes correctes, dark mode compatible

#### 15.21 — Read Layout.tsx structure
- **File:** `frontend-v2/src/components/Layout.tsx`
- **Action:** Lire le fichier pour trouver où se situe `<Outlet />`
- **Estimate:** 5min
- **AC:** Comprendre la structure

#### 15.22 — Wrap Outlet with ErrorBoundary in Layout
- **File:** `frontend-v2/src/components/Layout.tsx`
- **Action:** Importer ErrorBoundary, wrapper `<Outlet />` avec `<ErrorBoundary><Outlet /></ErrorBoundary>`
- **Estimate:** 10min
- **AC:** ErrorBoundary wraps Outlet

#### 15.23 — TypeScript compile check (ErrorBoundary)
- **File:** `frontend-v2/`
- **Action:** Lancer `npx tsc --noEmit --project tsconfig.app.json`
- **Estimate:** 5min
- **AC:** Exit 0, aucune erreur TS

---

### 🔹 Voie F2: Delete Confirmations

#### 15.24 — Read AdminUsersPage.tsx
- **File:** `frontend-v2/src/pages/AdminUsersPage.tsx`
- **Action:** Lire le fichier entièrement, identifier tous les boutons/handlers DELETE
- **Estimate:** 15min
- **AC:** Liste des handlers DELETE à modifier

#### 15.25 — Add Swal confirmation to DELETE handlers
- **File:** `frontend-v2/src/pages/AdminUsersPage.tsx`
- **Action:** Pour chaque DELETE sans confirmation, ajouter `await Swal.fire(...)` avant `.mutate()`
- **Estimate:** 30min
- **AC:** Tous les DELETE ont une confirmation Swal

#### 15.26 — Verify Swal import in AdminUsersPage
- **File:** `frontend-v2/src/pages/AdminUsersPage.tsx`
- **Action:** Vérifier que `import Swal from 'sweetalert2'` est présent en haut du fichier
- **Estimate:** 5min
- **AC:** Import présent

#### 15.27 — TypeScript compile check (AdminUsersPage)
- **File:** `frontend-v2/`
- **Action:** Lancer `npx tsc --noEmit --project tsconfig.app.json`
- **Estimate:** 5min
- **AC:** Exit 0

---

### 🔹 Voie F3: Empty States

#### 15.28 — Read ValidationHistoryPage.tsx
- **File:** `frontend-v2/src/pages/ValidationHistoryPage.tsx`
- **Action:** Lire le fichier, identifier où la liste est rendue (.map)
- **Estimate:** 10min
- **AC:** Comprendre la structure de la liste

#### 15.29 — Add empty state to ValidationHistoryPage
- **File:** `frontend-v2/src/pages/ValidationHistoryPage.tsx`
- **Action:** Ajouter `{items.length === 0 && !isLoading && <EmptyState />}` avant le `.map()`
- **Estimate:** 20min
- **AC:** Empty state affiché si liste vide, icône ClipboardCheck

#### 15.30 — Read ApprovalsPage.tsx
- **File:** `frontend-v2/src/pages/ApprovalsPage.tsx`
- **Action:** Lire le fichier, identifier où la liste est rendue
- **Estimate:** 10min
- **AC:** Comprendre la structure

#### 15.31 — Add empty state to ApprovalsPage
- **File:** `frontend-v2/src/pages/ApprovalsPage.tsx`
- **Action:** Ajouter `{items.length === 0 && !isLoading && <EmptyState />}` avant le `.map()`
- **Estimate:** 20min
- **AC:** Empty state affiché si liste vide, icône Inbox

#### 15.32 — TypeScript compile check (Empty states)
- **File:** `frontend-v2/`
- **Action:** Lancer `npx tsc --noEmit --project tsconfig.app.json`
- **Estimate:** 5min
- **AC:** Exit 0

---

## Dependencies Graph

```
Backend Track (parallèle)
├── B1 (15.01–15.07) → Voie indépendante
├── B2 (15.08–15.12) → Voie indépendante
└── B3 (15.13–15.18) → Voie indépendante

Frontend Track (parallèle)
├── F1 (15.19–15.23) → Voie indépendante
├── F2 (15.24–15.27) → Voie indépendante
└── F3 (15.28–15.32) → Voie indépendante
```

**Parallelization:**
- Backend track et Frontend track sont 100% indépendants → lancer les 2 agents en parallèle
- Au sein de chaque track, les 3 voies (B1/B2/B3 et F1/F2/F3) sont indépendantes mais un agent peut les traiter séquentiellement

---

## Total Estimates
- **Backend:** 4h 10min
- **Frontend:** 3h 15min
- **Validation:** 1h
- **Total:** ~8h (1 jour de dev)

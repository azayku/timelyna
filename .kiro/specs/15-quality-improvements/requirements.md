# Spec 15 — Quality Improvements & Technical Hygiene

## Overview
Cette spec adresse 6 problèmes qualité critiques identifiés par audit de code, répartis entre backend (exceptions, performances, typage) et frontend (résilience, UX, accessibilité).

**Scope:** 64 problèmes recensés, regroupés en 6 requirements prioritaires.

**Valeur métier:** Réduction des bugs silencieux, amélioration de la debuggabilité, meilleure UX sur erreurs et empty states.

**Non-scope:** Refactoring architectural, ajout de features, migration v1→v2.

---

## Requirements

### REQ-01: Exception Logging (Backend)
**Priority:** HIGH  
**Persona:** DevOps, Support  
**Rationale:** Les exceptions avalées silencieusement (`except Exception: pass`) masquent des bugs et rendent le debugging impossible.

**Acceptance Criteria:**
- [ ] Aucun `except Exception: pass` ne subsiste dans `backend/app/services/`
- [ ] Tous les except blocs qui n'avaient que `pass` loggent maintenant avec `logger.warning(..., exc_info=True)`
- [ ] Les services suivants sont corrigés :
  - `approval_service.py` (4+ occurrences)
  - `timesheet_service.py` (2+ occurrences)
  - `auth_service.py` (4+ occurrences)
  - `email_template_service.py` (2+ occurrences)
  - `license_service.py` (2+ occurrences)
  - `project_availability_service.py` (3+ occurrences)
- [ ] Les tests backend existants passent toujours (non régressif)

**Files:**
- `backend/app/services/approval_service.py`
- `backend/app/services/timesheet_service.py`
- `backend/app/services/auth_service.py`
- `backend/app/services/email_template_service.py`
- `backend/app/services/license_service.py`
- `backend/app/services/project_availability_service.py`

---

### REQ-02: N+1 Query Fix (Backend)
**Priority:** HIGH  
**Persona:** Tous (performance)  
**Rationale:** Les boucles qui font une requête DB par ID causent des latences de 500ms–2s sur les endpoints timesheet.

**Acceptance Criteria:**
- [ ] `timesheet_service.get_draft_entries()` charge tous les projets en 1 seule requête IN
- [ ] `timesheet_service.get_all_entries()` charge tous les projets en 1 seule requête IN
- [ ] Aucune nouvelle boucle N+1 introduite dans le service
- [ ] Les tests backend existants passent toujours

**Performance Target:**
- GET `/api/v1/timesheet-entries?status=draft&employee_id=X` doit retourner en < 200ms (actuellement ~800ms pour 20 entries)

**Files:**
- `backend/app/services/timesheet_service.py`

---

### REQ-03: Response Model Typing (Backend)
**Priority:** MEDIUM  
**Persona:** Frontend Dev, API consumers  
**Rationale:** Les routes GET timesheet retournent `list` générique, ce qui empêche la validation Pydantic et la génération d'OpenAPI correcte.

**Acceptance Criteria:**
- [ ] Un schéma `TimesheetEntryResponse` existe dans `backend/app/schemas/timesheet.py`
- [ ] Ce schéma couvre au minimum : `entry_id`, `employee_id`, `project_id`, `work_date`, `hours_worked`, `description`, `status`, `created_at`
- [ ] Les routes GET dans `backend/app/api/v1/timesheet.py` utilisent `response_model=list[TimesheetEntryResponse]`
- [ ] La doc OpenAPI `/docs` affiche le schéma correctement

**Files:**
- `backend/app/schemas/timesheet.py`
- `backend/app/api/v1/timesheet.py`

---

### REQ-04: Error Boundary (Frontend)
**Priority:** HIGH  
**Persona:** Tous  
**Rationale:** Les erreurs React non catchées affichent une page blanche, pas de fallback UI.

**Acceptance Criteria:**
- [ ] Un composant `ErrorBoundary.tsx` existe dans `frontend-v2/src/components/`
- [ ] Il utilise `componentDidCatch` et affiche un fallback avec icône + message + bouton "Réessayer"
- [ ] Il est déployé dans `Layout.tsx` autour de `<Outlet />`
- [ ] Le TypeScript compile sans erreur (`tsc --noEmit`)
- [ ] Tester manuellement : jeter une erreur dans un composant enfant → le boundary l'attrape

**Files:**
- `frontend-v2/src/components/ErrorBoundary.tsx` (nouveau)
- `frontend-v2/src/components/Layout.tsx`

---

### REQ-05: Delete Confirmations (Frontend)
**Priority:** HIGH  
**Persona:** Admin, Manager  
**Rationale:** Les boutons DELETE dans AdminUsersPage n'ont pas de confirmation, risque de suppression accidentelle.

**Acceptance Criteria:**
- [ ] Tous les handlers `onClick` qui appellent une mutation DELETE dans `AdminUsersPage.tsx` affichent une confirmation Swal AVANT de mutater
- [ ] Le dialog Swal affiche : titre, message "action irréversible", boutons Confirmer/Annuler
- [ ] Les suppressions existantes qui ont déjà une confirmation ne sont PAS modifiées
- [ ] Le TypeScript compile sans erreur

**Files:**
- `frontend-v2/src/pages/AdminUsersPage.tsx`

---

### REQ-06: Empty States (Frontend)
**Priority:** MEDIUM  
**Persona:** Tous  
**Rationale:** Les listes vides affichent juste un tableau sans rows, pas de message explicatif.

**Acceptance Criteria:**
- [ ] `ValidationHistoryPage.tsx` affiche un empty state si `items.length === 0 && !isLoading`
- [ ] `ApprovalsPage.tsx` affiche un empty state si `items.length === 0 && !isLoading`
- [ ] L'empty state contient : icône (lucide-react), message i18n "Aucune donnée", style centré
- [ ] Le TypeScript compile sans erreur

**Files:**
- `frontend-v2/src/pages/ValidationHistoryPage.tsx`
- `frontend-v2/src/pages/ApprovalsPage.tsx`

---

## Success Metrics
- **Backend:** Tests pytest passent, aucun `except Exception: pass` détectable par grep
- **Frontend:** `tsc --noEmit` exit 0, ErrorBoundary testable manuellement
- **Performance:** GET draft entries < 200ms (actuellement ~800ms)

## Timeline
- Spec création: 1h
- Backend fixes: 2–3h
- Frontend fixes: 2–3h
- Validation: 1h
- **Total:** ~1 jour de dev

## Dependencies
Aucune dépendance externe. Les deux voies (backend / frontend) sont parallélisables.

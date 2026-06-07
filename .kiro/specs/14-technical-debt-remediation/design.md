# Design Document — Spec 14 : Remédiation de la dette technique

## Overview

Cette spec est purement corrective. Elle ne modifie aucun comportement fonctionnel visible
par l'utilisateur final. Toutes les modifications sont internes : propagation des paramètres,
isolation des couches, consolidation des utilitaires, nettoyage.

L'approche est **chirurgicale** : chaque correction est indépendante et peut être livrée
séparément sans risque pour les autres modules.

---

## Architecture cible

### Backend — propagation org_id

**Avant**
```
Router → Service(db)
              └─ SELECT OrgSettings WHERE org_id = 1  ← hardcodé
```

**Après**
```
Router → Service(db, org_id=current_user["org_id"])
              └─ SELECT OrgSettings WHERE org_id = :org_id  ← dynamique
```

Le changement est localisé dans chaque router (extraction de `org_id`) et dans les
signatures de méthodes de services concernés. Aucun modèle de données n'est modifié.

---

### Backend — isolation SQL dans les repositories

**Avant**
```
FinanceDashboardService._get_kpis()
    └─ await self.db.execute(text("SELECT TO_CHAR(...)"))  ← SQL PG direct
```

**Après**
```
FinanceDashboardService.get_dashboard()
    └─ self.repo.get_kpis(start, end)   ← appel repository

FinanceDashboardRepository.get_kpis(start, end)
    └─ await self.db.execute(text("SELECT TO_CHAR(...)"))  ← SQL isolé ici
```

Un nouveau fichier `app/repositories/finance_dashboard_repository.py` est créé.
`FinanceDashboardService` passe de 250 lignes à ~80 lignes (logique pure, plus de SQL).

---

### Backend — utilitaire period partagé

**Nouveau fichier** : `app/utils/period.py`

```python
def parse_period(period: str) -> tuple[date, date]:
    """Convertit un code de période en (start, end) dates."""
    ...
```

Les deux copies dans `reporting_service.py` et `finance_dashboard_service.py` sont
remplacées par un import.

---

### Backend — instance Celery unique

**Avant**
```
app/core/celery_app.py     → crée celery_app (avec Beat schedule)
app/tasks/email_tasks.py   → crée celery_app (sans Beat schedule, sans include)
```

**Après**
```
app/core/celery_app.py     → crée celery_app (avec Beat schedule, include complet)
app/tasks/email_tasks.py   → from app.core.celery_app import celery_app
app/tasks/*.py             → from app.core.celery_app import celery_app
```

Le nom de l'instance exportée depuis `celery_app.py` devient `celery_app` (variable
au niveau module) en plus de la factory `create_celery_app()` conservée pour les tests.

---

### Backend — Response Models

Nouveaux schémas dans `app/schemas/` :

```
app/schemas/
├── timesheet.py        + WeekResponse, EntryResponse, SubmitWeekResponse
├── finance.py          + FinanceDashboardResponse, KpiResponse, KpiTrendResponse
├── reporting.py        + PersonalStatsResponse, TeamStatsResponse (nouveau fichier)
└── admin.py            + UserListResponse, UserDetailResponse (nouveau fichier)
```

Les endpoints concernés ajoutent `response_model=XxxResponse` dans le décorateur.

---

### Backend — Alembic

Structure :
```
backend/
├── alembic.ini
├── alembic/
│   ├── env.py          ← lit DATABASE_URL via app.core.config
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial_schema.py
```

`env.py` utilise `run_migrations_online()` async avec `asyncpg`.
`entrypoint.sh` ajoute `alembic upgrade head` avant `uvicorn`.

---

### Backend — nettoyage

Fichiers à supprimer de `backend/` :
- `check_gianni_data.sql`, `fix_gianni_manager.sql`, `setup_gianni_*.sql`, `setup_gianni_*.py`
- `check_week18_status.sql`, `check_week19_achille.sql`, `check_absences.sql`
- `check_and_reset_user.py`, `check_backend_status.py`, `check_email.py`
- `list_users.py`, `update_email.py`, `assign_projects_achille.py`
- `test_manager_api.py`, `test_manager_data.py`

Fichiers markdown de sessions à déplacer de la racine vers `docs/sessions/` :
- `SESSION_*.md`, `*_COMPLETE.md`, `*_FIXES*.md`, `SPEC_AUDIT.md`, etc.

---

### Frontend — découplage navigation

**Avant**
```ts
// apiClient.ts
if (res.status === 401) {
  window.location.href = '/login'   ← effet de bord dans lib
}
```

**Après**
```ts
// apiClient.ts
if (res.status === 401) {
  window.dispatchEvent(new CustomEvent('auth:unauthorized'))
}

// authStore.ts — dans l'init du store
window.addEventListener('auth:unauthorized', () => {
  useAuthStore.getState().clearUser()
  window.location.href = '/login'
})
```

Ce changement permet de tester `apiClient` sans mock de `window.location`.

---

### Frontend — organisation des fichiers pages

**Avant**
```
pages/AdminUsersPage.tsx       ← re-export vide de components/AdminUsersPage
components/AdminUsersPage.tsx  ← implémentation réelle (mauvais endroit)
```

**Après**
```
pages/AdminUsersPage.tsx       ← implémentation réelle (déplacée)
components/                    ← uniquement composants réutilisables
```

---

### Frontend — hooks timesheet dans MyTimesheetsPage

`MyTimesheetsPage` contient des `useMutation` directs qui recréent la logique déjà
présente dans `features/timesheet/hooks.ts`. La correction utilise `useUpdateEntry`
et `useDeleteEntry` depuis les hooks, garantissant l'invalidation de cache via
`queryKey: ['timesheet-week', week]`.

---

## Composants modifiés

### Backend

| Fichier | Type de modification |
|---------|---------------------|
| `app/services/timesheet_service.py` | Paramètre `org_id`, imports en tête, validation projet, messages FR |
| `app/services/absence_service.py` | Paramètre `org_id` |
| `app/services/approval_service.py` | Paramètre `org_id` |
| `app/services/reporting_service.py` | Import `parse_period` depuis utils |
| `app/services/finance_dashboard_service.py` | Import `parse_period`, délégation au repository |
| `app/repositories/finance_dashboard_repository.py` | **Nouveau** — SQL PostgreSQL isolé |
| `app/utils/period.py` | **Nouveau** — fonction `parse_period` partagée |
| `app/core/celery_app.py` | Export `celery_app` au niveau module |
| `app/tasks/email_tasks.py` | Import `celery_app` depuis `app/core/celery_app` |
| `app/tasks/notification_tasks.py` | Import `celery_app` depuis `app/core/celery_app` |
| `app/tasks/invoice_tasks.py` | Import `celery_app` depuis `app/core/celery_app` |
| `app/tasks/deactivation_tasks.py` | Import `celery_app` depuis `app/core/celery_app` |
| `app/schemas/timesheet.py` | Ajout `WeekResponse`, `EntryResponse`, `SubmitWeekResponse` |
| `app/schemas/finance.py` | **Nouveau** — `FinanceDashboardResponse`, `KpiResponse` |
| `app/schemas/reporting.py` | **Nouveau** — `PersonalStatsResponse`, `TeamStatsResponse` |
| `app/api/v1/timesheet.py` | Ajout `response_model` |
| `app/api/v1/finance.py` | Ajout `response_model` |
| `app/api/v1/admin.py` | Ajout `response_model` |
| `alembic/` | **Nouveau** — init + migration initiale |
| `entrypoint.sh` | Ajout `alembic upgrade head` |

### Frontend

| Fichier | Type de modification |
|---------|---------------------|
| `src/lib/apiClient.ts` | Remplace `window.location.href` par `CustomEvent` |
| `src/lib/authStore.ts` | Écoute `auth:unauthorized` |
| `src/lib/themeStore.ts` | Factory sécurisée pour `window.matchMedia` |
| `src/pages/AdminUsersPage.tsx` | Reçoit l'implémentation réelle (depuis `components/`) |
| `src/components/AdminUsersPage.tsx` | Supprimé (fusionné dans `pages/`) |
| `src/pages/MyTimesheetsPage.tsx` | Utilise `useUpdateEntry` / `useDeleteEntry` |
| Composants avec `t: any` | Typage avec `TFunction` de `react-i18next` |

---

## Décisions de conception

### Pourquoi un événement custom plutôt qu'un callback ?

Un callback créerait une dépendance circulaire (`apiClient` → `authStore` → `apiClient`).
L'événement DOM est le mécanisme de découplage natif du browser, sans dépendances.
La solution actuelle (import dynamique) fonctionne mais est moins testable.

### Pourquoi créer `finance_dashboard_repository.py` plutôt que `reporting_repository.py` ?

`ReportingRepository` existe déjà et couvre les stats générales. Les queries finance
(P&L, CA, marges) sont un domaine distinct avec leur propre cycle de vie.
Un second repository spécialisé est plus cohérent avec la division du domaine.

### Pourquoi conserver `create_celery_app()` factory ?

Les tests peuvent créer une instance Celery isolée via la factory sans polluer l'instance
globale. L'instance module-level `celery_app` sert à la production et aux workers.

### Alembic : migration initiale ou autogenerate ?

`autogenerate` depuis les modèles SQLAlchemy est utilisé pour la migration `0001`.
Les scripts `migrate_*.py` existants documentent des deltas — leurs DDL sont portés
manuellement dans la migration initiale en vérifiant contre le schéma réel en prod.

---

## Risques et mitigations

| Risque | Probabilité | Mitigation |
|--------|-------------|------------|
| Casse d'un endpoint après ajout `response_model` | Moyenne | Vérifier avec les tests d'intégration existants avant merge |
| Migration `0001` diverge du schéma prod | Faible | Comparer avec `alembic check` avant déploiement |
| Suppression des scripts de debug bloque un process non documenté | Faible | Review avec l'équipe avant suppression définitive |
| Propagation `org_id` oubliée dans un service non listé | Moyenne | Grep `org_id == 1` après correction et vérifier les 0 résultats |

# Requirements Document — Spec 14 : Remédiation de la dette technique

## Introduction

Suite à l'audit de code de juin 2026, cette spec adresse les failles identifiées sur
les axes suivants :
- **Multi-tenancy** : `org_id` hardcodé à `1` dans les services métier
- **Isolation de la couche données** : SQL PostgreSQL-spécifique dans les services
- **Cohérence de l'infrastructure Celery** : double instance Celery
- **Qualité du code** : DRY violations, imports locaux, double validation, messages bilingues
- **Contrat d'API** : absence de modèles de réponse Pydantic sur les endpoints
- **Gestion des migrations** : scripts ad-hoc remplacés par Alembic
- **Nettoyage du repo** : scripts de debug et SQL one-shot commités
- **Frontend** : typage incomplet, navigation couplée au client HTTP, organisation des fichiers

Les corrections sont **backward-compatible** : aucune table n'est supprimée, aucune API
existante n'est cassée.

---

## Glossaire

- **org_id** : identifiant de l'organisation courante, disponible dans le JWT de chaque utilisateur authentifié.
- **multi-tenant** : capacité du système à isoler correctement les données de chaque organisation.
- **DRY** (Don't Repeat Yourself) : principe d'unicité de la logique dans le code.
- **Alembic** : outil de migration de schéma pour SQLAlchemy.
- **Celery Beat** : planificateur de tâches périodiques de Celery.
- **Feature slice** : organisation du code frontend par domaine fonctionnel (`features/timesheet/`, etc.).
- **Response Model** : schéma Pydantic déclaré sur un endpoint FastAPI, validant la réponse sortante et alimentant OpenAPI.

---

## Requirements

### Requirement 1 — Multi-tenancy : propagation de l'org_id

**User Story :** En tant qu'employé d'une organisation autre que l'org 1, je veux que les règles de ma propre organisation (heures max, paramètres) s'appliquent à mes saisies, afin que la configuration de mon entreprise soit respectée.

#### Acceptance Criteria

1. WHEN un employé authentifié crée une saisie de temps, THE System SHALL charger les `OrgSettings` correspondant à son `org_id` (extrait du JWT) et non à `org_id = 1`.
2. WHEN un service métier a besoin des paramètres d'organisation, THE System SHALL recevoir l'`org_id` via son constructeur ou ses paramètres de méthode — jamais via une constante hardcodée.
3. THE System SHALL propager l'`org_id` du JWT dans tous les services suivants : `TimesheetService`, `AbsenceService`, `ApprovalService`, `ReportingService`.
4. IF l'`org_id` du JWT ne correspond à aucune ligne dans `org_settings`, THEN THE System SHALL appliquer des valeurs par défaut (`max_hours_per_day=16`, `standard_hours_per_day=8`) sans retourner d'erreur.
5. THE router SHALL extraire `org_id` depuis `current_user` et le passer explicitement au service concerné.

---

### Requirement 2 — Isolation de la couche données : repositories pour les requêtes SQL complexes

**User Story :** En tant que développeur, je veux que les requêtes SQL complexes soient isolées dans la couche repository, afin que les services restent indépendants du dialecte SQL utilisé.

#### Acceptance Criteria

1. THE System SHALL déplacer toutes les requêtes `text(...)` PostgreSQL-spécifiques de `FinanceDashboardService` vers `FinanceDashboardRepository`.
2. THE `FinanceDashboardService` SHALL appeler uniquement des méthodes du repository — aucune instruction SQL directe ne doit subsister dans le service.
3. THE repository SHALL isoler les fonctions PostgreSQL (`TO_CHAR`, `DATE_TRUNC`, `INTERVAL`) dans des méthodes nommées (`get_kpis`, `get_monthly_revenue`, `get_client_revenue`, `get_burn_rate`, `get_recent_invoices`, `get_overdue_invoices`).
4. THE repository SHALL être injectable (reçoit `AsyncSession` dans `__init__`), cohérent avec le pattern des autres repositories.

---

### Requirement 3 — Utilitaire partagé : parse_period

**User Story :** En tant que développeur, je veux une seule implémentation de `parse_period`, afin d'éviter la divergence entre les modules reporting et finance.

#### Acceptance Criteria

1. THE System SHALL créer un module `app/utils/period.py` exposant `parse_period(period: str) -> tuple[date, date]`.
2. THE `ReportingService` et `FinanceDashboardService` SHALL importer `parse_period` depuis `app/utils/period.py`.
3. THE `parse_period` function SHALL supporter les valeurs : `"this_month"`, `"last_month"`, `"quarter"`, `"year"`, `"all"`.
4. THE `parse_period` function SHALL être couverte par des tests unitaires.

---

### Requirement 4 — Infrastructure Celery : instance unique

**User Story :** En tant qu'opérateur, je veux que toutes les tâches Celery soient enregistrées sur la même instance applicative, afin que le Beat scheduler puisse les déclencher.

#### Acceptance Criteria

1. THE System SHALL avoir une seule instance Celery créée dans `app/core/celery_app.py` via `create_celery_app()`.
2. THE `app/tasks/email_tasks.py` SHALL importer l'instance Celery depuis `app/core/celery_app` et ne SHALL PAS créer sa propre instance `Celery(...)`.
3. ALL tasks dans `app/tasks/*.py` SHALL décorer leurs fonctions avec `@celery_app.task(...)` en utilisant l'instance importée.
4. WHEN Celery Beat démarre, ALL scheduled tasks SHALL être visibles via `celery inspect registered`.

---

### Requirement 5 — Contrat d'API : Response Models Pydantic

**User Story :** En tant que développeur frontend, je veux que les endpoints FastAPI déclarent des modèles de réponse typés, afin d'avoir une documentation OpenAPI fiable et des erreurs de contrat détectées à la compilation.

#### Acceptance Criteria

1. THE System SHALL déclarer un `response_model` Pydantic sur tout endpoint retournant actuellement `-> dict` ou `-> list`.
2. THE response models SHALL être définis dans les fichiers `app/schemas/` existants ou dans de nouveaux fichiers de schémas.
3. LES endpoints prioritaires à couvrir SHALL être : `GET /employee/timesheet/week`, `POST /employee/timesheet/entries`, `GET /admin/users`, `GET /approvals`, `GET /finance/dashboard`.
4. THE `app/schemas/timesheet.py` SHALL contenir `WeekResponse`, `EntryResponse`, et `SubmitWeekResponse`.
5. THE `app/schemas/finance.py` SHALL contenir `FinanceDashboardResponse`, `KpiResponse`.

---

### Requirement 6 — Migrations Alembic

**User Story :** En tant qu'opérateur, je veux gérer l'évolution du schéma de base de données via Alembic, afin de savoir exactement dans quel état est la DB de chaque déploiement.

#### Acceptance Criteria

1. THE System SHALL initialiser Alembic dans `backend/` avec `alembic init migrations`.
2. THE `alembic.ini` SHALL lire `DATABASE_URL` depuis les variables d'environnement (via `app/core/config.py`).
3. THE System SHALL générer une migration initiale `0001_initial_schema.py` correspondant au schéma actuel complet.
4. LES scripts `migrate_add_columns.py`, `migrate_fix_unique.py`, `migrate_spec11.py` SHALL être supprimés du repo après que leur contenu soit intégré dans les migrations Alembic.
5. THE `Dockerfile` et `entrypoint.sh` SHALL exécuter `alembic upgrade head` au démarrage avant de lancer uvicorn.

---

### Requirement 7 — Nettoyage du repository

**User Story :** En tant que développeur rejoignant le projet, je veux un repo propre sans fichiers de debug personnels, afin de comprendre rapidement la structure du projet.

#### Acceptance Criteria

1. THE repository SHALL ne plus contenir les fichiers SQL de debug spécifiques (`check_gianni_data.sql`, `fix_gianni_manager.sql`, `setup_gianni_*.sql`, `setup_gianni_*.py`, `check_week18_status.sql`, `check_week19_achille.sql`, `check_absences.sql`).
2. THE repository SHALL ne plus contenir les scripts utilitaires one-shot commités à la racine de `backend/` (`check_and_reset_user.py`, `check_backend_status.py`, `check_email.py`, `list_users.py`, `update_email.py`, `assign_projects_achille.py`, `test_manager_api.py`, `test_manager_data.py`).
3. THE `.gitignore` SHALL exclure `*.sql` en dehors du dossier `migrations/` et les scripts `check_*.py`, `fix_*.py` à la racine de `backend/`.
4. LES fichiers de documentation de session à la racine (plus de 30 fichiers `SESSION_*.md`, `*_COMPLETE.md`, etc.) SHALL être déplacés dans un dossier `docs/sessions/`.

---

### Requirement 8 — Qualité du code backend

**User Story :** En tant que développeur, je veux que le code soit cohérent et sans duplications évidentes, afin de le maintenir sans surprises.

#### Acceptance Criteria

1. THE `TimesheetService.create_entry` SHALL déplacer ses imports `from app.models...` et `from sqlalchemy...` en tête de fichier.
2. THE `TimesheetService.update_entry` double validation du statut projet (`status in ("draft"...) + status != "active"`) SHALL être remplacée par une seule condition avec un message unique en français.
3. ALL messages d'erreur dans `app/services/` SHALL être en français (suppression des messages en anglais mélangés).
4. THE `TimesheetService` SHALL exposer une méthode privée `_load_org_settings(org_id: int)` réutilisée dans `create_entry` et `update_entry`.

---

### Requirement 9 — Qualité du code frontend

**User Story :** En tant que développeur frontend, je veux un code typé et cohérent, afin de bénéficier de l'aide de TypeScript et d'éviter les régressions.

#### Acceptance Criteria

1. THE `t` parameter dans tous les composants React SHALL être typé avec `TFunction` importé depuis `react-i18next` — plus d'usage de `any`.
2. THE `apiClient.ts` SHALL supprimer la navigation `window.location.href = '/login'` et émettre un événement custom `auth:unauthorized` écouté par `authStore`.
3. THE `useAuthStore` SHALL écouter l'événement `auth:unauthorized` et déclencher `clearUser()` puis `window.location.href = '/login'`.
4. THE `themeStore.ts` SHALL initialiser `dark` dans une factory function sécurisée qui gère l'absence de `window.matchMedia` (environments sans DOM).
5. THE `pages/AdminUsersPage.tsx` (re-export vide) SHALL être supprimé ; `components/AdminUsersPage.tsx` SHALL être déplacé dans `pages/`.
6. THE `MyTimesheetsPage.tsx` SHALL utiliser `useUpdateEntry` et `useDeleteEntry` depuis `features/timesheet/hooks.ts` au lieu de `useMutation` direct.

---

### Requirement 10 — Tests de non-régression

**User Story :** En tant que développeur, je veux que les corrections soient couvertes par des tests, afin de garantir qu'elles ne régressent pas.

#### Acceptance Criteria

1. THE `app/utils/period.py` SHALL avoir une suite de tests `tests/unit/test_period_utils.py` couvrant les 5 valeurs de période.
2. THE multi-tenancy fix SHALL être couvert par un test vérifiant qu'un employé de l'org 2 charge bien les settings de l'org 2.
3. THE Celery fix SHALL être vérifié par un test d'import vérifiant qu'une seule instance Celery est utilisée dans `email_tasks`.
4. THE Response Models SHALL être vérifiés par des tests d'intégration existants mis à jour pour valider la structure de réponse.

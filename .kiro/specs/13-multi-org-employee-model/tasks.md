# Tasks — multi-org-employee-model

## Phase 1 : Migration base de données

- [x] 1.1 Créer la migration Alembic `0020_multi_org_employee_model.py`
  - Créer la table `organizations` (org_id, org_name, manager_id FK, created_at, updated_at, deleted_at)
  - Insérer la ligne par défaut (org_id=1, org_name="Organisation par défaut", manager_id=premier admin)
  - Ajouter la contrainte FK `employees.org_id → organizations.org_id`
  - Créer la table `employee_skills` avec contrainte UNIQUE (employee_id, skill_rate_id)
  - Créer la table `project_required_skills` avec contrainte UNIQUE (project_id, skill_rate_id)
  - Créer la table `employee_mutation_logs`
  - Ajouter la colonne optionnelle `org_settings.organizations_ref` (FK nullable)
  - Implémenter `downgrade()` complet

## Phase 2 : Modèles SQLAlchemy

- [x] 2.1 Créer `backend/app/models/organization.py` — modèle `Organization`
- [x] 2.2 Créer `backend/app/models/employee_skill.py` — modèle `EmployeeSkill`
- [x] 2.3 Créer `backend/app/models/project_required_skill.py` — modèle `ProjectRequiredSkill`
- [x] 2.4 Créer `backend/app/models/employee_mutation_log.py` — modèle `EmployeeMutationLog`
- [x] 2.5 Mettre à jour `backend/app/models/employee.py` — ajouter la FK `org_id → organizations`
- [x] 2.6 Mettre à jour `backend/app/models/__init__.py` — exporter les nouveaux modèles

## Phase 3 : Repositories

- [x] 3.1 Créer `backend/app/repositories/organization_repository.py`
  - `list_active()`, `get_by_id()`, `create()`, `update()`, `soft_delete()`
  - `list_by_manager(manager_id)` — pour le multi-équipes
  - `get_employee_count(org_id)` — pour la réponse enrichie
- [x] 3.2 Créer `backend/app/repositories/employee_skill_repository.py`
  - `list_by_employee(employee_id)`, `add(employee_id, skill_rate_id)`, `remove(employee_id, skill_rate_id)`
  - `get_employees_with_skills(skill_rate_ids)` — pour les suggestions
- [x] 3.3 Créer `backend/app/repositories/project_skill_repository.py`
  - `list_by_project(project_id)`, `set_skills(project_id, skills)`, `delete_by_project(project_id)`
- [x] 3.4 Créer `backend/app/repositories/mutation_log_repository.py`
  - `create(employee_id, from_org_id, to_org_id, mutated_by, reason)`, `list_by_employee(employee_id)`

## Phase 4 : Services

- [x] 4.1 Créer `backend/app/services/organization_service.py` — `OrganizationService`
  - `create_organization(org_name, manager_id)` — valide rôle manager/admin
  - `update_organization(org_id, **kwargs)`
  - `soft_delete(org_id)`
  - `list_organizations()`
- [x] 4.2 Créer `backend/app/services/mutation_service.py` — `MutationService`
  - `mutate_employee(employee_id, target_org_id, mutated_by, reason)`
  - Vérifications : org active, employé non-manager d'une org
  - Mise à jour `employees.org_id` et `employees.manager_id`
  - Insertion dans `employee_mutation_logs`
  - Déclenchement tâche Celery email notification
- [x] 4.3 Créer `backend/app/services/employee_suggestion_service.py` — `EmployeeSuggestionService`
  - `suggest_employees(project_id)` — filtre compétences + absences + chevauchements projets
  - Tri par `matching_skill_count` décroissant
- [x] 4.4 Mettre à jour `backend/app/services/approval_service.py`
  - Résoudre `manager_id` via `organizations.manager_id` à partir de `employees.org_id`
  - Retourner `no_valid_organization` si l'employé n'a pas d'org valide

## Phase 5 : Tâches Celery

- [x] 5.1 Ajouter la tâche `send_mutation_notification` dans `backend/app/tasks/email_tasks.py`
  - Envoyer un email au manager de la nouvelle organisation
  - Utiliser le template email existant ou en créer un nouveau `mutation_notification.html`

## Phase 6 : Routes API

- [x] 6.1 Ajouter les routes CRUD `/admin/organizations` dans `backend/app/api/v1/admin.py`
  - GET `/admin/organizations` — liste avec `employee_count`
  - POST `/admin/organizations` — création avec validation manager
  - GET `/admin/organizations/{id}`
  - PUT `/admin/organizations/{id}`
  - DELETE `/admin/organizations/{id}` — soft-delete
- [x] 6.2 Ajouter les routes compétences employé dans `backend/app/api/v1/admin.py`
  - GET `/admin/employees/{id}/skills`
  - POST `/admin/employees/{id}/skills`
  - DELETE `/admin/employees/{id}/skills/{skill_rate_id}`
- [x] 6.3 Ajouter les routes mutation dans `backend/app/api/v1/admin.py`
  - POST `/admin/employees/{id}/mutate`
  - GET `/admin/employees/{id}/mutation-history`
- [x] 6.4 Ajouter la route suggestions dans `backend/app/api/v1/admin.py`
  - GET `/admin/projects/{id}/suggested-employees`
- [x] 6.5 Étendre les routes projet existantes
  - POST `/admin/projects` — accepter `required_skills: list[ProjectSkillRequirement]`
  - PUT `/admin/projects/{id}` — accepter `required_skills`
  - Persister dans `project_required_skills` via `ProjectSkillRepository`

## Phase 7 : Schémas Pydantic

- [x] 7.1 Ajouter dans `backend/app/schemas/` (ou inline dans admin.py selon volume)
  - `CreateOrganizationRequest`, `UpdateOrganizationRequest`, `OrganizationResponse`
  - `AddEmployeeSkillRequest`, `EmployeeSkillResponse`
  - `MutateEmployeeRequest`, `MutationLogResponse`
  - `ProjectSkillRequirement`, `SuggestedEmployeeResponse`

## Phase 8 : Frontend — Feature organizations

- [x] 8.1 Créer `frontend/src/features/organizations/api.ts`
  - `fetchOrganizations()`, `createOrganization()`, `updateOrganization()`, `deleteOrganization()`
- [x] 8.2 Créer `frontend/src/features/organizations/hooks.ts`
  - `useOrganizations()`, `useCreateOrganization()`, `useUpdateOrganization()`, `useDeleteOrganization()`
- [x] 8.3 Créer `frontend/src/features/organizations/types.ts`
  - `Organization`, `CreateOrganizationPayload`, `UpdateOrganizationPayload`
- [x] 8.4 Créer `frontend/src/pages/AdminOrganizationsPage.tsx`
  - Tableau CRUD des organisations (nom, manager, nb employés)
  - Modal création/édition avec sélecteur de manager (filtre rôle manager/admin)
  - Confirmation soft-delete

## Phase 9 : Frontend — Compétences employé

- [x] 9.1 Créer `frontend/src/features/employees/skillsApi.ts`
  - `fetchEmployeeSkills(employeeId)`, `addEmployeeSkill()`, `removeEmployeeSkill()`
- [x] 9.2 Créer `frontend/src/components/EmployeeSkillsPanel.tsx`
  - Liste des compétences avec bouton suppression
  - Sélecteur d'ajout depuis les compétences disponibles de l'organisation
- [x] 9.3 Intégrer `EmployeeSkillsPanel` dans `frontend/src/pages/AdminUsersPage.tsx`
  - Afficher dans la fiche employé (drawer ou section dédiée)

## Phase 10 : Frontend — Mutation employé

- [x] 10.1 Créer `frontend/src/components/MutationModal.tsx`
  - Sélecteur d'organisation cible
  - Champ motif optionnel (max 500 chars)
  - Gestion des erreurs `employee_is_org_manager`, `invalid_target_organization`
- [x] 10.2 Intégrer le bouton "Muter" dans `frontend/src/pages/AdminUsersPage.tsx`
  - Visible uniquement pour les admins
  - Afficher l'historique des mutations dans la fiche employé

## Phase 11 : Frontend — Suggestions d'employés

- [x] 11.1 Créer `frontend/src/features/projects/suggestionsApi.ts`
  - `fetchSuggestedEmployees(projectId)`
- [x] 11.2 Créer `frontend/src/components/EmployeeSuggestionsPanel.tsx`
  - Liste des employés suggérés avec compétences correspondantes mises en évidence
  - Bouton "Ajouter à l'équipe" pour chaque suggestion
- [x] 11.3 Intégrer dans `frontend/src/pages/AdminProjectsPage.tsx`
  - Afficher le panel lors de la création/modification d'un projet
  - Permettre la saisie des `required_skills` lors de la création

## Phase 12 : Tests

- [x] 12.1 Créer `backend/tests/test_multi_org.py` — tests unitaires
  - Création organisation : manager valide / invalide (422 `invalid_manager`)
  - Soft-delete organisation : employés conservés
  - Ajout compétence : unicité, cohérence org (`skill_org_mismatch`)
  - Suppression compétence : `project_team_members` non affectés
  - Mutation : mise à jour org_id, manager_id, insertion log
  - Mutation bloquée : `employee_is_org_manager`
  - Mutation bloquée : org cible inactive (`invalid_target_organization`)
  - Suggestions : liste vide si aucun employé compétent
  - Suggestions : exclusion employés absents sur toute la période
  - Suggestions : exclusion employés avec chevauchement projet actif
  - Rétrocompatibilité : org_id=1 après migration, approvals.manager_id conservé
- [x] 12.2 Créer `backend/tests/test_multi_org_properties.py` — tests Hypothesis
  - P2 : Unicité (employee_id, skill_rate_id) — insertion dupliquée → erreur
  - P4 : Mutation round-trip — org_id mis à jour + log créé + manager_id synchronisé
  - P6 : Suggestions — tous les résultats ont ≥1 compétence requise
  - P7 : Suggestions — employés absents sur toute la période exclus
  - P8 : Suggestions — tri décroissant par matching_skill_count
  - P10 : Soft-delete org — employés toujours présents
  - P11 : Visibilité reporting — manager ne voit que ses organisations

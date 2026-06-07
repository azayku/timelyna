# Tasks — Spec 12c : Améliorations Employés & Projets

## US-01 — Enrichissement profil employé (adresse + date de naissance obligatoires)

- [x] **12c.1** Écrire migration `0012_employee_address_deactivation.py` : ajouter `address VARCHAR(500)` et `deactivation_scheduled_at TIMESTAMP` sur `employees`
- [x] **12c.2** Mettre à jour le modèle `Employee` avec `address` et `deactivation_scheduled_at`
- [x] **12c.3** Mettre à jour `CreateUserRequest` Pydantic : `birth_date: date` (obligatoire), `address: str` (obligatoire)
- [x] **12c.4** Ajouter validation backend : `birth_date` absent → 422, `address` absent → 422, `birth_date` dans le futur → 422
- [x] **12c.5** Mettre à jour `UserResponse` Pydantic pour inclure `address`
- [x] **12c.6** Mettre à jour `UpdateUserRequest` pour permettre la modification de `address` et `birth_date`
- [x] **12c.7** Mettre à jour le formulaire `UserModal` dans `AdminUsersPage.tsx` : champs `birth_date` (obligatoire) et `address` (textarea, obligatoire), affichage de l'âge calculé, badge orange "Désactivation le JJ/MM", modal désactivation Immédiat/Différé
- [x] **12c.8** Mettre à jour `AuthService.create_employee()` : `birth_date` obligatoire pour la génération du mot de passe par défaut
- [x] **12c.9** Unit test : création employé sans `birth_date` → 422 ; sans `address` → 422 ; `birth_date` futur → 422

## US-02 — Désactivation différée de compte

- [x] **12c.10** Implémenter `AuthService.schedule_deactivation(employee_id, scheduled_at)` : stocke la date, envoie email de prévenance si ≤ 7 jours
- [x] **12c.11** Implémenter `AuthService.cancel_scheduled_deactivation(employee_id)` : supprime `deactivation_scheduled_at`
- [x] **12c.12** Enregistrer `PUT /api/v1/admin/users/{id}/schedule-deactivation` et `DELETE /api/v1/admin/users/{id}/schedule-deactivation` dans `admin.py`
- [x] **12c.13** Créer tâche Celery `process_scheduled_deactivations()` : désactive les employés dont `deactivation_scheduled_at <= now`, révoque les tokens
- [x] **12c.14** Configurer Celery Beat pour `process_scheduled_deactivations` quotidiennement à 00h05
- [x] **12c.15** Mettre à jour `AdminUsersPage.tsx` : modal de désactivation avec choix Immédiat/Différé, DatePicker, badge orange "Désactivation le JJ/MM"
- [x] **12c.16** Integration test : `PUT /admin/users/{id}/schedule-deactivation` → `deactivation_scheduled_at` stocké
- [x] **12c.17** Unit test : `process_scheduled_deactivations` — date passée → désactivé ; date future → ignoré

## US-03 — Gestion avancée des projets (code auto, statuts, équipe, compétences)

- [x] **12c.18** Créer `backend/app/utils/project_code.py` : `generate_project_code()` (5 lettres majuscules + 4 chiffres) et `ensure_unique_project_code(db)`
- [x] **12c.19** Modifier `POST /api/v1/admin/projects` : générer automatiquement `project_code` si non fourni, vérifier l'unicité
- [x] **12c.20** Ajouter `ProjectRepository.get_by_code(code)` pour la vérification d'unicité
- [x] **12c.21** Mettre à jour le modèle `Project` : ajouter `draft` et `cancelled` aux statuts valides
- [x] **12c.22** Modifier `TimesheetService.create_entry()` : bloquer la saisie si le projet est en statut `draft` ou `planning`
- [x] **12c.23** Écrire migration `0013_skill_rates.py` : créer `skill_rates` et `project_team_members`
- [x] **12c.24** Créer modèle SQLAlchemy `SkillRate` dans `backend/app/models/skill_rate.py`
- [x] **12c.25** Créer modèle SQLAlchemy `ProjectTeamMember` dans `backend/app/models/project_team_member.py`
- [x] **12c.26** Créer `SkillRateRepository` : `list_by_org`, `create`, `update`, `delete`
- [x] **12c.27** Créer `ProjectTeamRepository` : `get_team`, `assign_member`, `remove_member`, `update_skill`
- [x] **12c.28** Enregistrer routes `GET/POST/PUT/DELETE /api/v1/admin/skill-rates` avec `require_role('admin')`
- [x] **12c.29** Implémenter `ProjectAvailabilityService.get_team_availability(start_date, end_date)` : occupation %, absences, conflits de projets
- [x] **12c.30** Enregistrer `GET /api/v1/admin/projects/{id}/team-availability` avec `require_role('admin', 'manager')`
- [x] **12c.31** Mettre à jour `InvoicingService.create_draft()` : calculer les lignes par compétence (priorité custom_rate > skill_rate > project_rate > client_rate)
- [x] **12c.32** Créer `SkillRatesPage.tsx` : tableau AG Grid des compétences avec CRUD inline
- [x] **12c.33** Mettre à jour `TeamAssignmentModal.tsx` : afficher disponibilité de chaque employé sur la période du projet, sélecteur de compétence par membre, avertissement si >80%
- [x] **12c.34** Mettre à jour `AdminProjectsPage.tsx` : badge coloré par statut (draft/planning/active/paused/completed/cancelled), code généré automatiquement (modifiable), `end_date` visible
- [x] **12c.35** Unit test : `generate_project_code` — format correct, unicité garantie
- [x] **12c.36** Unit test : `create_entry` avec projet en statut `draft` → 422

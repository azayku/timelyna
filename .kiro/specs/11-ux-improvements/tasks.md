# Tasks — UX Improvements & Operational Features

## US-01 — Correction saisie des heures

- [x] **11.1** Modifier `ProjectRepository.list_active_for_employee()` pour accepter un paramètre `reference_date: date | None` et filtrer les projets dont `start_date <= reference_date` et (`end_date IS NULL` OR `end_date >= reference_date`)
- [x] **11.2** Modifier `GET /api/v1/projects` pour accepter le query param `?date=YYYY-MM-DD` et le passer au repository
- [x] **11.3** Modifier `TimesheetEntryPage.tsx` : lire `?date=` depuis `useSearchParams()` comme date initiale (fallback `today`), remplacer `getCurrentWeek()` hardcodé
- [x] **11.4** Modifier `TimesheetWeekPage.tsx` : le bouton "Saisir des heures" navigue vers `/timesheet/entry?date=YYYY-MM-DD` en passant la date du jour sélectionné
- [x] **11.5** Modifier le hook `useProjects` pour passer la `selectedDate` en paramètre de requête
- [x] **11.6** Désactiver le formulaire de saisie sur `TimesheetEntryPage` si la date sélectionnée est dans le futur, avec message explicatif

## US-02 — Username & mot de passe automatiques

- [x] **11.7** Écrire migration Alembic `0005_add_employee_username_birthdate.py` : ajouter `username VARCHAR(50) UNIQUE`, `birth_date DATE`, `must_change_password BOOLEAN DEFAULT false`, `annual_leave_days INTEGER DEFAULT 25` sur `employees`
- [x] **11.8** Mettre à jour le modèle SQLAlchemy `Employee` avec les nouveaux champs
- [x] **11.9** Implémenter `generate_username(first_name, last_name)` dans `app/utils/username.py` : 4 lettres nom + 4 lettres prénom, minuscules, sans accents (unidecode)
- [x] **11.10** Implémenter `ensure_unique_username(base, db)` : vérifie l'unicité en DB, ajoute suffixe numérique si nécessaire
- [x] **11.11** Implémenter `generate_default_password(username, birth_date)` : `username + DDMMYYYY` si birth_date, sinon `secrets.token_urlsafe(12)`
- [x] **11.12** Modifier `AuthService.create_employee()` pour appeler les fonctions de génération, stocker `username`, `birth_date`, `must_change_password=True`
- [x] **11.13** Mettre à jour `CreateUserRequest` schema Pydantic pour inclure `birth_date: date | None`
- [x] **11.14** Mettre à jour `UserResponse` schema pour inclure `username`, `must_change_password`
- [x] **11.15** Ajouter `must_change_password` dans le payload JWT (`create_access_token`)
- [x] **11.16** Modifier le store Zustand `useAuth` : détecter `must_change_password === true` après login et rediriger vers `/change-password?forced=true`
- [x] **11.17** Modifier `ChangePasswordPage.tsx` : en mode `?forced=true`, masquer le bouton Annuler et afficher un message explicatif
- [x] **11.18** Après changement de mot de passe réussi, mettre `must_change_password=False` en DB via `AuthService.change_password()`
- [x] **11.19** Mettre à jour `AdminUsersPage.tsx` pour afficher le `username` généré dans la réponse de création (toast ou modal de confirmation)

## US-03 — Vue disponibilité des employés

- [x] **11.20** Implémenter `AvailabilityService.get_availability(start_date, end_date, department, project_id)` dans `app/services/availability_service.py`
- [x] **11.21** Créer `AvailabilityRepository` dans `app/repositories/availability_repository.py` : requêtes agrégées heures par employé/jour et absences par plage
- [x] **11.22** Enregistrer `GET /api/v1/admin/availability` avec params `start_date`, `end_date`, `department?`, `project_id?` et `require_role('admin', 'manager')`
- [x] **11.23** Créer `AvailabilityPage.tsx` : sélecteur de plage de dates (max 31j), tableau employés × jours avec cellules colorées (vert/orange/rouge)
- [x] **11.24** Créer `AvailabilityCell.tsx` : affiche heures loggées, % occupation, badge absence si applicable
- [x] **11.25** Ajouter la route `/admin/availability` dans le React Router et la sidebar admin

## US-04 — Intégration AG Grid

- [x] **11.26** Installer `ag-grid-community` et `ag-grid-react` dans `frontend/package.json`
- [x] **11.27** Créer le composant réutilisable `src/components/DataGrid.tsx` avec `AgGridReact`, `defaultColDef` (sortable, filter, resizable, floatingFilter), pagination 25 par défaut, persistance filtres dans `localStorage` via `storageKey`
- [x] **11.28** Migrer `AdminUsersPage.tsx` vers `DataGrid` : colonnes Nom, Email, Rôle, Statut, Manager, Date création
- [x] **11.29** Migrer `AdminProjectsPage.tsx` vers `DataGrid` : colonnes Nom, Code, Client, Statut, Équipe, Budget
- [x] **11.30** Migrer `AdminClientsPage.tsx` vers `DataGrid` : colonnes Nom, Email, Taux, Statut
- [x] **11.31** Migrer `ApprovalsPage.tsx` vers `DataGrid` : colonnes Employé, Semaine, Heures, Statut, Date soumission
- [x] **11.32** Migrer `SubmissionsPage.tsx` vers `DataGrid` : colonnes Semaine, Heures, Statut, Date soumission
- [x] **11.33** Migrer `InvoicesPage.tsx` vers `DataGrid` : colonnes Numéro, Client, Montant, Statut, Date
- [x] **11.34** Migrer `FinancialReportPage.tsx` vers `DataGrid` : colonnes Client, Heures, CA, Coût, Marge

## US-05 — Templates d'emails paramétrables

- [x] **11.35** Écrire migration Alembic `0007_create_email_templates.py` : table `email_templates`
- [x] **11.36** Créer modèle SQLAlchemy `EmailTemplate` dans `app/models/email_template.py`
- [x] **11.37** Implémenter `EmailTemplateService` dans `app/services/email_template_service.py` : `get_template()`, `render_template()`, `update_template()`, `send_preview()`
- [x] **11.38** Modifier `app/utils/email.py` : vérifier si un template personnalisé existe en DB avant d'utiliser le Jinja2 par défaut
- [x] **11.39** Enregistrer les routes `GET/PUT /api/v1/admin/email-templates`, `GET /api/v1/admin/email-templates/{key}` et `POST /api/v1/admin/email-templates/{key}/preview` dans `admin.py`
- [x] **11.40** Créer `EmailTemplatesPage.tsx` : liste des templates, éditeur sujet + corps HTML, aperçu iframe sandboxée, bouton test, bouton réinitialiser
- [x] **11.41** Ajouter la route `/admin/email-templates` dans le React Router et la sidebar admin

## US-06 — Rappels automatiques de saisie

- [x] **11.42** Écrire migration Alembic `0008_create_notification_logs.py` : table `notification_logs` (déjà dans schéma initial)
- [x] **11.43** Écrire migration Alembic `0009_add_timesheet_reminder_pref.py` : ajouter `timesheet_reminder_enabled BOOLEAN DEFAULT true` sur `notification_preferences` (utilise le système de types existant)
- [x] **11.44** Créer `app/tasks/reminder_tasks.py` avec tâche Celery `send_weekly_timesheet_reminders()` : employés actifs avec projets, vérifie saisies semaine précédente, exclut absences approuvées, respecte préférences, log dans `notification_logs`
- [x] **11.45** Créer tâche Celery `send_monthly_timesheet_reminders()` : semaines non soumises du mois écoulé, même logique
- [x] **11.46** Configurer schedules Celery Beat : lundi 16h00 hebdomadaire, dernier jour du mois 12h00 mensuel
- [x] **11.47** Créer template email Jinja2 `timesheet_reminder.html` avec liste semaines manquantes et lien saisie
- [x] **11.48** Mettre à jour `NotificationPreferencesPage.tsx` pour afficher le toggle "Rappels de saisie des heures" (affichage automatique via système de types)

## US-07 — Déclaration d'absences

- [x] **11.49** Écrire migration Alembic `0006_create_absences.py` : table `absences` (déjà dans schéma initial)
- [x] **11.50** Créer modèle SQLAlchemy `Absence` dans `app/models/absence.py`
- [x] **11.51** Créer `AbsenceRepository` dans `app/repositories/absence_repository.py` : `create`, `get_by_id`, `get_by_employee`, `get_pending_for_manager`, `get_by_date_range`, `update_status`
- [x] **11.52** Implémenter `AbsenceService` dans `app/services/absence_service.py` : `create()`, `approve()`, `reject()`, `cancel()`, `get_leave_balance()`
- [x] **11.53** Enregistrer routes employé dans `app/api/v1/absences.py` : `POST/GET /api/v1/employee/absences`, `DELETE /api/v1/employee/absences/{id}`
- [x] **11.54** Enregistrer routes manager : `GET /api/v1/manager/absences`, `POST /api/v1/manager/absences/{id}/approve`, `POST /api/v1/manager/absences/{id}/reject`
- [x] **11.55** Enregistrer route admin : `GET /api/v1/admin/absences` avec filtres `employee_id`, `status`, `start_date`, `end_date`
- [x] **11.56** Wirer notifications dans `AbsenceService` : notifier manager à la création, notifier employé à l'approbation/rejet
- [x] **11.57** Créer `AbsencesPage.tsx` : liste absences employé avec statut coloré, bouton "Déclarer une absence"
- [x] **11.58** Créer `AbsenceFormModal.tsx` : formulaire type (cp/maladie/autre), dates start/end, notes, validation Zod
- [x] **11.59** Créer `ManagerAbsencesPage.tsx` : absences en attente de l'équipe, boutons approuver/rejeter avec modal raison
- [x] **11.60** Ajouter routes absences dans React Router et liens sidebar (employé + manager)

## US-08 — Activation / Désactivation de compte employé

- [x] **11.61** Implémenter `AuthService.deactivate_employee(employee_id)` : passe `employment_status` à `inactive` et révoque tous les refresh tokens
- [x] **11.62** Implémenter `AuthService.activate_employee(employee_id)` : passe `employment_status` à `active`
- [x] **11.63** Enregistrer `PUT /api/v1/admin/users/{id}/deactivate` et `PUT /api/v1/admin/users/{id}/activate` dans `admin.py` avec `require_role('admin')`
- [x] **11.64** Mettre à jour `AdminUsersPage.tsx` : colonne Statut avec badge coloré, bouton toggle Désactiver/Réactiver avec modale de confirmation, filtre AG Grid sur le statut

## Tests

- [x] **11.65** Unit test : `generate_username` — noms courts, accents, collision → suffixe numérique
- [x] **11.66** Unit test : `generate_default_password` — avec et sans date de naissance
- [x] **11.67** Integration test : `POST /admin/users` → username généré, `must_change_password=True`, email envoyé
- [x] **11.68** Integration test : login avec `must_change_password=True` → flag présent dans le token
- [x] **11.69** Integration test : `PUT /admin/users/{id}/deactivate` → refresh tokens révoqués, login retourne 403
- [x] **11.70** Integration test : `PUT /admin/users/{id}/activate` → login fonctionne à nouveau
- [x] **11.71** Unit test : `AbsenceService.approve()` — succès, mauvais manager, déjà approuvée
- [x] **11.72** Unit test : `send_weekly_timesheet_reminders` — avec saisies (pas de rappel), sans saisies (rappel), absent toute la semaine (pas de rappel), préférences désactivées (pas de rappel)
- [x] **11.73** Integration test : `GET /admin/availability` — données agrégées correctes avec absences et heures

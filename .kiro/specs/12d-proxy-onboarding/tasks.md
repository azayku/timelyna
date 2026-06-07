# Tasks — Spec 12d : Mode Proxy Admin & Onboarding Différé

## US-01 — Mode Proxy Admin (Admin Impersonation)

- [x] **12d.1** Écrire migration `0014_proxy_audit.py` : créer `proxy_audit_logs`, ajouter `proxy_admin_id BIGINT` sur `timesheet_entries`
- [x] **12d.2** Mettre à jour le modèle `TimesheetEntry` avec `proxy_admin_id`
- [x] **12d.3** Créer modèle `ProxyAuditLog` dans `backend/app/models/proxy_audit_log.py`
- [x] **12d.4** Implémenter `AuthService.create_proxy_token(admin_id, employee_id)` : JWT avec `is_proxy: true`, durée 2h, log dans `proxy_audit_logs`
- [x] **12d.5** Implémenter `AuthService.end_proxy_session(proxy_log_id)` : enregistre `ended_at` et `entries_created`
- [x] **12d.6** Modifier `get_current_user` dependency : détecter `is_proxy`, injecter `proxy_admin_id` dans le contexte de la requête
- [x] **12d.7** Modifier `TimesheetService.create_entry()` : si `is_proxy`, enregistrer `proxy_admin_id` sur l'entrée, forcer statut `draft`
- [x] **12d.8** Enregistrer `POST /api/v1/admin/proxy/start`, `POST /api/v1/admin/proxy/end`, `GET /api/v1/admin/proxy/logs` dans `admin.py` avec `require_role('admin')` et `require_finance_license()`
- [x] **12d.9** Créer `frontend/src/lib/proxyStore.ts` : store Zustand `isProxy`, `proxiedEmployee`, `proxyLogId`, `startProxy()`, `endProxy()`
- [x] **12d.10** Créer `ProxyBanner.tsx` : bannière orange persistante avec nom de l'employé, compteur de pointages créés, bouton "Quitter le proxy"
- [x] **12d.11** Modifier `App.tsx` : afficher `ProxyBanner` si `isProxy === true`
- [x] **12d.12** Modifier la sidebar : masquer les entrées admin/finance si `isProxy === true`, afficher uniquement Timesheet et Saisie
- [x] **12d.13** Ajouter bouton "Agir en tant que" dans `AdminUsersPage.tsx` (visible uniquement si licence Finance Pro active)
- [x] **12d.14** Créer `ProxyLogsPage.tsx` : tableau AG Grid des sessions proxy avec admin, employé, durée, nombre de pointages
- [x] **12d.15** Integration test : `POST /admin/proxy/start` → token proxy valide ; saisie d'heures avec token proxy → `proxy_admin_id` enregistré
- [x] **12d.16** Integration test : token proxy ne peut pas accéder aux routes admin → 403

## US-02 — Création différée de compte lors du recrutement

- [x] **12d.17** Écrire migration `0016_pending_employees.py` : créer table `pending_employees`, ajouter `account_creation_lead_days INTEGER DEFAULT 2` sur `org_settings`
- [x] **12d.18** Mettre à jour le modèle `OrgSettings` avec `account_creation_lead_days`
- [x] **12d.19** Créer modèle SQLAlchemy `PendingEmployee` dans `backend/app/models/pending_employee.py`
- [x] **12d.20** Créer `PendingEmployeeRepository` : `create`, `get_pending_due(today)`, `get_all`, `delete`, `get_by_id`
- [x] **12d.21** Modifier `AuthService` : ajouter `create_employee_or_pending()` — si `hire_date - lead_days > today` → crée `PendingEmployee`, sinon crée `Employee` immédiatement
- [x] **12d.22** Créer `backend/app/tasks/onboarding_tasks.py` avec tâche Celery `activate_pending_employees()` : récupère les pending dont `account_creation_date <= today`, crée les comptes, supprime les enregistrements, notifie l'admin
- [x] **12d.23** Configurer Celery Beat pour `activate_pending_employees` quotidiennement à 07h00
- [x] **12d.24** Enregistrer `GET/POST /api/v1/admin/pending-employees`, `DELETE /api/v1/admin/pending-employees/{id}`, `POST /api/v1/admin/pending-employees/{id}/activate` dans `admin.py`
- [x] **12d.25** Mettre à jour `POST /api/v1/admin/users` pour appeler `create_employee_or_pending()` au lieu de `create_employee()` directement
- [x] **12d.26** Mettre à jour `OrgSettingsPage.tsx` : ajouter champ "Délai de création de compte (jours)" avec input numérique 0-30 et description explicative
- [x] **12d.27** Mettre à jour `AdminUsersPage.tsx` : ajouter onglet "En attente" avec tableau AG Grid des `pending_employees` (colonnes : Nom, Email, Rôle, Date d'entrée, Date création compte, Actions)
- [x] **12d.28** Ajouter boutons "Forcer la création" et "Annuler" sur chaque ligne du tableau des recrutements en attente
- [x] **12d.29** Afficher un badge bleu "Compte prévu le JJ/MM" dans la réponse du formulaire de création si `type === 'pending'`
- [x] **12d.30** Unit test : `create_employee_or_pending` — `hire_date` futur → `PendingEmployee` ; `hire_date` passé → `Employee` immédiat
- [x] **12d.31** Unit test : `activate_pending_employees` — `account_creation_date = today` → compte créé ; date future → ignoré
- [x] **12d.32** Integration test : `POST /admin/users` avec `hire_date` dans 10 jours et `lead_days = 2` → `pending_employee` créé avec `account_creation_date = hire_date - 2`

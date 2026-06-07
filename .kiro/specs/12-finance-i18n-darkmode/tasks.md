# Tasks — Module Finance Pro, AG Grid, i18n, Dark Mode & Employee Enhancements

## US-01 — Licence Finance Pro

- [ ] **12.1** Ajouter `FINANCE_LICENSE_SECRET` dans `backend/app/core/config.py` et `backend/.env`
- [ ] **12.2** Créer `backend/app/utils/finance_license.py` : `generate_key(expiry)`, `validate_key(key)` avec HMAC-SHA256 + XOR + CRC32 base36
- [ ] **12.3** Écrire migration `0010_finance_license_fields.py` : ajouter `finance_license_key VARCHAR(100)` et `finance_license_expires_at DATE` sur `org_settings`
- [ ] **12.4** Mettre à jour le modèle `OrgSettings` avec les deux nouveaux champs
- [ ] **12.5** Créer `backend/app/core/finance_license_deps.py` : dépendance FastAPI `require_finance_license()` qui vérifie la validité en DB
- [ ] **12.6** Enregistrer `POST /api/v1/admin/finance-license/activate` et `GET /api/v1/admin/finance-license/status` dans `admin.py`
- [ ] **12.7** Créer `frontend/src/features/finance/useFinanceLicense.ts` : hook React Query qui expose `isActive`, `expiresAt`, `daysLeft`
- [ ] **12.8** Créer `FinanceLicenseGuard.tsx` : composant wrapper qui redirige vers la page licence si inactif
- [ ] **12.9** Créer `FinanceLicensePage.tsx` : champ de saisie de la clé, badge statut, bandeau d'avertissement si ≤ 30 jours
- [ ] **12.10** Masquer les entrées Finance Pro dans la sidebar si `isActive === false`
- [ ] **12.11** Unit test : `validate_key` — clé valide, format invalide, checksum incorrect, HMAC invalide, date expirée

## US-02 — Dashboard Finance Pro

- [ ] **12.12** Implémenter `FinanceDashboardService.get_dashboard(org_id, period)` dans `backend/app/services/finance_dashboard_service.py`
- [ ] **12.13** Enregistrer `GET /api/v1/finance/dashboard` avec `require_finance_license()` et `require_role('finance', 'admin')`
- [ ] **12.14** Créer `KpiCard.tsx` : widget KPI avec icône Lucide, valeur formatée, flèche tendance (hausse/baisse)
- [ ] **12.15** Créer `RevenueChart.tsx` : Recharts `ComposedChart` (Bar + Line) sur 12 mois glissants, adapté dark mode
- [ ] **12.16** Créer `ClientRevenueDonut.tsx` : Recharts `PieChart` répartition CA par client, adapté dark mode
- [ ] **12.17** Créer `ProjectBurnChart.tsx` : Recharts `BarChart` groupé heures facturées vs budget, adapté dark mode
- [ ] **12.18** Créer `RecentInvoicesWidget.tsx` : tableau des 5 dernières factures avec statut coloré
- [ ] **12.19** Créer `OverdueWidget.tsx` : liste des factures en retard avec nombre de jours de retard
- [ ] **12.20** Créer `FinanceDashboardPage.tsx` : layout responsive grid avec tous les widgets, lien vers vues détaillées

## US-03 — Gestion avancée des factures

- [ ] **12.21** Écrire migration `0011_invoice_enhancements.py` : ajouter `due_date`, `paid_at`, `tax_rate`, `subtotal_ht`, `tax_amount`, `total_ttc` sur `invoices` ; créer `invoice_line_items` et `invoice_audit_logs`
- [ ] **12.22** Mettre à jour le modèle SQLAlchemy `Invoice` avec les nouveaux champs
- [ ] **12.23** Créer modèle `InvoiceLineItem` dans `backend/app/models/invoice_line_item.py`
- [ ] **12.24** Créer modèle `InvoiceAuditLog` dans `backend/app/models/invoice_audit_log.py`
- [ ] **12.25** Mettre à jour `InvoicingService.create_draft()` : calcul `subtotal_ht`, `tax_amount`, `total_ttc`, génération numéro `FAC-YYYY-NNNN`, calcul `due_date`
- [ ] **12.26** Mettre à jour `InvoicingService.finalize()` : logger dans `invoice_audit_logs`
- [ ] **12.27** Ajouter `InvoicingService.mark_paid(invoice_id, paid_at)` : passe statut à `paid`, enregistre `paid_at`
- [ ] **12.28** Créer tâche Celery `mark_overdue_invoices()` : passe à `overdue` les factures `sent` dont `due_date < today`
- [ ] **12.29** Configurer Celery Beat pour `mark_overdue_invoices` quotidiennement à 01h00
- [ ] **12.30** Mettre à jour `InvoicesPage.tsx` avec AG Grid : colonnes Numéro, Client, Montant TTC, Statut, Échéance, Actions
- [ ] **12.31** Mettre à jour `InvoiceDetailPage.tsx` : panneau aperçu PDF latéral, section lignes manuelles, historique audit, bouton "Marquer payée"

## US-04 — Rapports financiers avancés

- [ ] **12.32** Implémenter `ReportingService.get_pnl(period)` : revenus, coûts, marge brute, marge nette
- [ ] **12.33** Implémenter `ReportingService.get_project_profitability()` : budget vs réel, marge par projet
- [ ] **12.34** Implémenter `ReportingService.get_aging_report()` : créances 0-30j, 31-60j, 61-90j, >90j
- [ ] **12.35** Implémenter `ReportingService.get_cashflow_forecast(months=3)` : prévision basée sur factures en cours
- [ ] **12.36** Enregistrer les routes reporting finance avec `require_finance_license()` et `require_role('finance', 'admin')`
- [ ] **12.37** Créer `FinancialReportPage.tsx` : onglets P&L / Rentabilité projets / Aging / Prévision trésorerie, export PDF/CSV

## US-05 — AG Grid (tous les tableaux)

- [ ] **12.38** Installer `ag-grid-community` et `ag-grid-react` si pas déjà fait (`npm install ag-grid-community ag-grid-react`)
- [x] **12.39** Créer/mettre à jour `src/components/DataGrid.tsx` : `AgGridReact` avec `defaultColDef` (sortable, filter, resizable, floatingFilter), pagination 25 par défaut, persistance `localStorage`, prop `darkMode`
- [x] **12.40** Migrer `AdminUsersPage.tsx` vers `DataGrid` : colonnes Nom, Username, Email, Rôle, Statut, Date naissance, Actions
- [x] **12.41** Migrer `AdminProjectsPage.tsx` vers `DataGrid` : colonnes Nom, Code, Client, Statut, Équipe, Budget
- [x] **12.42** Migrer `AdminClientsPage.tsx` vers `DataGrid` : colonnes Nom, Email, Taux, Statut
- [x] **12.43** Migrer `ApprovalsPage.tsx` vers `DataGrid` : colonnes Employé, Semaine, Heures, Statut, Date soumission
- [x] **12.44** Migrer `SubmissionsPage.tsx` vers `DataGrid` : colonnes Semaine, Heures, Statut, Date soumission
- [ ] **12.45** Migrer `AbsencesPage.tsx` vers `DataGrid` : colonnes Employé, Type, Début, Fin, Statut
- [x] **12.46** Migrer `FinancialReportPage.tsx` vers `DataGrid` : colonnes Client, Heures, CA, Coût, Marge

## US-06 — Désactivation différée

- [ ] **12.47** Écrire migration `0012_employee_address_deactivation.py` : ajouter `address VARCHAR(500)` et `deactivation_scheduled_at TIMESTAMP` sur `employees`
- [ ] **12.48** Mettre à jour le modèle `Employee` avec `address` et `deactivation_scheduled_at`
- [ ] **12.49** Implémenter `AuthService.schedule_deactivation(employee_id, scheduled_at)` : stocke la date, envoie email si ≤ 7 jours
- [ ] **12.50** Implémenter `AuthService.cancel_scheduled_deactivation(employee_id)` : supprime `deactivation_scheduled_at`
- [ ] **12.51** Enregistrer `PUT /api/v1/admin/users/{id}/schedule-deactivation` et `DELETE /api/v1/admin/users/{id}/schedule-deactivation` dans `admin.py`
- [ ] **12.52** Créer tâche Celery `process_scheduled_deactivations()` : désactive les employés dont `deactivation_scheduled_at <= now`
- [ ] **12.53** Configurer Celery Beat pour `process_scheduled_deactivations` quotidiennement à 00h05
- [ ] **12.54** Mettre à jour `AdminUsersPage.tsx` : modal de désactivation avec choix Immédiat/Différé, DatePicker, badge orange "Désactivation le JJ/MM"

## US-07 — Enrichissement profil employé

- [ ] **12.55** Mettre à jour `CreateUserRequest` Pydantic : `birth_date: date` (obligatoire), `address: str` (obligatoire)
- [ ] **12.56** Ajouter validation backend : `birth_date` absent → 422, `address` absent → 422, `birth_date` dans le futur → 422
- [ ] **12.57** Mettre à jour `UserResponse` Pydantic pour inclure `address`
- [ ] **12.58** Mettre à jour `UpdateUserRequest` pour permettre la modification de `address` et `birth_date`
- [ ] **12.59** Mettre à jour le formulaire `UserModal` dans `AdminUsersPage.tsx` : champs `birth_date` (obligatoire) et `address` (textarea, obligatoire), affichage de l'âge calculé
- [ ] **12.60** Mettre à jour `AuthService.create_employee()` : `birth_date` obligatoire pour la génération du mot de passe par défaut
- [ ] **12.61** Unit test : création employé sans `birth_date` → 422 ; sans `address` → 422

## US-08 — Internationalisation

- [ ] **12.62** Installer `react-i18next` et `i18next` (`npm install react-i18next i18next`)
- [ ] **12.63** Créer `frontend/src/lib/i18n.ts` : configuration i18next avec FR/EN/IT, persistance `localStorage`
- [ ] **12.64** Créer les fichiers de traduction `src/locales/fr/translation.json`, `src/locales/en/translation.json`, `src/locales/it/translation.json` avec toutes les clés de l'interface
- [ ] **12.65** Initialiser i18n dans `main.tsx` (import `./lib/i18n`)
- [ ] **12.66** Ajouter le sélecteur de langue (FR 🇫🇷 / EN 🇬🇧 / IT 🇮🇹) sur `LoginPage.tsx`
- [ ] **12.67** Ajouter le sélecteur de langue dans le menu profil (navbar)
- [ ] **12.68** Créer `frontend/src/lib/formatters.ts` : `formatDate(d)` et `formatCurrency(n, currency)` basés sur `Intl`
- [ ] **12.69** Remplacer tous les textes hardcodés par `t('clé')` dans les composants principaux (LoginPage, Sidebar, TimesheetEntryPage, ApprovalsPage, AdminUsersPage)
- [ ] **12.70** Ajouter `preferred_language` sur le modèle `Employee` et dans `UserResponse` pour les emails traduits

## US-09 — Dark Mode

- [ ] **12.71** Configurer `tailwind.config.js` : `darkMode: 'class'`
- [ ] **12.72** Créer `frontend/src/lib/themeStore.ts` : store Zustand avec `dark`, `toggle()`, persistance `localStorage`, initialisation depuis `prefers-color-scheme`
- [ ] **12.73** Appliquer/retirer la classe `dark` sur `document.documentElement` au toggle et à l'initialisation dans `App.tsx`
- [ ] **12.74** Ajouter le bouton toggle Dark/Light (icône Sun/Moon) dans la navbar
- [ ] **12.75** Ajouter les classes `dark:` sur tous les composants principaux : Sidebar, BottomNav, Layout, modales, formulaires, cards
- [ ] **12.76** Passer `darkMode` prop au composant `DataGrid.tsx` pour switcher entre `ag-theme-alpine` et `ag-theme-alpine-dark`
- [ ] **12.77** Adapter les couleurs des graphiques Recharts : créer `useChartTheme()` hook qui retourne les couleurs selon le mode
- [ ] **12.78** Tester le dark mode sur toutes les pages principales et corriger les contrastes insuffisants

## Tests

- [ ] **12.79** Unit test : `generate_key` + `validate_key` — clé valide, expirée, falsifiée, mauvais format
- [ ] **12.80** Integration test : `POST /admin/finance-license/activate` → module activé ; routes finance accessibles
- [ ] **12.81** Integration test : licence expirée → routes finance retournent 402
- [ ] **12.82** Integration test : `PUT /admin/users/{id}/schedule-deactivation` → `deactivation_scheduled_at` stocké
- [ ] **12.83** Unit test : `process_scheduled_deactivations` — employé avec date passée désactivé, date future ignoré
- [ ] **12.84** Integration test : création employé sans `birth_date` → 422 ; sans `address` → 422

## US-10 — Gestion avancée des projets

- [ ] **12.85** Créer `backend/app/utils/project_code.py` : `generate_project_code()` (5 lettres + 4 chiffres) et `ensure_unique_project_code(db)`
- [ ] **12.86** Modifier `POST /api/v1/admin/projects` : générer automatiquement `project_code` si non fourni, vérifier l'unicité
- [ ] **12.87** Ajouter `ProjectRepository.get_by_code(code)` pour la vérification d'unicité
- [ ] **12.88** Mettre à jour le modèle `Project` : ajouter `draft` et `cancelled` aux statuts valides, `end_date` obligatoire pour les projets actifs
- [ ] **12.89** Modifier `TimesheetService.create_entry()` : bloquer la saisie si le projet est en statut `draft` ou `planning`
- [ ] **12.90** Écrire migration `0013_skill_rates.py` : créer `skill_rates` et `project_team_members`
- [ ] **12.91** Créer modèle SQLAlchemy `SkillRate` dans `backend/app/models/skill_rate.py`
- [ ] **12.92** Créer modèle SQLAlchemy `ProjectTeamMember` dans `backend/app/models/project_team_member.py`
- [ ] **12.93** Créer `SkillRateRepository` : `list_by_org`, `create`, `update`, `delete`
- [ ] **12.94** Créer `ProjectTeamRepository` : `get_team`, `assign_member`, `remove_member`, `update_skill`
- [ ] **12.95** Enregistrer routes `GET/POST/PUT/DELETE /api/v1/admin/skill-rates` avec `require_role('admin')`
- [ ] **12.96** Implémenter `ProjectAvailabilityService.get_team_availability(start_date, end_date)` : occupation %, absences, conflits
- [ ] **12.97** Enregistrer `GET /api/v1/admin/projects/{id}/team-availability` avec `require_role('admin', 'manager')`
- [ ] **12.98** Mettre à jour `InvoicingService.create_draft()` : calculer les lignes par compétence (priorité custom_rate > skill_rate > project_rate > client_rate)
- [ ] **12.99** Créer `SkillRatesPage.tsx` : tableau AG Grid des compétences avec CRUD inline
- [ ] **12.100** Mettre à jour `TeamAssignmentModal.tsx` dans `AdminProjectsPage.tsx` : afficher disponibilité de chaque employé sur la période du projet, sélecteur de compétence par membre, avertissement si >80%
- [ ] **12.101** Mettre à jour `AdminProjectsPage.tsx` : badge coloré par statut, champ `end_date` obligatoire, code généré automatiquement (modifiable)
- [ ] **12.102** Unit test : `generate_project_code` — format correct, unicité garantie
- [ ] **12.103** Unit test : `create_entry` avec projet en statut `draft` → 422

## US-11 — Mode Proxy Admin

- [ ] **12.104** Écrire migration `0014_proxy_audit.py` : créer `proxy_audit_logs`, ajouter `proxy_admin_id` sur `timesheet_entries`
- [ ] **12.105** Mettre à jour le modèle `TimesheetEntry` avec `proxy_admin_id`
- [ ] **12.106** Créer modèle `ProxyAuditLog` dans `backend/app/models/proxy_audit_log.py`
- [ ] **12.107** Implémenter `AuthService.create_proxy_token(admin_id, employee_id)` : JWT avec `is_proxy: true`, durée 2h, log dans `proxy_audit_logs`
- [ ] **12.108** Implémenter `AuthService.end_proxy_session(proxy_log_id)` : enregistre `ended_at` et `entries_created`
- [ ] **12.109** Modifier `get_current_user` dependency : détecter `is_proxy`, injecter `proxy_admin_id` dans le contexte
- [ ] **12.110** Modifier `TimesheetService.create_entry()` : si `is_proxy`, enregistrer `proxy_admin_id` sur l'entrée, forcer statut `draft`
- [ ] **12.111** Enregistrer `POST /api/v1/admin/proxy/start`, `POST /api/v1/admin/proxy/end`, `GET /api/v1/admin/proxy/logs` dans `admin.py` avec `require_role('admin')` et `require_finance_license()`
- [ ] **12.112** Créer `frontend/src/lib/proxyStore.ts` : store Zustand `isProxy`, `proxiedEmployee`, `proxyLogId`, `startProxy()`, `endProxy()`
- [ ] **12.113** Créer `ProxyBanner.tsx` : bannière orange persistante avec nom de l'employé, compteur de pointages créés, bouton "Quitter le proxy"
- [ ] **12.114** Modifier `App.tsx` : afficher `ProxyBanner` si `isProxy === true`
- [ ] **12.115** Modifier la sidebar : masquer les entrées admin/finance si `isProxy === true`, afficher uniquement Timesheet et Saisie
- [ ] **12.116** Ajouter bouton "Agir en tant que" dans `AdminUsersPage.tsx` (visible uniquement si licence Finance Pro active)
- [ ] **12.117** Créer `ProxyLogsPage.tsx` : tableau AG Grid des sessions proxy avec admin, employé, durée, nombre de pointages
- [ ] **12.118** Integration test : `POST /admin/proxy/start` → token proxy valide ; saisie d'heures avec token proxy → `proxy_admin_id` enregistré
- [ ] **12.119** Integration test : token proxy ne peut pas accéder aux routes admin → 403

## US-12 — Création différée de compte lors du recrutement

- [ ] **12.120** Écrire migration `0016_pending_employees.py` : créer table `pending_employees`, ajouter `account_creation_lead_days INTEGER DEFAULT 2` sur `org_settings`
- [ ] **12.121** Mettre à jour le modèle `OrgSettings` avec `account_creation_lead_days`
- [ ] **12.122** Créer modèle SQLAlchemy `PendingEmployee` dans `backend/app/models/pending_employee.py`
- [ ] **12.123** Créer `PendingEmployeeRepository` dans `backend/app/repositories/pending_employee_repository.py` : `create`, `get_pending_due(today)`, `get_all`, `delete`, `get_by_id`
- [ ] **12.124** Modifier `AuthService` : ajouter `create_employee_or_pending()` qui compare `hire_date - lead_days` avec `today` et crée soit un `Employee` immédiatement, soit un `PendingEmployee`
- [ ] **12.125** Créer `backend/app/tasks/onboarding_tasks.py` avec tâche Celery `activate_pending_employees()` : récupère les `pending_employees` dont `account_creation_date <= today`, crée les comptes, supprime les enregistrements, notifie l'admin
- [ ] **12.126** Configurer Celery Beat pour `activate_pending_employees` quotidiennement à 07h00
- [ ] **12.127** Enregistrer les routes `GET/POST /api/v1/admin/pending-employees`, `DELETE /api/v1/admin/pending-employees/{id}`, `POST /api/v1/admin/pending-employees/{id}/activate` dans `admin.py`
- [ ] **12.128** Mettre à jour `POST /api/v1/admin/users` pour appeler `create_employee_or_pending()` au lieu de `create_employee()` directement
- [ ] **12.129** Mettre à jour `OrgSettingsPage.tsx` : ajouter le champ "Délai de création de compte (jours)" avec input numérique 0-30 et description explicative
- [ ] **12.130** Mettre à jour `AdminUsersPage.tsx` : ajouter onglet "En attente" avec tableau AG Grid des `pending_employees` (colonnes : Nom, Email, Rôle, Date d'entrée, Date création compte, Actions)
- [ ] **12.131** Ajouter boutons "Forcer la création" et "Annuler" sur chaque ligne du tableau des recrutements en attente
- [ ] **12.132** Afficher un badge bleu "Compte prévu le JJ/MM" dans la réponse du formulaire de création si `type === 'pending'`
- [ ] **12.133** Unit test : `create_employee_or_pending` — `hire_date` dans le futur → `PendingEmployee` créé ; `hire_date` passée → `Employee` créé immédiatement
- [ ] **12.134** Unit test : `activate_pending_employees` — employé avec `account_creation_date = today` → compte créé, pending supprimé ; date future → ignoré
- [ ] **12.135** Integration test : `POST /admin/users` avec `hire_date` dans 10 jours et `lead_days = 2` → `pending_employee` créé avec `account_creation_date = hire_date - 2`

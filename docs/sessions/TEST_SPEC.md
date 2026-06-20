# TEST_SPEC.md — Timelyna
> Spécification complète des tests : Backend (pytest) + Frontend (Vitest)  
> Basé sur le code existant — fonctions, services et endpoints réels

---

## LÉGENDE

| Symbole | Signification |
|---------|--------------|
| `[U]` | Test unitaire (logique isolée, mock DB) |
| `[I]` | Test d'intégration (vraie DB de test) |
| `[E2E]` | Test end-to-end (flux complet API → réponse) |
| 🔴 | Test critique (sécurité, données) |
| 🟡 | Test important (logique métier) |
| 🟢 | Test standard (happy path) |

---

## PARTIE 1 — BACKEND

---

### MODULE : `app/services/auth_service.py`

---

#### 1.1 `AuthService.authenticate(identifier, password, ip_address)`

**Rôle :** Valide les credentials (email ou username), gère le lockout, retourne les tokens.

---

**TEST-AUTH-001** `[U]` 🟢  
**Nom :** `test_authenticate_valid_email_returns_tokens`  
**Endpoint associé :** `POST /auth/login`  
**Scénario :**  
Un employé existant envoie son email et son mot de passe corrects.  
**Données :**  
- `identifier = "alice@test.com"`, `password = "SecurePass123"`  
- DB contient un employee avec `email="alice@test.com"` et hash bcrypt de `"SecurePass123"`  
**Résultat attendu :**  
- Retourne un dict avec `access_token`, `refresh_token`, `expires_at`  
- `access_token` est un JWT décodable contenant `employee_id`, `role`, `org_id`  
- Aucune exception levée  

---

**TEST-AUTH-002** `[U]` 🟢  
**Nom :** `test_authenticate_valid_username_returns_tokens`  
**Endpoint associé :** `POST /auth/login`  
**Scénario :**  
Un employé se connecte avec son **username** (pas son email).  
**Données :**  
- `identifier = "alice.martin"`, `password = "SecurePass123"`  
- DB contient un employee avec `username="alice.martin"`  
**Résultat attendu :**  
- Même résultat qu'AUTH-001 — retourne les tokens  

---

**TEST-AUTH-003** `[U]` 🔴  
**Nom :** `test_authenticate_wrong_password_raises_401`  
**Endpoint associé :** `POST /auth/login`  
**Scénario :**  
L'email est valide mais le mot de passe est incorrect.  
**Données :**  
- `identifier = "alice@test.com"`, `password = "WrongPassword"`  
**Résultat attendu :**  
- Lève `HTTPException(status_code=401)`  
- Le message ne révèle pas si c'est l'email ou le mot de passe qui est faux (protection énumération)  
- Le compteur de tentatives en DB est incrémenté  

---

**TEST-AUTH-004** `[U]` 🔴  
**Nom :** `test_authenticate_unknown_identifier_raises_401`  
**Endpoint associé :** `POST /auth/login`  
**Scénario :**  
L'email n'existe pas dans la DB.  
**Données :**  
- `identifier = "nonexistent@test.com"`, `password = "anything"`  
**Résultat attendu :**  
- Lève `HTTPException(status_code=401)` (même message qu'un mauvais mot de passe)  
- **Temps de réponse similaire** : la fonction doit exécuter un faux hash compare pour éviter les timing attacks  

---

**TEST-AUTH-005** `[U]` 🔴  
**Nom :** `test_authenticate_locked_account_raises_429`  
**Endpoint associé :** `POST /auth/login`  
**Scénario :**  
Le compte a déjà atteint `LOGIN_MAX_ATTEMPTS` tentatives échouées dans la fenêtre `LOGIN_WINDOW_MINUTES`.  
**Données :**  
- Employee avec `failed_login_count = LOGIN_MAX_ATTEMPTS`, `last_failed_login` dans la fenêtre  
**Résultat attendu :**  
- Lève `HTTPException(status_code=429)` avec message de lockout  
- Aucun token généré  

---

**TEST-AUTH-006** `[U]` 🟡  
**Nom :** `test_authenticate_inactive_employee_raises_401`  
**Endpoint associé :** `POST /auth/login`  
**Scénario :**  
L'employé a `employment_status = "inactive"` (désactivé).  
**Résultat attendu :**  
- Lève `HTTPException(status_code=401)` ou `403`  

---

#### 1.2 `AuthService.refresh(token)`

**Rôle :** Valide le refresh token, en génère un nouveau (rotation), invalide l'ancien.

---

**TEST-AUTH-007** `[U]` 🟢  
**Nom :** `test_refresh_valid_token_returns_new_tokens`  
**Endpoint associé :** `POST /auth/refresh`  
**Scénario :**  
Un refresh token valide et non révoqué est fourni.  
**Résultat attendu :**  
- Retourne nouveaux `access_token` et `refresh_token`  
- L'ancien refresh token est marqué comme révoqué en DB  

---

**TEST-AUTH-008** `[U]` 🔴  
**Nom :** `test_refresh_revoked_token_raises_401`  
**Endpoint associé :** `POST /auth/refresh`  
**Scénario :**  
Le token a déjà été utilisé (révoqué).  
**Résultat attendu :**  
- Lève `HTTPException(status_code=401)`  

---

**TEST-AUTH-009** `[U]` 🔴  
**Nom :** `test_refresh_expired_token_raises_401`  
**Endpoint associé :** `POST /auth/refresh`  
**Scénario :**  
Le token a dépassé sa date d'expiration.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=401)`  

---

#### 1.3 `AuthService.change_password(employee_id, current_password, new_password)`

**Rôle :** Vérifie l'ancien mot de passe, met à jour le hash, révoque tous les refresh tokens.

---

**TEST-AUTH-010** `[U]` 🟢  
**Nom :** `test_change_password_success`  
**Endpoint associé :** `POST /auth/password/change`  
**Scénario :**  
L'employé fournit son mot de passe actuel correct et un nouveau mot de passe.  
**Résultat attendu :**  
- Hash du mot de passe mis à jour en DB  
- `must_change_password = False`  
- Tous les refresh tokens de l'employé sont révoqués  
- Email de confirmation envoyé (task async mockée)  

---

**TEST-AUTH-011** `[U]` 🔴  
**Nom :** `test_change_password_wrong_current_raises_400`  
**Endpoint associé :** `POST /auth/password/change`  
**Scénario :**  
L'employé fournit un mauvais `current_password`.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=400)`  
- Le mot de passe en DB n'est **pas** modifié  

---

#### 1.4 `AuthService.create_employee_or_pending(email, first_name, last_name, role, ..., hire_date)`

**Rôle :** Crée soit un `Employee` immédiatement, soit un `PendingEmployee` si la `hire_date` est trop loin.

---

**TEST-AUTH-012** `[U]` 🟢  
**Nom :** `test_create_employee_immediate_when_hire_date_soon`  
**Endpoint associé :** `POST /admin/users`  
**Scénario :**  
`hire_date` = aujourd'hui + 1 jour (inférieur à `account_creation_lead_days`).  
**Résultat attendu :**  
- Retourne `{type: "employee", ...}` avec `generated_username` et `generated_password`  
- `must_change_password = True`  

---

**TEST-AUTH-013** `[U]` 🟡  
**Nom :** `test_create_pending_employee_when_hire_date_far`  
**Endpoint associé :** `POST /admin/users`  
**Scénario :**  
`hire_date` = aujourd'hui + 30 jours (supérieur à `account_creation_lead_days`).  
**Résultat attendu :**  
- Retourne `{type: "pending", ...}` — aucun compte `Employee` créé  
- Un enregistrement `PendingEmployee` est créé en DB  

---

**TEST-AUTH-014** `[U]` 🔴  
**Nom :** `test_create_employee_duplicate_email_raises_422`  
**Endpoint associé :** `POST /admin/users`  
**Scénario :**  
L'email est déjà utilisé par un autre employé.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)` ou `409`  

---

#### 1.5 `AuthService.create_proxy_token(admin_id, employee_id)`

**Rôle :** Admin impersonne un employé — génère un JWT proxy, insère un `ProxyAuditLog`.

---

**TEST-AUTH-015** `[U]` 🔴  
**Nom :** `test_proxy_token_contains_correct_claims`  
**Endpoint associé :** `POST /admin/proxy/start`  
**Scénario :**  
Admin (id=1) démarre une session proxy sur l'employé (id=5).  
**Résultat attendu :**  
- JWT contient `sub = employee_id=5`, `proxy_admin_id = 1`, expiry = 2h  
- Un `ProxyAuditLog` est créé en DB avec `started_at` rempli  

---

### MODULE : `app/services/timesheet_service.py`

---

#### 2.1 `TimesheetService.create_entry(employee_id, data, proxy_admin_id)`

**Rôle :** Crée une entrée de pointage après validation des heures, du projet, des doublons.

---

**TEST-TS-001** `[U]` 🟢  
**Nom :** `test_create_entry_valid_data_returns_draft`  
**Endpoint associé :** `POST /employee/timesheet/entries`  
**Scénario :**  
Employé crée une entrée pour un projet assigné, date passée, 8h normales.  
**Données :**  
- `employee_id=1`, `project_id=10`, `work_date="2026-05-05"`, `hours_worked=8`, `entry_type="normal"`  
**Résultat attendu :**  
- Retourne un dict avec `status="draft"`, `hours_worked=8.0`  
- Entrée persiste en DB avec `deleted_at=None`  

---

**TEST-TS-002** `[U]` 🔴  
**Nom :** `test_create_entry_future_date_raises_422`  
**Endpoint associé :** `POST /employee/timesheet/entries`  
**Scénario :**  
`work_date` est demain ou dans le futur.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)` avec message explicite  

---

**TEST-TS-003** `[U]` 🔴  
**Nom :** `test_create_entry_project_not_assigned_raises_403`  
**Endpoint associé :** `POST /employee/timesheet/entries`  
**Scénario :**  
Le `project_id` existe mais n'est pas assigné à cet employé.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=403)` ou `404`  

---

**TEST-TS-004** `[U]` 🔴  
**Nom :** `test_create_entry_exceeds_max_daily_hours_raises_422`  
**Endpoint associé :** `POST /employee/timesheet/entries`  
**Scénario :**  
L'employé a déjà 8h ce jour, il essaie d'ajouter 4h (total = 12h > `max_hours_per_day=10`).  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)` mentionnant le dépassement des heures max  

---

**TEST-TS-005** `[U]` 🟡  
**Nom :** `test_create_entry_duplicate_raises_409`  
**Endpoint associé :** `POST /employee/timesheet/entries`  
**Scénario :**  
Une entrée identique (même `employee_id`, `project_id`, `work_date`, `entry_type`) existe déjà.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=409)` — contrainte d'unicité  

---

**TEST-TS-006** `[U]` 🟡  
**Nom :** `test_create_entry_below_minimum_hours_raises_422`  
**Endpoint associé :** `POST /employee/timesheet/entries`  
**Scénario :**  
`hours_worked = 0.1` (inférieur à `0.25`).  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)`  

---

#### 2.2 `TimesheetService.update_entry(employee_id, entry_id, data)`

**Rôle :** Modifie une entrée en statut `draft` ou `rejected`. Remet une entrée `rejected` en `draft`.

---

**TEST-TS-007** `[U]` 🟢  
**Nom :** `test_update_draft_entry_updates_hours`  
**Endpoint associé :** `PUT /employee/timesheet/entries/{entry_id}`  
**Scénario :**  
Entrée `draft` avec `hours_worked=8` → mise à jour à `7.5`.  
**Résultat attendu :**  
- Retourne l'entrée mise à jour avec `hours_worked=7.5`, `status="draft"`  

---

**TEST-TS-008** `[U]` 🟡  
**Nom :** `test_update_rejected_entry_reverts_to_draft`  
**Endpoint associé :** `PUT /employee/timesheet/entries/{entry_id}`  
**Scénario :**  
Entrée `rejected` (suite à un refus manager) est modifiée par l'employé.  
**Résultat attendu :**  
- Entrée mise à jour avec `status="draft"` (plus `"rejected"`)  
- Peut être re-soumise  

---

**TEST-TS-009** `[U]` 🔴  
**Nom :** `test_update_submitted_entry_raises_403`  
**Endpoint associé :** `PUT /employee/timesheet/entries/{entry_id}`  
**Scénario :**  
Tentative de modification d'une entrée `submitted` (en attente d'approbation).  
**Résultat attendu :**  
- Lève `HTTPException(status_code=403)` ou `409`  
- Entrée non modifiée en DB  

---

**TEST-TS-010** `[U]` 🔴  
**Nom :** `test_update_approved_entry_raises_403`  
**Endpoint associé :** `PUT /employee/timesheet/entries/{entry_id}`  
**Scénario :**  
Tentative de modification d'une entrée `approved`.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=403)` ou `409`  

---

**TEST-TS-011** `[U]` 🔴  
**Nom :** `test_update_entry_of_another_employee_raises_403`  
**Endpoint associé :** `PUT /employee/timesheet/entries/{entry_id}`  
**Scénario :**  
Employé A essaie de modifier une entrée appartenant à l'employé B.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=403)` ou `404`  

---

#### 2.3 `TimesheetService.delete_entry(employee_id, entry_id)`

**Rôle :** Suppression logique (soft delete) d'une entrée, uniquement si statut `draft`.

---

**TEST-TS-012** `[U]` 🟢  
**Nom :** `test_delete_draft_entry_soft_deletes`  
**Endpoint associé :** `DELETE /employee/timesheet/entries/{entry_id}`  
**Scénario :**  
Suppression d'une entrée `draft`.  
**Résultat attendu :**  
- `deleted_at` rempli en DB  
- L'entrée n'apparaît plus dans les requêtes standard  
- Retourne `None` (204 No Content)  

---

**TEST-TS-013** `[U]` 🔴  
**Nom :** `test_delete_non_draft_entry_raises_403`  
**Endpoint associé :** `DELETE /employee/timesheet/entries/{entry_id}`  
**Scénario :**  
Tentative de suppression d'une entrée `submitted` ou `approved`.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=403)` ou `422`  
- `deleted_at` reste `None` en DB  

---

#### 2.4 `TimesheetService.submit_week(employee_id, week_str)`

**Rôle :** Soumet toutes les entrées `draft` d'une semaine ISO. Crée ou réutilise une `Approval`.

---

**TEST-TS-014** `[U]` 🟢  
**Nom :** `test_submit_week_first_time_creates_approval`  
**Endpoint associé :** `POST /employee/timesheet/submit`  
**Scénario :**  
Première soumission pour la semaine `2026-W18`, 5 entrées `draft`.  
**Résultat attendu :**  
- Toutes les entrées passent en `submitted`  
- Une `Approval` est créée avec `status="pending"`  
- Une notification in-app est envoyée au manager  
- Retourne `{approval_id, entries_submitted: 5}`  

---

**TEST-TS-015** `[U]` 🟡  
**Nom :** `test_submit_week_resubmission_after_rejection`  
**Endpoint associé :** `POST /employee/timesheet/submit`  
**Scénario :**  
L'approbation précédente de `2026-W18` a le statut `rejected`. L'employé a corrigé les entrées (repassées en `draft`).  
**Résultat attendu :**  
- L'`Approval` existante est **réutilisée** (pas de nouvelle créée)  
- Son statut repasse à `pending`  
- Les entrées passent en `submitted`  

---

**TEST-TS-016** `[U]` 🔴  
**Nom :** `test_submit_week_no_draft_entries_raises_422`  
**Endpoint associé :** `POST /employee/timesheet/submit`  
**Scénario :**  
La semaine n'a aucune entrée `draft` (toutes déjà `submitted` ou `approved`).  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)` avec code `"no_draft_entries"`  

---

**TEST-TS-017** `[U]` 🔴  
**Nom :** `test_submit_week_no_manager_found_raises_422`  
**Endpoint associé :** `POST /employee/timesheet/submit`  
**Scénario :**  
L'employé n'appartient à aucune organisation ou l'organisation n'a pas de manager.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)` avec code `"no_valid_organization"`  

---

**TEST-TS-018** `[U]` 🟡  
**Nom :** `test_submit_week_invalid_format_raises_422`  
**Endpoint associé :** `POST /employee/timesheet/submit`  
**Scénario :**  
`week_str = "2026-18"` (format invalide, devrait être `"2026-W18"`).  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)` ou `ValueError`  

---

#### 2.5 `TimesheetService.get_week(employee_id, week_str)`

**Rôle :** Retourne les entrées groupées par date pour une semaine ISO.

---

**TEST-TS-019** `[U]` 🟢  
**Nom :** `test_get_week_returns_entries_grouped_by_date`  
**Endpoint associé :** `GET /employee/timesheet/week?week=2026-W18`  
**Scénario :**  
L'employé a 3 entrées réparties sur 2 jours de la semaine 18.  
**Résultat attendu :**  
- Retourne un dict avec clés de dates  
- Chaque clé contient la liste des entrées pour ce jour  
- `week_total` = somme totale des heures  

---

**TEST-TS-020** `[U]` 🟢  
**Nom :** `test_get_week_empty_week_returns_empty_dict`  
**Endpoint associé :** `GET /employee/timesheet/week?week=2026-W18`  
**Scénario :**  
Aucune entrée pour cette semaine.  
**Résultat attendu :**  
- Retourne un dict vide ou `{entries: [], week_total: 0}`  

---

### MODULE : `app/services/approval_service.py`

---

#### 3.1 `ApprovalService.approve(approver_id, approval_id, notes, is_admin)`

**Rôle :** Manager approuve une soumission. Met à jour toutes les entrées en `approved`.

---

**TEST-APP-001** `[U]` 🟢  
**Nom :** `test_approve_pending_approval_success`  
**Endpoint associé :** `POST /manager/approvals/{approval_id}/approve`  
**Scénario :**  
Manager (id=2) approuve l'approbation (id=10) qui est en statut `pending`.  
**Données :** 2 entrées `submitted` liées à cet approval  
**Résultat attendu :**  
- `Approval.status = "approved"`, `approved_at` rempli  
- Les 2 entrées passent en `status = "approved"` avec `approved_at`  
- Notification in-app envoyée à l'employé  
- Email envoyé (task async mockée)  
- Retourne `{approval_id: 10, status: "approved"}`  

---

**TEST-APP-002** `[U]` 🔴  
**Nom :** `test_approve_already_approved_raises_409`  
**Endpoint associé :** `POST /manager/approvals/{approval_id}/approve`  
**Scénario :**  
L'approbation est déjà en statut `approved`.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=409)`  

---

**TEST-APP-003** `[U]` 🔴  
**Nom :** `test_approve_by_unauthorized_manager_raises_403`  
**Endpoint associé :** `POST /manager/approvals/{approval_id}/approve`  
**Scénario :**  
Un manager essaie d'approuver une soumission d'un employé **qui n'est pas dans son équipe**.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=403)` ou `404`  

---

#### 3.2 `ApprovalService.reject(approver_id, approval_id, rejection_reason, is_admin)`

**Rôle :** Rejette une soumission. Repasse les entrées en `draft`. Nécessite une raison (min 10 chars).

---

**TEST-APP-004** `[U]` 🟢  
**Nom :** `test_reject_approval_with_reason_success`  
**Endpoint associé :** `POST /manager/approvals/{approval_id}/reject`  
**Scénario :**  
Manager rejette avec raison `"Heures incorrectes sur le projet X"`.  
**Résultat attendu :**  
- `Approval.status = "rejected"`, `rejection_reason` remplie  
- Les entrées `submitted` repassent en `status = "draft"`  
- Notification in-app + email envoyés à l'employé  

---

**TEST-APP-005** `[U]` 🔴  
**Nom :** `test_reject_approval_reason_too_short_raises_422`  
**Endpoint associé :** `POST /manager/approvals/{approval_id}/reject`  
**Scénario :**  
`rejection_reason = "Bad"` (moins de 10 caractères).  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)` — validation Pydantic ou service  

---

#### 3.3 `ApprovalService.cancel(employee_id, approval_id)`

**Rôle :** L'employé annule sa propre soumission (statut `pending` → `cancelled`, entrées → `draft`).

---

**TEST-APP-006** `[U]` 🟢  
**Nom :** `test_cancel_own_pending_approval_success`  
**Endpoint associé :** `POST /employee/submissions/{approval_id}/cancel`  
**Scénario :**  
L'employé annule sa soumission en attente.  
**Résultat attendu :**  
- `Approval.status = "cancelled"`  
- Entrées repassent en `draft`  
- Retourne `{approval_id, status: "cancelled"}`  

---

**TEST-APP-007** `[U]` 🔴  
**Nom :** `test_cancel_another_employee_submission_raises_403`  
**Endpoint associé :** `POST /employee/submissions/{approval_id}/cancel`  
**Scénario :**  
L'employé A essaie d'annuler la soumission de l'employé B.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=403)` ou `404`  

---

**TEST-APP-008** `[U]` 🔴  
**Nom :** `test_cancel_already_approved_submission_raises_409`  
**Endpoint associé :** `POST /employee/submissions/{approval_id}/cancel`  
**Scénario :**  
L'approbation est déjà `approved` — ne peut plus être annulée.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=409)`  

---

#### 3.4 `ApprovalService.get_pending_for_manager(manager_id, page, page_size)`

**Rôle :** Liste paginée des approbations `pending` pour les rapports du manager.

---

**TEST-APP-009** `[U]` 🟢  
**Nom :** `test_get_pending_returns_only_manager_team_approvals`  
**Endpoint associé :** `GET /manager/approvals?status=pending`  
**Scénario :**  
Manager A a 3 employés. Manager B a 2 employés. Chacun a soumis une semaine.  
**Résultat attendu :**  
- `get_pending_for_manager(manager_A_id)` retourne 3 entrées  
- Les 2 entrées du manager B **ne sont pas incluses**  

---

### MODULE : `app/services/absence_service.py`

---

#### 4.1 `AbsenceService.create(employee_id, absence_type, start_date, end_date, notes)`

**Rôle :** Crée une demande d'absence avec statut `pending`. Notifie le manager.

---

**TEST-ABS-001** `[U]` 🟢  
**Nom :** `test_create_absence_valid_request_success`  
**Endpoint associé :** `POST /employee/absences` *(ou via modal)*  
**Scénario :**  
Employé demande 3 jours de congé payé (`cp`), dates : 2026-05-12 → 2026-05-14.  
**Résultat attendu :**  
- Absence créée avec `status="pending"`, `absence_type="cp"`  
- `start_date="2026-05-12"`, `end_date="2026-05-14"`  
- Notification envoyée au manager  

---

**TEST-ABS-002** `[U]` 🔴  
**Nom :** `test_create_absence_end_before_start_raises_422`  
**Scénario :**  
`end_date < start_date`.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)`  

---

**TEST-ABS-003** `[U]` 🟡  
**Nom :** `test_create_absence_sick_leave_no_balance_required`  
**Scénario :**  
Congé maladie (`sick`) avec solde de congés payés = 0. Le service ne doit pas bloquer.  
**Résultat attendu :**  
- Absence créée avec `status="pending"`  
- Aucune vérification de solde pour le type `sick`  

---

#### 4.2 `AbsenceService.approve(manager_id, absence_id)`

---

**TEST-ABS-004** `[U]` 🟢  
**Nom :** `test_approve_absence_success`  
**Endpoint associé :** `POST /manager/absences/{absence_id}/approve`  
**Scénario :**  
Manager approuve une demande `pending`.  
**Résultat attendu :**  
- `Absence.status = "approved"`, `approved_at` rempli, `approved_by = manager_id`  
- Notification envoyée à l'employé  

---

**TEST-ABS-005** `[U]` 🔴  
**Nom :** `test_approve_absence_by_wrong_manager_raises_403`  
**Scénario :**  
Manager C essaie d'approuver une absence d'un employé appartenant au Manager D.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=403)` ou `404`  

---

#### 4.3 `AbsenceService.reject(manager_id, absence_id, reason)`

---

**TEST-ABS-006** `[U]` 🟢  
**Nom :** `test_reject_absence_with_reason_success`  
**Endpoint associé :** `POST /manager/absences/{absence_id}/reject`  
**Scénario :**  
Manager rejette avec une raison.  
**Résultat attendu :**  
- `Absence.status = "rejected"`, `rejection_reason` remplie  
- Notification envoyée à l'employé  

---

#### 4.4 `AbsenceService.get_leave_balance(employee_id, year)`

**Rôle :** Calcule le solde annuel de congés : acquis - pris (absences `cp` approuvées).

---

**TEST-ABS-007** `[U]` 🟢  
**Nom :** `test_get_leave_balance_calculates_correctly`  
**Endpoint associé :** `GET /employee/leave-balance?year=2026`  
**Scénario :**  
L'employé a `annual_leave_days=25`. Il a 2 absences `cp` approuvées de 3 jours chacune.  
**Résultat attendu :**  
- `days_taken = 6`, `days_remaining = 19`, `annual_leave_days = 25`  

---

**TEST-ABS-008** `[U]` 🟡  
**Nom :** `test_get_leave_balance_pending_absences_not_counted`  
**Scénario :**  
Une absence `cp` est en statut `pending` (pas encore approuvée).  
**Résultat attendu :**  
- Elle **n'est pas comptée** dans `days_taken`  
- Seules les absences `approved` comptent  

---

### MODULE : `app/services/organization_service.py`

---

**TEST-ORG-001** `[U]` 🟢  
**Nom :** `test_create_organization_with_valid_manager`  
**Endpoint associé :** `POST /admin/organizations`  
**Scénario :**  
Admin crée une organisation avec un manager valide (role = `"manager"`).  
**Résultat attendu :**  
- Organisation créée en DB  
- `manager_id` assigné  
- Retourne l'objet Organization  

---

**TEST-ORG-002** `[U]` 🔴  
**Nom :** `test_create_organization_with_employee_role_raises_422`  
**Endpoint associé :** `POST /admin/organizations`  
**Scénario :**  
Le `manager_id` pointe vers un employé avec `role = "employee"` (pas manager).  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)` avec code `"invalid_manager"`  

---

**TEST-ORG-003** `[U]` 🟢  
**Nom :** `test_list_organizations_includes_employee_count`  
**Endpoint associé :** `GET /admin/organizations`  
**Scénario :**  
2 organisations, org A a 5 employés actifs, org B a 3 employés actifs.  
**Résultat attendu :**  
- Chaque entrée contient `employee_count` correct  
- Les organisations soft-deletées ne sont pas incluses  

---

**TEST-ORG-004** `[U]` 🟡  
**Nom :** `test_soft_delete_organization_marks_deleted_at`  
**Endpoint associé :** `DELETE /admin/organizations/{org_id}`  
**Scénario :**  
Admin supprime une organisation.  
**Résultat attendu :**  
- `Organization.deleted_at` est rempli  
- `list_organizations()` ne la retourne plus  
- Les employés de l'organisation gardent leur compte  

---

### MODULE : `app/services/mutation_service.py`

---

**TEST-MUT-001** `[U]` 🟢  
**Nom :** `test_mutate_employee_to_new_org_success`  
**Endpoint associé :** `POST /admin/employees/{employee_id}/mutate`  
**Scénario :**  
Employé (org=1) est muté vers org=2. Org 2 a un manager (id=10).  
**Résultat attendu :**  
- `Employee.org_id = 2`, `Employee.manager_id = 10`  
- Un `EmployeeMutationLog` est créé  
- Task Celery `send_mutation_notification` est appelée  

---

**TEST-MUT-002** `[U]` 🔴  
**Nom :** `test_mutate_org_manager_raises_422`  
**Endpoint associé :** `POST /admin/employees/{employee_id}/mutate`  
**Scénario :**  
L'employé est lui-même manager d'une organisation.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)` avec code `"employee_is_org_manager"`  

---

**TEST-MUT-003** `[U]` 🔴  
**Nom :** `test_mutate_to_inactive_org_raises_422`  
**Endpoint associé :** `POST /admin/employees/{employee_id}/mutate`  
**Scénario :**  
L'organisation cible est soft-deletée (`deleted_at` rempli).  
**Résultat attendu :**  
- Lève `HTTPException(status_code=422)` avec code `"invalid_target_organization"`  

---

### MODULE : `app/services/invoicing_service.py`

---

**TEST-INV-001** `[U]` 🟢  
**Nom :** `test_create_draft_invoice_groups_by_project`  
**Endpoint associé :** `POST /finance/invoices`  
**Scénario :**  
Client A a des entrées approuvées sur 2 projets pour la période `"2026-05"`.  
**Résultat attendu :**  
- Invoice créée avec 2 lignes de facturation (`line_items`)  
- Numéro au format `FAC-2026-NNNN`  
- `due_date = issued_date + 30 jours`  
- `status = "draft"`  

---

**TEST-INV-002** `[U]` 🔴  
**Nom :** `test_create_draft_no_approved_entries_raises_400`  
**Endpoint associé :** `POST /finance/invoices`  
**Scénario :**  
Aucune entrée approuvée non-facturée pour ce client/période.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=400)`  

---

**TEST-INV-003** `[U]` 🟡  
**Nom :** `test_billing_rate_priority_custom_over_project`  
**Endpoint associé :** `POST /finance/invoices`  
**Scénario :**  
Entrée avec `billing_rate` custom (non nul). Le projet a aussi un `billing_rate`.  
**Résultat attendu :**  
- La ligne de facturation utilise le taux **custom** de l'entrée (priorité la plus haute)  

---

**TEST-INV-004** `[U]` 🟡  
**Nom :** `test_finalize_invoice_marks_entries_invoiced`  
**Endpoint associé :** `POST /finance/invoices/{invoice_id}/finalize`  
**Scénario :**  
Facture en statut `draft` est finalisée.  
**Résultat attendu :**  
- Toutes les entrées liées passent en `status = "invoiced"`  
- Facture passe en `status = "ready"`  
- Un `InvoiceAuditLog` est créé  

---

**TEST-INV-005** `[U]` 🔴  
**Nom :** `test_finalize_non_draft_invoice_raises_409`  
**Endpoint associé :** `POST /finance/invoices/{invoice_id}/finalize`  
**Scénario :**  
Facture déjà en statut `ready` ou `sent`.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=409)`  

---

**TEST-INV-006** `[U]` 🟢  
**Nom :** `test_mark_paid_invoice_sent_status_success`  
**Endpoint associé :** `POST /finance/invoices/{invoice_id}/mark-paid`  
**Scénario :**  
Facture `sent` est marquée comme payée.  
**Résultat attendu :**  
- `Invoice.status = "paid"`, `paid_at` rempli  
- `InvoiceAuditLog` créé  

---

**TEST-INV-007** `[U]` 🔴  
**Nom :** `test_mark_paid_draft_invoice_raises_409`  
**Endpoint associé :** `POST /finance/invoices/{invoice_id}/mark-paid`  
**Scénario :**  
Facture encore en `draft`.  
**Résultat attendu :**  
- Lève `HTTPException(status_code=409)`  

---

### MODULE : `app/services/reporting_service.py`

---

**TEST-REP-001** `[U]` 🟢  
**Nom :** `test_get_personal_stats_calculates_billable_pct`  
**Endpoint associé :** `GET /employee/statistics?period=this_month`  
**Scénario :**  
Employé a 40h approuvées : 30h facturables + 10h non facturables.  
**Résultat attendu :**  
- `total_hours = 40`, `billable_hours = 30`, `billable_pct = 75.0`  

---

**TEST-REP-002** `[U]` 🟢  
**Nom :** `test_get_hours_report_grouped_by_employee`  
**Endpoint associé :** `GET /admin/hours-report?group_by=employee`  
**Scénario :**  
3 employés ont des entrées approuvées pour la même période.  
**Résultat attendu :**  
- Liste de 3 enregistrements, un par employé  
- Chaque enregistrement contient les totaux par type d'heure  

---

**TEST-REP-003** `[U]` 🟡  
**Nom :** `test_parse_period_this_month_returns_correct_dates`  
**Scénario :**  
Appel de `_parse_period("this_month")` en mai 2026.  
**Résultat attendu :**  
- `start = date(2026, 5, 1)`, `end = date(2026, 5, 31)`  

---

---

## PARTIE 2 — TESTS D'INTÉGRATION BACKEND

---

**TEST-INT-001** `[I]` 🟢  
**Nom :** `test_full_weekly_workflow_submit_and_approve`  
**Endpoints :**  
1. `POST /employee/timesheet/entries` × 5  
2. `POST /employee/timesheet/submit`  
3. `GET /manager/approvals`  
4. `POST /manager/approvals/{id}/approve`  
**Scénario :**  
L'employé crée 5 entrées (lundi→vendredi), soumet la semaine. Le manager liste les approbations, voit l'entrée de l'employé, approuve. Vérification finale : entrées en `approved`, approbation en `approved`.  

---

**TEST-INT-002** `[I]` 🟡  
**Nom :** `test_rejection_and_resubmission_workflow`  
**Endpoints :**  
1. `POST /employee/timesheet/entries` × 3  
2. `POST /employee/timesheet/submit`  
3. `POST /manager/approvals/{id}/reject`  
4. `PUT /employee/timesheet/entries/{id}` (correction)  
5. `POST /employee/timesheet/submit` (re-soumission)  
6. `POST /manager/approvals/{id}/approve`  
**Scénario :**  
Soumission → rejet → correction par l'employé (entrées repassent en draft) → re-soumission → approbation.  

---

**TEST-INT-003** `[I]` 🟡  
**Nom :** `test_proxy_admin_creates_entry_for_employee`  
**Endpoints :**  
1. `POST /admin/proxy/start`  
2. `POST /employee/timesheet/entries` (avec token proxy)  
3. `POST /admin/proxy/end`  
**Scénario :**  
Admin démarre une session proxy sur l'employé, crée une entrée en son nom, termine la session.  
**Résultat attendu :**  
- L'entrée est créée avec `employee_id = employé`, `created_by_proxy = admin_id`  
- `ProxyAuditLog.entries_created = 1`  

---

**TEST-INT-004** `[I]` 🟡  
**Nom :** `test_employee_mutation_updates_manager`  
**Endpoints :**  
1. `POST /admin/employees/{id}/mutate`  
2. `GET /manager/approvals` (depuis le nouveau manager)  
3. `POST /employee/timesheet/submit` (depuis l'employé muté)  
**Scénario :**  
Employé muté vers Org 2. Il soumet une semaine. Vérifier que la notification va bien au **nouveau** manager (pas l'ancien).  

---

---

## PARTIE 3 — FRONTEND (Vitest + React Testing Library)

---

### PAGE : `LoginPage`

---

**TEST-FE-001** `[U]` 🟢  
**Nom :** `test_login_page_submits_form_and_redirects`  
**Composant :** `LoginPage`  
**Service appelé :** `POST /auth/login`  
**Scénario :**  
L'utilisateur saisit un email et mot de passe valides, clique sur "Se connecter".  
**Assertions :**  
- Le bouton affiche `"Connexion…"` pendant la requête  
- Après succès : `navigate('/')` est appelé  
- `authStore.token` est rempli  

---

**TEST-FE-002** `[U]` 🔴  
**Nom :** `test_login_page_shows_error_on_401`  
**Composant :** `LoginPage`  
**Scénario :**  
L'API retourne `401 Unauthorized`.  
**Assertions :**  
- Message d'erreur `"Email ou mot de passe incorrect."` affiché  
- Formulaire toujours visible (pas de redirection)  

---

**TEST-FE-003** `[U]` 🔴  
**Nom :** `test_login_page_shows_lockout_message_on_429`  
**Composant :** `LoginPage`  
**Scénario :**  
L'API retourne `429 Too Many Requests`.  
**Assertions :**  
- Message de lockout affiché (ex : `"Compte temporairement bloqué"`)  

---

### PAGE : `MyTimesheetsPage`

---

**TEST-FE-004** `[U]` 🟢  
**Nom :** `test_timesheets_page_displays_entries_grouped_by_week`  
**Composant :** `MyTimesheetsPage`  
**Service appelé :** `GET /employee/timesheet/entries`  
**Scénario :**  
L'API retourne 5 entrées toutes sur `2026-W18`.  
**Assertions :**  
- Une section "Semaine 18" est affichée  
- Le total d'heures de la semaine est correct  
- Le badge de statut de la semaine est visible  

---

**TEST-FE-005** `[U]` 🟢  
**Nom :** `test_submit_week_button_calls_api_and_updates_badge`  
**Composant :** `MyTimesheetsPage`  
**Service appelé :** `POST /employee/timesheet/submit`  
**Scénario :**  
Week avec entrées `draft` → l'utilisateur clique "Soumettre" → SweetAlert de confirmation → confirme.  
**Assertions :**  
- `POST /employee/timesheet/submit` appelé avec `{week: "2026-W18"}`  
- Badge passe de `"Brouillon"` à `"En attente"` après succès  

---

**TEST-FE-006** `[U]` 🟡  
**Nom :** `test_edit_entry_inline_saves_new_hours`  
**Composant :** `MyTimesheetsPage` → composant `EntryRow`  
**Service appelé :** `PUT /employee/timesheet/entries/{id}`  
**Scénario :**  
Clic sur l'icône crayon d'une entrée `draft` → modifie les heures → confirme.  
**Assertions :**  
- `PUT /employee/timesheet/entries/1` appelé avec `{hours_worked: 7}`  
- L'affichage se met à jour avec `7h`  

---

**TEST-FE-007** `[U]` 🔴  
**Nom :** `test_delete_entry_shows_swal_and_removes_on_confirm`  
**Composant :** `MyTimesheetsPage` → composant `EntryRow`  
**Service appelé :** `DELETE /employee/timesheet/entries/{id}`  
**Scénario :**  
Clic sur l'icône poubelle → SweetAlert demande confirmation → confirme.  
**Assertions :**  
- `DELETE /employee/timesheet/entries/1` appelé  
- L'entrée disparaît de la liste  

---

**TEST-FE-008** `[U]` 🟡  
**Nom :** `test_filter_by_status_draft_shows_only_draft_entries`  
**Composant :** `MyTimesheetsPage`  
**Scénario :**  
Clic sur le bouton filtre `"Brouillons"`.  
**Assertions :**  
- Seules les semaines avec entrées `draft` sont visibles  
- Le bouton `"Brouillons"` a la classe `bg-indigo-600`  

---

**TEST-FE-009** `[U]` 🟡  
**Nom :** `test_year_filter_shows_entries_for_selected_year`  
**Composant :** `MyTimesheetsPage`  
**Scénario :**  
Clic sur bouton `"2025"`.  
**Assertions :**  
- Seules les semaines de 2025 sont affichées  

---

### MODAL : `QuickTimesheetModal`

---

**TEST-FE-010** `[U]` 🟢  
**Nom :** `test_quick_modal_shows_projects_for_selected_date`  
**Composant :** `QuickTimesheetModal`  
**Service appelé :** `GET /projects?active=true&date=2026-05-06`  
**Scénario :**  
Modal ouverte avec `defaultDate="2026-05-06"`. L'API retourne 2 projets.  
**Assertions :**  
- Dropdown affiche les 2 projets  
- Option par défaut `"— Choisir un projet —"` présente  

---

**TEST-FE-011** `[U]` 🟢  
**Nom :** `test_quick_modal_submit_creates_entry_and_closes`  
**Composant :** `QuickTimesheetModal`  
**Service appelé :** `POST /employee/timesheet/entries`  
**Scénario :**  
Sélection projet + heures + clic "Enregistrer".  
**Assertions :**  
- `POST /employee/timesheet/entries` appelé avec les bonnes données  
- La modal se ferme après succès  
- `onClose` est appelé  

---

**TEST-FE-012** `[U]` 🟡  
**Nom :** `test_quick_modal_shows_error_on_api_failure`  
**Composant :** `QuickTimesheetModal`  
**Scénario :**  
L'API retourne une erreur `422`.  
**Assertions :**  
- Message d'erreur affiché dans la modal  
- La modal **ne se ferme pas**  

---

**TEST-FE-013** `[U]` 🟡  
**Nom :** `test_quick_modal_shows_empty_state_when_no_projects`  
**Composant :** `QuickTimesheetModal`  
**Service appelé :** `GET /projects?active=true&date=2026-05-06`  
**Scénario :**  
L'API retourne une liste vide de projets.  
**Assertions :**  
- Message `"Aucun projet actif assigné pour cette date."` affiché  
- Bouton "Enregistrer" désactivé  

---

### MODAL : `TimeOffRequestModal`

---

**TEST-FE-014** `[U]` 🟢  
**Nom :** `test_timeoff_modal_submits_request_and_closes`  
**Composant :** `TimeOffRequestModal`  
**Service appelé :** `POST /employee/absences`  
**Scénario :**  
Sélection type `"cp"`, dates 2026-05-12→14, clic "Soumettre".  
**Assertions :**  
- `POST /employee/absences` appelé avec les bonnes données  
- La modal se ferme  

---

**TEST-FE-015** `[U]` 🔴  
**Nom :** `test_timeoff_modal_shows_error_on_unexpected_api_error`  
**Composant :** `TimeOffRequestModal`  
**Scénario :**  
L'API retourne `500 Internal Server Error`.  
**Assertions :**  
- Message `"Erreur inattendue."` affiché  
- La modal ne se ferme pas  

---

### PAGE : `ApprovalsPage`

---

**TEST-FE-016** `[U]` 🟢  
**Nom :** `test_approvals_page_lists_pending_submissions`  
**Composant :** `ApprovalsPage`  
**Service appelé :** `GET /manager/approvals?status=pending`  
**Scénario :**  
2 soumissions en attente dans l'API.  
**Assertions :**  
- 2 lignes affichées avec nom employé, semaine, heures  
- Boutons "Valider" et "Rejeter" présents pour chaque ligne  

---

**TEST-FE-017** `[U]` 🟢  
**Nom :** `test_approvals_page_approve_submission_updates_ui`  
**Composant :** `ApprovalsPage`  
**Service appelé :** `POST /manager/approvals/{id}/approve`  
**Scénario :**  
Clic "Valider" → confirmation → succès API.  
**Assertions :**  
- La soumission disparaît de la liste `pending`  
- OU son badge passe à `"Approuvé"`  

---

**TEST-FE-018** `[U]` 🔴  
**Nom :** `test_approvals_page_reject_requires_reason_min_10_chars`  
**Composant :** `ApprovalsPage`  
**Service appelé :** `POST /manager/approvals/{id}/reject`  
**Scénario :**  
Clic "Rejeter" → formulaire de rejet affiché. L'utilisateur saisit `"Bad"` (< 10 chars).  
**Assertions :**  
- Bouton "Confirmer le rejet" reste désactivé  
- Après 10+ caractères, bouton devient actif  

---

### PAGE : `ManagerTeamPage`

---

**TEST-FE-019** `[U]` 🟢  
**Nom :** `test_team_page_shows_10_items_first_page`  
**Composant :** `ManagerTeamPage`  
**Service appelé :** `GET /manager/team`  
**Scénario :**  
L'API retourne 15 membres d'équipe.  
**Assertions :**  
- Seulement 10 membres affichés (pagination)  
- Contrôles de pagination visibles  
- Indicateur `"1–10 sur 15"`  

---

**TEST-FE-020** `[U]` 🟡  
**Nom :** `test_team_page_search_filters_in_frontend`  
**Composant :** `ManagerTeamPage`  
**Scénario :**  
Liste de 15 membres. Saisie de `"alice"` dans le champ de recherche.  
**Assertions :**  
- Seuls les membres dont le nom/email contient `"alice"` sont visibles  
- Compteur mis à jour  

---

**TEST-FE-021** `[U]` 🟡  
**Nom :** `test_team_page_org_filter_reduces_list`  
**Composant :** `ManagerTeamPage`  
**Scénario :**  
Sélection de `"Org A"` dans le dropdown de filtre organisation.  
**Assertions :**  
- Seuls les membres de `"Org A"` sont affichés  
- Le dropdown est pré-rempli avec les organisations uniques présentes dans les données  

---

**TEST-FE-022** `[U]` 🟡  
**Nom :** `test_team_page_reset_filters_shows_all`  
**Composant :** `ManagerTeamPage`  
**Scénario :**  
Après avoir appliqué un filtre, clic sur "Réinitialiser les filtres".  
**Assertions :**  
- Tous les membres réapparaissent  
- Champ recherche vidé  
- Dropdown remis à `"Toutes les organisations"`  

---

### PAGE : `ManagerOrganizationsPage`

---

**TEST-FE-023** `[U]` 🟢  
**Nom :** `test_orgs_page_search_filters_by_name_and_manager`  
**Composant :** `ManagerOrganizationsPage`  
**Service appelé :** `GET /manager/organizations`  
**Scénario :**  
3 organisations. Saisie de `"Tech"` dans le champ de recherche.  
**Assertions :**  
- Seules les orgs dont le nom ou le nom du manager contient `"Tech"` sont visibles  

---

**TEST-FE-024** `[U]` 🟡  
**Nom :** `test_orgs_page_pagination_10_items`  
**Composant :** `ManagerOrganizationsPage`  
**Scénario :**  
L'API retourne 12 organisations.  
**Assertions :**  
- 10 organisations en page 1  
- Pagination visible avec `"Page 1 / 2"`  

---

### COMPOSANT : `MobileMenu`

---

**TEST-FE-025** `[U]` 🟢  
**Nom :** `test_mobile_menu_opens_quick_timesheet_modal`  
**Composant :** `MobileMenu`  
**Scénario :**  
Clic sur `"Saisie rapide"` dans le menu mobile.  
**Assertions :**  
- `QuickTimesheetModal` s'ouvre (`open = true`)  
- Le menu se ferme  

---

**TEST-FE-026** `[U]` 🟢  
**Nom :** `test_mobile_menu_opens_absence_modal`  
**Composant :** `MobileMenu`  
**Scénario :**  
Clic sur `"Déclarer une absence"`.  
**Assertions :**  
- `TimeOffRequestModal` s'ouvre  
- Le menu se ferme  

---

**TEST-FE-027** `[U]` 🟡  
**Nom :** `test_mobile_menu_shows_admin_section_for_admin_role`  
**Composant :** `MobileMenu`  
**Scénario :**  
L'utilisateur connecté a `role = "admin"`.  
**Assertions :**  
- Section `"Administration"` visible avec les liens admin  

---

**TEST-FE-028** `[U]` 🟡  
**Nom :** `test_mobile_menu_hides_admin_section_for_employee_role`  
**Composant :** `MobileMenu`  
**Scénario :**  
L'utilisateur connecté a `role = "employee"`.  
**Assertions :**  
- Section `"Administration"` absente du menu  

---

### COMPOSANT : `Layout`

---

**TEST-FE-029** `[U]` 🟢  
**Nom :** `test_layout_page_title_updates_on_route_change`  
**Composant :** `Layout`  
**Scénario :**  
Navigation vers `/timesheet/my-timesheets`.  
**Assertions :**  
- `<Header title="Mes pointages" />` (ou traduction i18n courante)  
- Breadcrumb correct `["TIMESHEET", "Mes pointages"]`  

---

**TEST-FE-030** `[U]` 🟢  
**Nom :** `test_layout_page_title_updates_with_language_change`  
**Composant :** `Layout`  
**Scénario :**  
Langue passe de `fr` à `en`, page `/timesheet/my-timesheets`.  
**Assertions :**  
- Titre passe de `"Mes pointages"` à `"My Timesheets"` dynamiquement  

---

### COMPOSANT : `BottomNav`

---

**TEST-FE-031** `[U]` 🟡  
**Nom :** `test_bottom_nav_shows_approvals_badge_for_manager`  
**Composant :** `BottomNav`  
**Service appelé :** `GET /manager/approvals?status=pending`  
**Scénario :**  
Manager avec 3 approbations en attente.  
**Assertions :**  
- Icône `CheckSquare` avec badge rouge `"3"` visible  

---

**TEST-FE-032** `[U]` 🟡  
**Nom :** `test_bottom_nav_shows_menu_icon_for_employee`  
**Composant :** `BottomNav`  
**Scénario :**  
L'utilisateur a `role = "employee"`.  
**Assertions :**  
- L'icône `Menu` est affichée (pas l'icône `CheckSquare`)  
- Aucun badge d'approbation  

---

---

## PARTIE 4 — TESTS E2E (FLUX COMPLETS)

---

**TEST-E2E-001** 🟢  
**Nom :** `e2e_employee_creates_and_submits_week`  
**Flux :**  
1. `POST /auth/login` (employee)  
2. `POST /employee/timesheet/entries` × 3 (lundi, mardi, mercredi)  
3. `GET /employee/timesheet/week?week=2026-W18` → vérifie 3 entrées  
4. `POST /employee/timesheet/submit` (semaine 18)  
5. `GET /employee/submissions` → vérifie `status="pending"`  
**Résultat final :** 3 entrées `submitted`, 1 approbation `pending`  

---

**TEST-E2E-002** 🟢  
**Nom :** `e2e_manager_approves_full_week`  
**Prérequis :** E2E-001 terminé  
**Flux :**  
1. `POST /auth/login` (manager)  
2. `GET /manager/approvals?status=pending` → 1 résultat  
3. `GET /manager/approvals/{id}` → voir le détail  
4. `POST /manager/approvals/{id}/approve` (avec notes)  
5. `GET /manager/approvals?status=approved` → 1 résultat  
**Résultat final :** Approbation `approved`, entrées `approved`  

---

**TEST-E2E-003** 🟡  
**Nom :** `e2e_rejection_and_resubmission`  
**Flux :**  
1. Login employee → Créer 2 entrées → Soumettre  
2. Login manager → Rejeter avec raison  
3. Login employee → Voir entrées `rejected` → Modifier une entrée → Re-soumettre  
4. Login manager → Approuver  
**Résultat final :** Toutes les entrées `approved`  

---

**TEST-E2E-004** 🟡  
**Nom :** `e2e_leave_request_approved_by_manager`  
**Flux :**  
1. Login employee → `POST /employee/absences` (3 jours cp)  
2. Login manager → `GET /manager/absences` → voir la demande  
3. Manager → `POST /manager/absences/{id}/approve`  
4. `GET /employee/absences` → statut `approved`  
**Résultat final :** Absence `approved`  

---

**TEST-E2E-005** 🟡  
**Nom :** `e2e_create_invoice_and_finalize`  
**Prérequis :** Entrées approuvées pour un client  
**Flux :**  
1. Login finance/admin  
2. `POST /finance/invoices` → créer brouillon  
3. `GET /finance/invoices/{id}` → vérifier les line_items  
4. `POST /finance/invoices/{id}/finalize` → statut `ready`  
5. `POST /finance/invoices/{id}/send` → statut `sent`  
6. `POST /finance/invoices/{id}/mark-paid` → statut `paid`  
**Résultat final :** Invoice `paid`, entrées `invoiced`  

---

**TEST-E2E-006** 🟡  
**Nom :** `e2e_employee_mutation_changes_approval_routing`  
**Flux :**  
1. Login admin → `POST /admin/employees/{id}/mutate` (Org 1 → Org 2)  
2. Login employee muté → créer des entrées → soumettre  
3. Login manager Org 2 → vérifier que la soumission apparaît dans ses approbations  
4. Login manager Org 1 → vérifier que la soumission **N'APPARAÎT PAS** dans ses approbations  
**Résultat final :** Routage correct vers le nouveau manager  

---

## PARTIE 5 — STRUCTURE DES FICHIERS DE TEST

```
tests/
├── backend/
│   ├── conftest.py                     # DB session, fixtures partagées, cleanup
│   ├── unit/
│   │   ├── test_auth_service.py        # TEST-AUTH-001 → 015
│   │   ├── test_timesheet_service.py   # TEST-TS-001 → 020
│   │   ├── test_approval_service.py    # TEST-APP-001 → 009
│   │   ├── test_absence_service.py     # TEST-ABS-001 → 008
│   │   ├── test_organization_service.py# TEST-ORG-001 → 004
│   │   ├── test_mutation_service.py    # TEST-MUT-001 → 003
│   │   ├── test_invoicing_service.py   # TEST-INV-001 → 007
│   │   └── test_reporting_service.py   # TEST-REP-001 → 003
│   └── integration/
│       └── test_workflows.py           # TEST-INT-001 → 004
│
└── frontend/
    ├── setup.ts                        # MSW setup, i18n mock, authStore mock
    ├── mocks/
    │   ├── handlers.ts                 # MSW handlers pour tous les endpoints
    │   └── fixtures.ts                 # Données de test réutilisables
    ├── pages/
    │   ├── LoginPage.test.tsx          # TEST-FE-001 → 003
    │   ├── MyTimesheetsPage.test.tsx   # TEST-FE-004 → 009
    │   ├── ApprovalsPage.test.tsx      # TEST-FE-016 → 018
    │   ├── ManagerTeamPage.test.tsx    # TEST-FE-019 → 022
    │   └── ManagerOrgsPage.test.tsx    # TEST-FE-023 → 024
    ├── modals/
    │   ├── QuickTimesheetModal.test.tsx# TEST-FE-010 → 013
    │   └── TimeOffRequestModal.test.tsx# TEST-FE-014 → 015
    ├── components/
    │   ├── MobileMenu.test.tsx         # TEST-FE-025 → 028
    │   ├── Layout.test.tsx             # TEST-FE-029 → 030
    │   └── BottomNav.test.tsx          # TEST-FE-031 → 032
    └── e2e/
        └── workflows.test.tsx          # TEST-E2E-001 → 006
```

---

## COMMANDES D'EXÉCUTION

```bash
# Backend — tous les tests
pytest tests/backend/ -v

# Backend — uniquement les tests unitaires
pytest tests/backend/unit/ -v

# Backend — uniquement les tests d'intégration
pytest tests/backend/integration/ -v

# Backend — avec rapport de couverture
pytest tests/backend/ --cov=app --cov-report=html

# Backend — test spécifique
pytest tests/backend/unit/test_timesheet_service.py::test_create_entry_valid_data_returns_draft -v

# Frontend — tous les tests
npm run test

# Frontend — en mode watch
npm run test -- --watch

# Frontend — couverture
npm run test -- --coverage

# Frontend — test spécifique
npm run test -- MyTimesheetsPage
```

---

*Dernière mise à jour : Mai 2026 — v2.0 (basé sur le code réel)*

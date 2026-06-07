# Design — UX Improvements & Operational Features

## US-01 — Correction saisie des heures

### Problème actuel
`TimesheetEntryPage` utilise `getCurrentWeek()` hardcodé — la date sélectionnée ne se propage pas depuis `TimesheetWeekPage`. La liste des projets retourne tous les projets actifs de l'employé sans tenir compte de la date.

### Solution

**Frontend — propagation de la date**
- `TimesheetWeekPage` : le bouton "Saisir des heures" navigue vers `/timesheet/entry?date=YYYY-MM-DD` en passant la date du jour sélectionné
- `TimesheetEntryPage` : lit `?date=` depuis `useSearchParams()`, fallback sur `today`
- Le sélecteur de date existant reste fonctionnel

**Backend — filtrage des projets par date**
```
GET /api/v1/projects?date=2025-W12-1   (date ISO optionnelle)
```
- Si `date` fourni : retourne les projets actifs où l'employé est membre ET dont `start_date <= date <= end_date` (ou `end_date IS NULL`)
- `ProjectRepository.list_active_for_employee(employee_id, reference_date=None)`

---

## US-02 — Username & mot de passe automatiques

### Nouveaux champs sur `Employee`
```sql
ALTER TABLE employees ADD COLUMN username VARCHAR(50) UNIQUE;
ALTER TABLE employees ADD COLUMN birth_date DATE;
ALTER TABLE employees ADD COLUMN must_change_password BOOLEAN DEFAULT false;
```

### Algorithme de génération du username
```python
def generate_username(first_name: str, last_name: str) -> str:
    # Normaliser : minuscules, supprimer accents
    last = unidecode(last_name)[:4].lower().ljust(4, 'x')
    first = unidecode(first_name)[:4].lower().ljust(4, 'x')
    return last + first  # ex: "martjean"

def ensure_unique_username(base: str, existing: set[str]) -> str:
    if base not in existing:
        return base
    for i in range(1, 100):
        candidate = f"{base}{i:02d}"
        if candidate not in existing:
            return candidate
    raise ValueError("Cannot generate unique username")
```

### Algorithme de génération du mot de passe
```python
def generate_default_password(username: str, birth_date: date | None) -> str:
    if birth_date:
        return username + birth_date.strftime("%d%m%Y")
    return secrets.token_urlsafe(12)
```

### Flux de création
```
POST /api/v1/admin/users
    │
    ├─ Générer username (unique)
    ├─ Générer mot de passe par défaut
    ├─ Créer Employee avec must_change_password=True
    ├─ Créer password_reset_token (24h) pour setup
    └─ Envoyer email welcome avec username + lien setup
```

### Réponse enrichie
```json
{
  "employee_id": 42,
  "username": "martjean",
  "email": "jean.martin@company.fr",
  "must_change_password": true,
  ...
}
```

### Frontend — forcer le changement de mot de passe
- Après login, si `must_change_password === true` dans le JWT → rediriger vers `/change-password?forced=true`
- `ChangePasswordPage` en mode forcé : pas de bouton "Annuler", message explicatif

---

## US-03 — Vue disponibilité

### API
```
GET /api/v1/admin/availability?start_date=2025-04-01&end_date=2025-04-07&department=Dev&project_id=5
```

**Réponse :**
```json
{
  "dates": ["2025-04-01", "2025-04-02", ...],
  "employees": [
    {
      "employee_id": 1,
      "full_name": "Jean Martin",
      "department": "Dev",
      "days": {
        "2025-04-01": {
          "hours_logged": 7.5,
          "occupation_pct": 94,
          "absence": null
        },
        "2025-04-02": {
          "hours_logged": 0,
          "occupation_pct": 0,
          "absence": { "type": "cp", "status": "approved" }
        }
      }
    }
  ]
}
```

### Service
```python
class AvailabilityService:
    async def get_availability(
        self, start_date: date, end_date: date,
        department: str | None, project_id: int | None
    ) -> dict
```

### Frontend — `AvailabilityPage.tsx`
- Sélecteur de plage de dates (max 31 jours)
- Tableau : lignes = employés, colonnes = jours
- Cellule colorée : vert (dispo), orange (partiel), rouge (plein/absent)
- Filtres : département, projet

---

## US-04 — AG Grid

### Dépendance
```bash
npm install ag-grid-community ag-grid-react
```
AG Grid Community (licence MIT) — pas de licence commerciale requise.

### Composant réutilisable `DataGrid.tsx`
```tsx
// src/components/DataGrid.tsx
import { AgGridReact } from 'ag-grid-react'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

interface DataGridProps<T> {
  rowData: T[]
  columnDefs: ColDef[]
  pageSize?: number
  storageKey?: string  // pour persister filtres dans localStorage
  onRowClicked?: (row: T) => void
}
```

### Configuration par défaut
```ts
const defaultColDef = {
  sortable: true,
  filter: true,
  resizable: true,
  floatingFilter: true,  // filtres sous les en-têtes
}

const paginationPageSizeSelector = [10, 25, 50, 100]
const defaultPageSize = 25
```

### Pages à migrer
| Page | Colonnes clés |
|------|--------------|
| `AdminUsersPage` | Nom, Email, Rôle, Statut, Manager, Date création |
| `AdminProjectsPage` | Nom, Code, Client, Statut, Équipe, Budget |
| `AdminClientsPage` | Nom, Email, Taux, Statut |
| `ApprovalsPage` | Employé, Semaine, Heures, Statut, Date soumission |
| `SubmissionsPage` | Semaine, Heures, Statut, Date soumission |
| `InvoicesPage` | Numéro, Client, Montant, Statut, Date |
| `FinancialReportPage` | Client, Heures, CA, Coût, Marge |

---

## US-05 — Templates d'emails paramétrables

### Nouveau modèle `EmailTemplate`
```sql
CREATE TABLE email_templates (
  id BIGSERIAL PRIMARY KEY,
  template_key VARCHAR(100) NOT NULL UNIQUE,  -- 'welcome_new_employee', 'password_reset'
  subject VARCHAR(255) NOT NULL,
  html_body TEXT NOT NULL,
  text_body TEXT,
  variables JSONB,  -- liste des variables disponibles
  updated_by BIGINT REFERENCES employees(employee_id),
  updated_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Variables disponibles par template
```json
{
  "welcome_new_employee": ["first_name", "last_name", "username", "setup_link", "org_name"],
  "password_reset": ["first_name", "last_name", "reset_link", "org_name"]
}
```

### Service
```python
class EmailTemplateService:
    async def get_template(self, key: str) -> dict
    async def render_template(self, key: str, context: dict) -> tuple[str, str]  # subject, html
    async def update_template(self, key: str, subject: str, html_body: str) -> dict
    async def send_preview(self, key: str, to_email: str) -> None
```

### API
```
GET  /api/v1/admin/email-templates
GET  /api/v1/admin/email-templates/{key}
PUT  /api/v1/admin/email-templates/{key}
POST /api/v1/admin/email-templates/{key}/preview
```

### Frontend — `EmailTemplatesPage.tsx`
- Liste des templates avec statut (par défaut / personnalisé)
- Éditeur : champ sujet + éditeur HTML (textarea avec coloration syntaxique basique)
- Panneau d'aperçu en temps réel (iframe sandboxée)
- Bouton "Envoyer un test"
- Bouton "Réinitialiser au défaut"

---

## US-06 — Rappels automatiques

### Celery Beat Schedule
```python
# Chaque lundi à 16h00
CELERY_BEAT_SCHEDULE = {
    "weekly-timesheet-reminder": {
        "task": "app.tasks.reminder_tasks.send_weekly_timesheet_reminders",
        "schedule": crontab(hour=16, minute=0, day_of_week=1),  # lundi
    },
    "monthly-timesheet-reminder": {
        "task": "app.tasks.reminder_tasks.send_monthly_timesheet_reminders",
        "schedule": crontab(hour=12, minute=0, day=last_day_of_month),
    },
}
```

### Logique du rappel hebdomadaire
```python
async def send_weekly_timesheet_reminders():
    # Semaine précédente (lundi-dimanche)
    last_week = get_last_week()
    # Employés actifs avec au moins 1 projet actif
    employees = await get_active_employees_with_projects()
    for emp in employees:
        # Vérifier si des heures ont été saisies la semaine dernière
        has_entries = await has_entries_for_week(emp.employee_id, last_week)
        # Vérifier préférences de notification
        prefs = await get_notification_prefs(emp.employee_id)
        if not has_entries and prefs.timesheet_reminder_enabled:
            await send_reminder_email(emp, last_week, "weekly")
            await log_reminder(emp.employee_id, "weekly", last_week)
```

### Nouveau champ sur `notification_preferences`
```sql
ALTER TABLE notification_preferences ADD COLUMN timesheet_reminder_enabled BOOLEAN DEFAULT true;
```

### Table `notification_logs`
```sql
CREATE TABLE notification_logs (
  id BIGSERIAL PRIMARY KEY,
  employee_id BIGINT REFERENCES employees(employee_id),
  type VARCHAR(100) NOT NULL,  -- 'weekly_reminder', 'monthly_reminder'
  reference_period VARCHAR(20),  -- '2025-W12' ou '2025-04'
  sent_at TIMESTAMP DEFAULT NOW(),
  email_address VARCHAR(255)
);
```

---

## US-07 — Déclaration d'absences

### Modèle `Absence`
```sql
CREATE TABLE absences (
  id BIGSERIAL PRIMARY KEY,
  employee_id BIGINT NOT NULL REFERENCES employees(employee_id),
  absence_type VARCHAR(50) NOT NULL,  -- cp | sick_leave | other
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  notes VARCHAR(500),
  status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
  rejection_reason VARCHAR(500),
  approved_by BIGINT REFERENCES employees(employee_id),
  approved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  CHECK (end_date >= start_date)
);
```

### Nouveau champ sur `Employee`
```sql
ALTER TABLE employees ADD COLUMN annual_leave_days INTEGER DEFAULT 25;
```

### API
```
POST   /api/v1/employee/absences              — déclarer une absence
GET    /api/v1/employee/absences              — mes absences
DELETE /api/v1/employee/absences/{id}         — annuler (si pending)

GET    /api/v1/manager/absences               — absences de l'équipe (pending)
POST   /api/v1/manager/absences/{id}/approve
POST   /api/v1/manager/absences/{id}/reject   body: { reason }

GET    /api/v1/admin/absences                 — toutes les absences (filtrable)
```

### Service
```python
class AbsenceService:
    async def create(self, employee_id: int, data: dict) -> dict
    async def approve(self, manager_id: int, absence_id: int) -> dict
    async def reject(self, manager_id: int, absence_id: int, reason: str) -> dict
    async def cancel(self, employee_id: int, absence_id: int) -> None
    async def get_leave_balance(self, employee_id: int, year: int) -> dict
```

### Frontend
- `AbsencesPage.tsx` — liste des absences de l'employé + bouton "Déclarer une absence"
- `AbsenceFormModal.tsx` — formulaire : type, dates, notes
- `ManagerAbsencesPage.tsx` — liste des absences en attente de l'équipe + approve/reject
- `AbsenceCalendar.tsx` — vue calendrier mensuelle (optionnel, composant Recharts ou natif)

---

## US-08 — Activation / Désactivation de compte employé

### API
```
PUT /api/v1/admin/users/{id}/deactivate   — désactiver
PUT /api/v1/admin/users/{id}/activate     — réactiver
```

### Service
```python
# Dans AuthService
async def deactivate_employee(self, employee_id: int) -> None:
    await self.repo.update_employee(employee_id, employment_status="inactive")
    await self.repo.revoke_all_refresh_tokens(employee_id)
    await self.db.commit()

async def activate_employee(self, employee_id: int) -> None:
    await self.repo.update_employee(employee_id, employment_status="active")
    await self.db.commit()
```

### Frontend — `AdminUsersPage.tsx`
- Colonne "Statut" avec badge coloré (vert = actif, gris = inactif)
- Bouton toggle dans la ligne : "Désactiver" / "Réactiver" avec confirmation modale
- Filtre AG Grid sur la colonne statut (actif / inactif / tous)

---

## Migrations Alembic

| Migration | Description |
|-----------|-------------|
| `0005_add_employee_username_birthdate.py` | Ajoute `username`, `birth_date`, `must_change_password`, `annual_leave_days` sur `employees` |
| `0006_create_absences.py` | Crée la table `absences` |
| `0007_create_email_templates.py` | Crée la table `email_templates` |
| `0008_create_notification_logs.py` | Crée la table `notification_logs` |
| `0009_add_timesheet_reminder_pref.py` | Ajoute `timesheet_reminder_enabled` sur `notification_preferences` |


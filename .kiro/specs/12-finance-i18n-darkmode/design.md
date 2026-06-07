# Design — Module Finance Pro, AG Grid, i18n, Dark Mode & Employee Enhancements

---

## US-01 — Licence Finance Pro

### Algorithme complet

```python
# backend/app/utils/finance_license.py
import hashlib, hmac, struct, zlib, unicodedata
from datetime import date

SECRET = os.environ.get("FINANCE_LICENSE_SECRET", "change-me")

def _hmac8(date_str: str) -> str:
    """HMAC-SHA256 des 8 premiers chars hex."""
    h = hmac.new(SECRET.encode(), date_str.encode(), hashlib.sha256)
    return h.hexdigest()[:8]

def _xor_date(date_str: str, key8: str) -> str:
    """XOR chaque char de date_str avec key8 cyclique → hex."""
    result = []
    for i, c in enumerate(date_str):
        result.append(format(ord(c) ^ ord(key8[i % 8]), '02x'))
    return ''.join(result)

def _checksum(parts: str) -> str:
    """CRC32 en base36."""
    crc = zlib.crc32(parts.encode()) & 0xFFFFFFFF
    return _to_base36(crc)

def _to_base36(n: int) -> str:
    chars = '0123456789abcdefghijklmnopqrstuvwxyz'
    result = ''
    while n:
        result = chars[n % 36] + result
        n //= 36
    return result or '0'

def generate_key(expiry: date) -> str:
    date_str = expiry.strftime("%Y%m%d")
    hmac8 = _hmac8(date_str)
    xored = _xor_date(date_str, hmac8)
    body = f"FIN-{xored}-{hmac8}"
    chk = _checksum(body)
    return f"{body}-{chk}"

def validate_key(key: str) -> date:
    """Retourne la date d'expiration ou lève ValueError."""
    parts = key.split('-')
    if len(parts) != 4 or parts[0] != 'FIN':
        raise ValueError("Format de clé invalide")
    _, xored, hmac8, chk = parts
    body = f"FIN-{xored}-{hmac8}"
    if _checksum(body) != chk:
        raise ValueError("Checksum invalide")
    # Décoder la date
    date_chars = []
    for i in range(0, len(xored), 2):
        byte_val = int(xored[i:i+2], 16) ^ ord(hmac8[i//2 % 8])
        date_chars.append(chr(byte_val))
    date_str = ''.join(date_chars)
    # Vérifier HMAC
    if _hmac8(date_str) != hmac8:
        raise ValueError("Signature HMAC invalide")
    expiry = date.fromisoformat(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}")
    if expiry < date.today():
        raise ValueError("Licence expirée")
    return expiry
```

### Nouveaux champs sur `OrgSettings`
```sql
ALTER TABLE org_settings ADD COLUMN finance_license_key VARCHAR(100);
ALTER TABLE org_settings ADD COLUMN finance_license_expires_at DATE;
```

### Middleware FastAPI
```python
# backend/app/core/finance_license_deps.py
def require_finance_license():
    async def dep(db: AsyncSession = Depends(get_db)):
        settings = await get_org_settings(db)
        if not settings.finance_license_expires_at:
            raise HTTPException(402, "Module Finance Pro non activé")
        if settings.finance_license_expires_at < date.today():
            raise HTTPException(402, "Licence Finance Pro expirée")
    return Depends(dep)
```

### API
```
POST /api/v1/admin/finance-license/activate   body: { key: str }
GET  /api/v1/admin/finance-license/status
```

### Frontend
- `FinanceLicensePage.tsx` — champ de saisie de la clé, badge statut, bandeau d'avertissement 30j
- `useFinanceLicense` hook — vérifie le statut, expose `isActive`, `expiresAt`, `daysLeft`
- Toutes les routes Finance Pro wrappées dans `<FinanceLicenseGuard>` qui redirige si inactif

---

## US-02 — Dashboard Finance Pro

### Librairies
- Recharts (déjà installé) pour tous les graphiques
- `react-grid-layout` pour les widgets draggables (optionnel v2)

### Composants
```
src/features/finance/
├── FinanceDashboardPage.tsx     — layout principal
├── KpiCard.tsx                  — widget KPI avec icône, valeur, tendance
├── RevenueChart.tsx             — ComposedChart (Bar + Line) 12 mois
├── ClientRevenueDonut.tsx       — PieChart répartition CA par client
├── ProjectBurnChart.tsx         — BarChart groupé heures vs budget
├── RecentInvoicesWidget.tsx     — tableau 5 dernières factures
├── OverdueWidget.tsx            — liste factures en retard
└── hooks.ts                     — useFinanceDashboard(period)
```

### API
```
GET /api/v1/finance/dashboard?period=month|year
```
Réponse :
```json
{
  "kpis": { "revenue_month": 0, "revenue_year": 0, "billable_hours": 0, "margin_pct": 0, "pending_invoices": 0 },
  "monthly_revenue": [{ "month": "2025-01", "revenue": 0, "hours": 0 }],
  "client_revenue": [{ "client": "Acme", "revenue": 0 }],
  "project_burn": [{ "project": "...", "budget_hours": 0, "actual_hours": 0 }],
  "recent_invoices": [],
  "overdue_invoices": []
}
```

---

## US-03 — Gestion avancée des factures

### Nouveaux champs sur `Invoice`
```sql
ALTER TABLE invoices ADD COLUMN due_date DATE;
ALTER TABLE invoices ADD COLUMN paid_at TIMESTAMP;
ALTER TABLE invoices ADD COLUMN tax_rate DECIMAL(5,2) DEFAULT 20.00;
ALTER TABLE invoices ADD COLUMN subtotal_ht DECIMAL(12,2);
ALTER TABLE invoices ADD COLUMN tax_amount DECIMAL(12,2);
ALTER TABLE invoices ADD COLUMN total_ttc DECIMAL(12,2);
```

### Table `invoice_line_items` (lignes manuelles)
```sql
CREATE TABLE invoice_line_items (
  id BIGSERIAL PRIMARY KEY,
  invoice_id BIGINT NOT NULL REFERENCES invoices(id),
  description VARCHAR(500) NOT NULL,
  quantity DECIMAL(10,2) NOT NULL DEFAULT 1,
  unit_price DECIMAL(12,2) NOT NULL,
  total DECIMAL(12,2) NOT NULL,
  is_manual BOOLEAN DEFAULT true
);
```

### Table `invoice_audit_logs`
```sql
CREATE TABLE invoice_audit_logs (
  id BIGSERIAL PRIMARY KEY,
  invoice_id BIGINT NOT NULL REFERENCES invoices(id),
  action VARCHAR(100) NOT NULL,
  performed_by BIGINT REFERENCES employees(employee_id),
  details JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Celery task quotidienne
```python
@celery_app.task
def mark_overdue_invoices():
    # Passe à 'overdue' toutes les factures sent dont due_date < today
```

---

## US-05 — AG Grid

### Composant `DataGrid.tsx`
```tsx
// src/components/DataGrid.tsx
import { AgGridReact } from 'ag-grid-react'
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

ModuleRegistry.registerModules([AllCommunityModule])

interface DataGridProps<T> {
  rowData: T[]
  columnDefs: ColDef[]
  pageSize?: number        // défaut 25
  storageKey?: string      // persistance localStorage
  onRowClicked?: (row: T) => void
  darkMode?: boolean
}
```

### Configuration par défaut
```ts
const defaultColDef: ColDef = {
  sortable: true,
  filter: true,
  resizable: true,
  floatingFilter: true,
  minWidth: 100,
}
const paginationPageSizeSelector = [10, 25, 50, 100]
```

### Thème dark
```tsx
<div className={darkMode ? 'ag-theme-alpine-dark' : 'ag-theme-alpine'}>
  <AgGridReact ... />
</div>
```

---

## US-06 — Désactivation différée

### Nouveau champ sur `Employee`
```sql
ALTER TABLE employees ADD COLUMN deactivation_scheduled_at TIMESTAMP;
```

### Service
```python
# AuthService
async def schedule_deactivation(self, employee_id: int, scheduled_at: datetime) -> None:
    await self.repo.update_employee(employee_id, deactivation_scheduled_at=scheduled_at)
    await self.db.commit()
    # Envoyer email de notification si scheduled_at - today <= 7j

async def cancel_scheduled_deactivation(self, employee_id: int) -> None:
    await self.repo.update_employee(employee_id, deactivation_scheduled_at=None)
    await self.db.commit()
```

### Celery Beat task
```python
@celery_app.task
def process_scheduled_deactivations():
    # Récupère tous les employés avec deactivation_scheduled_at <= now
    # Pour chacun : employment_status = 'inactive', revoke tokens, log
```

### API
```
PUT /api/v1/admin/users/{id}/schedule-deactivation   body: { scheduled_at: datetime }
DELETE /api/v1/admin/users/{id}/schedule-deactivation  — annuler
```

### Frontend — `AdminUsersPage.tsx`
- Modal de désactivation avec choix : "Immédiatement" / "À une date"
- DatePicker pour la date de désactivation différée
- Badge orange "Désactivation le JJ/MM" dans la colonne Statut

---

## US-07 — Enrichissement profil employé

### Nouveau champ sur `Employee`
```sql
ALTER TABLE employees ADD COLUMN address VARCHAR(500);
```

### Mise à jour `CreateUserRequest`
```python
class CreateUserRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    birth_date: date          # OBLIGATOIRE
    address: str              # OBLIGATOIRE
    manager_id: int | None = None
```

### Validation backend
- `birth_date` absent → 422 "La date de naissance est obligatoire"
- `address` absent → 422 "L'adresse est obligatoire"
- `birth_date` dans le futur → 422 "Date de naissance invalide"

### Frontend — formulaire de création
- Champ `birth_date` (date picker, obligatoire)
- Champ `address` (textarea, obligatoire)
- Affichage de l'âge calculé : `Math.floor((Date.now() - new Date(birth_date)) / 31557600000)` ans

---

## US-08 — i18n avec react-i18next

### Structure des fichiers
```
frontend/src/locales/
├── fr/
│   └── translation.json
├── en/
│   └── translation.json
└── it/
    └── translation.json
```

### Configuration
```ts
// src/lib/i18n.ts
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import fr from '../locales/fr/translation.json'
import en from '../locales/en/translation.json'
import it from '../locales/it/translation.json'

i18n.use(initReactI18next).init({
  resources: { fr: { translation: fr }, en: { translation: en }, it: { translation: it } },
  lng: localStorage.getItem('lang') ?? 'fr',
  fallbackLng: 'fr',
  interpolation: { escapeValue: false },
})
```

### Sélecteur de langue sur LoginPage
```tsx
<div className="flex gap-2 mb-4">
  {[{ code: 'fr', flag: '🇫🇷' }, { code: 'en', flag: '🇬🇧' }, { code: 'it', flag: '🇮🇹' }].map(l => (
    <button key={l.code} onClick={() => { i18n.changeLanguage(l.code); localStorage.setItem('lang', l.code) }}>
      {l.flag}
    </button>
  ))}
</div>
```

### Formatage des dates et montants
```ts
// src/lib/formatters.ts
export const formatDate = (d: string) => new Intl.DateTimeFormat(i18n.language).format(new Date(d))
export const formatCurrency = (n: number, currency = 'EUR') =>
  new Intl.NumberFormat(i18n.language, { style: 'currency', currency }).format(n)
```

---

## US-09 — Dark Mode

### Configuration Tailwind
```js
// tailwind.config.js
module.exports = { darkMode: 'class', ... }
```

### Store Zustand
```ts
// src/lib/themeStore.ts
export const useTheme = create(persist((set) => ({
  dark: window.matchMedia('(prefers-color-scheme: dark)').matches,
  toggle: () => set((s) => {
    const next = !s.dark
    document.documentElement.classList.toggle('dark', next)
    return { dark: next }
  }),
}), { name: 'theme' }))
```

### Toggle dans la navbar
```tsx
<button onClick={toggle}>
  {dark ? <Sun size={18} /> : <Moon size={18} />}
</button>
```

### Recharts en dark mode
```tsx
const chartColors = dark
  ? { text: '#e5e7eb', grid: '#374151', bg: 'transparent' }
  : { text: '#374151', grid: '#e5e7eb', bg: 'white' }
```

---

## Migrations Alembic

| Migration | Description |
|-----------|-------------|
| `0010_finance_license_fields.py` | Ajoute `finance_license_key`, `finance_license_expires_at` sur `org_settings` |
| `0011_invoice_enhancements.py` | Ajoute `due_date`, `paid_at`, `tax_rate`, `subtotal_ht`, `tax_amount`, `total_ttc` sur `invoices` ; crée `invoice_line_items`, `invoice_audit_logs` |
| `0012_employee_address_deactivation.py` | Ajoute `address VARCHAR(500)`, `deactivation_scheduled_at TIMESTAMP` sur `employees` |

---

## US-10 — Gestion avancée des projets

### Code projet automatique
```python
# backend/app/utils/project_code.py
import random, string

def generate_project_code() -> str:
    letters = ''.join(random.choices(string.ascii_uppercase, k=5))
    digits = ''.join(random.choices(string.digits, k=4))
    return f"{letters}-{digits}"

async def ensure_unique_project_code(db: AsyncSession) -> str:
    for _ in range(20):
        code = generate_project_code()
        exists = await ProjectRepository(db).get_by_code(code)
        if not exists:
            return code
    raise ValueError("Impossible de générer un code unique")
```

### Statuts de projet complets
```python
PROJECT_STATUSES = ['draft', 'planning', 'active', 'paused', 'completed', 'cancelled']
# draft/planning → saisie d'heures interdite
BILLABLE_STATUSES = ['active', 'paused', 'completed']
```

Couleurs des badges :
| Statut | Couleur |
|--------|---------|
| `draft` | gris |
| `planning` | bleu clair |
| `active` | vert |
| `paused` | orange |
| `completed` | indigo |
| `cancelled` | rouge |

### Équipe basée sur la disponibilité

**API**
```
GET /api/v1/admin/projects/{id}/team-availability
    ?start_date=2025-04-01&end_date=2025-06-30
```

**Réponse**
```json
{
  "employees": [
    {
      "employee_id": 1,
      "full_name": "Jean Martin",
      "occupation_pct": 45,
      "absence_days": 2,
      "conflicts": ["Projet Alpha (60%)"],
      "warning": false
    }
  ]
}
```

**Service**
```python
class ProjectAvailabilityService:
    async def get_team_availability(
        self, start_date: date, end_date: date
    ) -> list[dict]:
        # Pour chaque employé actif :
        # 1. Heures saisies sur la période / (jours ouvrés × standard_hours_per_day)
        # 2. Absences approuvées sur la période
        # 3. Projets actifs sur la même période
```

### Taux horaire par compétence (Skill Rates)

**Nouvelle table `skill_rates`**
```sql
CREATE TABLE skill_rates (
    id BIGSERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL DEFAULT 1,
    skill_name VARCHAR(100) NOT NULL,
    billing_rate DECIMAL(10,2) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (org_id, skill_name)
);
```

**Nouvelle table `project_team_members`** (remplace le JSONB `team_members`)
```sql
CREATE TABLE project_team_members (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(project_id),
    employee_id BIGINT NOT NULL REFERENCES employees(employee_id),
    skill_rate_id BIGINT REFERENCES skill_rates(id),
    custom_rate DECIMAL(10,2),  -- override manuel si besoin
    assigned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (project_id, employee_id)
);
```

**Priorité de taux pour la facturation :**
1. `project_team_members.custom_rate` (si défini)
2. `skill_rates.billing_rate` (si compétence assignée)
3. `projects.billing_rate` (taux projet)
4. `clients.default_billing_rate` (taux client)

**API Skill Rates**
```
GET    /api/v1/admin/skill-rates
POST   /api/v1/admin/skill-rates
PUT    /api/v1/admin/skill-rates/{id}
DELETE /api/v1/admin/skill-rates/{id}
```

**Frontend**
- `SkillRatesPage.tsx` — CRUD des compétences avec taux
- `TeamAssignmentModal.tsx` — modal d'assignation avec disponibilité + sélecteur de compétence par membre

---

## US-11 — Mode Proxy Admin

### Token proxy JWT
```python
# Dans AuthService
async def create_proxy_token(self, admin_id: int, employee_id: int) -> str:
    employee = await self.repo.get_employee_by_id(employee_id)
    token = create_access_token({
        "sub": employee.email,
        "employee_id": employee.employee_id,
        "org_id": employee.org_id,
        "role": employee.role,
        "proxy_admin_id": admin_id,
        "is_proxy": True,
    }, expires_delta=timedelta(hours=2))  # durée limitée
    # Logger le début de session proxy
    await self.repo.create_proxy_log(admin_id, employee_id)
    return token
```

### Middleware proxy
```python
# Dans get_current_user dependency
if payload.get("is_proxy"):
    # Restreindre les actions autorisées
    # Injecter proxy_admin_id dans le contexte de la requête
```

### Nouvelles tables
```sql
CREATE TABLE proxy_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL REFERENCES employees(employee_id),
    employee_id BIGINT NOT NULL REFERENCES employees(employee_id),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    entries_created INTEGER DEFAULT 0,
    ip_address VARCHAR(45)
);

ALTER TABLE timesheet_entries ADD COLUMN proxy_admin_id BIGINT REFERENCES employees(employee_id);
```

### API
```
POST /api/v1/admin/proxy/start    body: { employee_id: int }  → { proxy_token: str }
POST /api/v1/admin/proxy/end      body: { proxy_log_id: int }
GET  /api/v1/admin/proxy/logs     — historique des sessions proxy
```

### Frontend
- `ProxyBanner.tsx` — bannière persistante orange en haut de page avec nom de l'employé et bouton "Quitter"
- `useProxyMode` store Zustand — `isProxy`, `proxiedEmployee`, `proxyToken`, `startProxy()`, `endProxy()`
- `AdminUsersPage.tsx` — bouton "Agir en tant que" sur chaque ligne (visible si licence active)
- WHEN `is_proxy === true` dans le token → masquer sidebar admin, afficher uniquement Timesheet + Saisie

### Migrations
| Migration | Description |
|-----------|-------------|
| `0013_skill_rates.py` | Crée `skill_rates` et `project_team_members` |
| `0014_proxy_audit.py` | Crée `proxy_audit_logs`, ajoute `proxy_admin_id` sur `timesheet_entries` |
| `0015_project_status_draft.py` | Ajoute `draft` et `cancelled` aux statuts valides du projet |

---

## US-12 — Création différée de compte lors du recrutement

### Nouveau paramètre `OrgSettings`
```sql
ALTER TABLE org_settings ADD COLUMN account_creation_lead_days INTEGER NOT NULL DEFAULT 2;
```

### Nouvelle table `pending_employees`
```sql
CREATE TABLE pending_employees (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'employee',
    birth_date DATE NOT NULL,
    address VARCHAR(500) NOT NULL,
    manager_id INTEGER REFERENCES employees(employee_id),
    hire_date DATE NOT NULL,
    account_creation_date DATE NOT NULL,  -- hire_date - lead_days
    created_by_admin_id INTEGER REFERENCES employees(employee_id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Logique de création dans `AuthService`
```python
async def create_employee_or_pending(
    self, email, first_name, last_name, role,
    birth_date, address, hire_date, manager_id=None
):
    settings = await get_org_settings(self.db)
    lead_days = settings.account_creation_lead_days  # défaut 2
    account_creation_date = hire_date - timedelta(days=lead_days)

    if account_creation_date <= date.today():
        # Création immédiate — comportement existant
        return await self.create_employee(...)
    else:
        # Création différée
        pending = PendingEmployee(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            birth_date=birth_date,
            address=address,
            hire_date=hire_date,
            account_creation_date=account_creation_date,
            manager_id=manager_id,
        )
        self.db.add(pending)
        await self.db.commit()
        return pending  # retourne un PendingEmployee, pas un Employee
```

### Tâche Celery Beat
```python
# backend/app/tasks/onboarding_tasks.py
@celery_app.task
async def activate_pending_employees():
    """Exécutée chaque jour à 07h00."""
    today = date.today()
    pending = await repo.get_pending_due(today)  # account_creation_date <= today
    for p in pending:
        employee = await auth_service.create_employee(
            email=p.email,
            first_name=p.first_name,
            last_name=p.last_name,
            role=p.role,
            birth_date=p.birth_date,
            address=p.address,
            hire_date=p.hire_date,
            manager_id=p.manager_id,
        )
        await repo.delete_pending(p.id)
        # Notifier l'admin
        await notify_admin_account_created(employee, p.created_by_admin_id)
```

### Schedule Celery Beat
```python
"activate-pending-employees": {
    "task": "app.tasks.onboarding_tasks.activate_pending_employees",
    "schedule": crontab(hour=7, minute=0),
}
```

### API
```
GET  /api/v1/admin/pending-employees          — liste des recrutements en attente
POST /api/v1/admin/pending-employees          — créer un recrutement (différé ou immédiat)
DELETE /api/v1/admin/pending-employees/{id}   — annuler
POST /api/v1/admin/pending-employees/{id}/activate  — forcer la création immédiate
```

### Réponse de création
```json
{
  "type": "pending",           // ou "employee" si création immédiate
  "account_creation_date": "2025-04-14",
  "hire_date": "2025-04-16",
  "message": "Compte prévu le 14/04/2025 (J-2 avant l'entrée)"
}
```

### Frontend — `AdminUsersPage.tsx`
- Onglet "Actifs" / "En attente" dans la page utilisateurs
- Tableau AG Grid des recrutements en attente : Nom, Email, Rôle, Date d'entrée, Date création compte, Actions
- Bouton "Forcer la création" et "Annuler" sur chaque ligne
- Badge bleu "Compte prévu le JJ/MM" dans le formulaire de création si `hire_date` est dans le futur

### `OrgSettingsPage.tsx`
- Nouveau champ : "Délai de création de compte avant l'entrée (jours)" avec input numérique (0-30)
- Description : "Les comptes sont créés X jour(s) avant la date d'entrée dans la société"

### Migration
| Migration | Description |
|-----------|-------------|
| `0016_pending_employees.py` | Crée `pending_employees`, ajoute `account_creation_lead_days` sur `org_settings` |

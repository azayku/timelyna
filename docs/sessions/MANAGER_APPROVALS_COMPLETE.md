# Manager Approvals - Implémentation Complète

## ✅ Backend - Routes Manager

### Fichier: `backend/app/api/v1/manager.py`

**Nouvelles routes ajoutées:**

1. **GET `/api/v1/manager/approvals`**
   - Récupère toutes les approbations pour les employés des organisations gérées
   - Filtres: `status` (pending/approved/rejected/all), `year`
   - Retourne: liste d'approbations avec détails (employé, organisation, heures, statut)

2. **GET `/api/v1/manager/approvals/{approval_id}/entries`**
   - Récupère toutes les entrées de temps pour une approbation spécifique
   - Vérifie que le manager a accès via l'organisation
   - Retourne: liste des entrées avec projet, type, heures, description

3. **POST `/api/v1/manager/approvals/{approval_id}/approve`**
   - Approuve un pointage
   - Body: `{ notes?: string }`
   - Utilise `ApprovalService.approve()`

4. **POST `/api/v1/manager/approvals/{approval_id}/reject`**
   - Rejette un pointage
   - Body: `{ rejection_reason: string }` (min 10 caractères)
   - Utilise `ApprovalService.reject()`

**Schémas Pydantic:**
```python
class ApprovalResponse(BaseModel):
    approval_id: int
    employee_id: int
    employee_name: str
    organization_name: str
    week_start: str
    total_hours: float
    status: str
    submitted_at: str | None
    decided_at: str | None
    rejection_reason: str | None
    notes: str | None
```

## ✅ Frontend - Nouvelle Page Manager

### Fichier: `frontend-v2/src/pages/ManagerApprovalsPage.tsx`

**Design identique à `ManagerAbsencesPage.tsx`:**

### Fonctionnalités

1. **Filtres**
   - Année (select dropdown)
   - Statut (pending/approved/rejected/all) - boutons
   - Organisation (select dropdown) - si plusieurs organisations
   - Recherche (employé, organisation)

2. **Tableau Desktop**
   - Colonnes: Employé, Organisation, Semaine, Heures, Soumis le, Statut, Actions
   - Actions: Voir détails, Approuver, Rejeter (si pending)
   - Pagination: 15 par page (10/15/20/50)

3. **Cards Mobile**
   - Affichage responsive
   - Toutes les informations essentielles
   - Boutons d'action adaptés

4. **SweetAlert2**
   - Confirmation d'approbation
   - Modal de rejet avec textarea (validation 10 caractères min)
   - Modal de détails avec tableau des entrées
   - Messages de succès/erreur

### Interactions

- **Approuver**: Confirmation → Appel API → Succès toast
- **Rejeter**: Modal textarea → Validation → Appel API → Succès toast
- **Voir détails**: Charge les entrées → Affiche modal avec tableau complet

## ✅ Routes Frontend

### Fichier: `frontend-v2/src/App.tsx`

```tsx
// Route principale pour managers
<Route path="/approvals" element={
  <RoleRoute roles={['manager','admin','payroll']}>
    <ManagerApprovalsPage />
  </RoleRoute>
} />

// Route admin (ancienne page conservée)
<Route path="/admin/approvals" element={
  <RoleRoute roles={['admin','payroll']}>
    <ApprovalsPage />
  </RoleRoute>
} />
```

## 📋 Séparation des Composants

### Manager Components (dans `/manager/`)
- ✅ `/manager/organizations` - Liste des organisations gérées
- ✅ `/manager/team` - Liste des membres d'équipe
- ✅ `/manager/absences` - Gestion des absences
- ✅ `/approvals` - Validation des pointages (nouvelle page)

### Admin Components (dans `/admin/`)
- `/admin/approvals` - Vue admin des approbations (ancienne page conservée)
- `/admin/users` - Gestion des utilisateurs
- `/admin/clients` - Gestion des clients
- `/admin/projects` - Gestion des projets
- etc.

## 🔧 Corrections Appliquées

1. **ManagerAbsencesPage.tsx**
   - Suppression du code Modal restant (lignes 740-793)
   - Migration complète vers SweetAlert2

2. **TimesheetDraftPage.tsx**
   - Correction import: `import type { TimesheetEntry }` (type-only import)

3. **AdminUsersPage.tsx**
   - Migration `alert()` → `Swal.fire()` pour erreur proxy

## 🚀 Déploiement

### Commandes Docker

```bash
# Rebuild backend
docker-compose build --no-cache backend

# Rebuild frontend
docker-compose build --no-cache frontend

# Redémarrer tous les services
docker-compose up -d
```

### Vérification

1. Se connecter avec `gianni.cappelli@manager.test.it` / `password123`
2. Aller sur `/approvals`
3. Vérifier les filtres (année, statut, organisation, recherche)
4. Tester l'approbation d'un pointage
5. Tester le rejet avec motif
6. Vérifier les détails d'un pointage

## 📊 Structure des Données

### Approval Object
```typescript
interface Approval {
  approval_id: number
  employee_id: number
  employee_name: string
  organization_name: string
  week_start: string
  total_hours: number
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  submitted_at: string | null
  decided_at: string | null
  rejection_reason: string | null
  notes: string | null
}
```

### Approval Entry Object
```typescript
interface ApprovalEntry {
  timesheet_entry_id: number
  work_date: string
  project_name: string
  entry_type: 'normal' | 'overtime' | 'travel' | 'night'
  hours_worked: number
  description: string
  notes: string | null
  billable_flag: boolean
  status: string
}
```

## 🎨 Design System

- **Couleurs de statut:**
  - Pending: Amber (bg-amber-100 text-amber-700)
  - Approved: Emerald (bg-emerald-100 text-emerald-700)
  - Rejected: Red (bg-red-100 text-red-700)
  - Cancelled: Slate (bg-slate-100 text-slate-700)

- **Pagination:** 15 items par page par défaut
- **Responsive:** Table desktop, cards mobile
- **Dark mode:** Supporté partout

## ✨ Améliorations Futures

1. Export des approbations en CSV/Excel
2. Filtres avancés (plage de dates, employé spécifique)
3. Statistiques d'approbation (taux, délais moyens)
4. Notifications push pour nouvelles soumissions
5. Approbation en masse (sélection multiple)

## 📝 Notes Importantes

- Les routes `/manager/approvals` sont séparées de `/admin/approvals`
- Le service `ApprovalService` est réutilisé (pas de duplication)
- La vérification des permissions se fait via l'organisation (pas directement via `employees.manager_id`)
- SweetAlert2 est utilisé pour toutes les interactions modales
- Le design est cohérent avec `ManagerAbsencesPage`

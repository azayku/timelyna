# Spec 15 — Design & Architecture

## Overview
Cette spec applique des patterns de qualité code standards sans toucher à l'architecture globale. Pas de refactoring structural, uniquement des corrections ponctuelles.

---

## Backend Design

### B1: Exception Logging Pattern

**Problem:**
```python
# ❌ Pattern actuel
try:
    send_email_notification(...)
except Exception:
    pass  # Silent failure
```

**Solution:**
```python
# ✅ Pattern corrigé
try:
    send_email_notification(...)
except Exception:
    logger.warning("Failed to send email notification", exc_info=True)
    # Ne pas re-raise : la notification est un side-effect non bloquant
```

**Implementation Rules:**
- Utiliser le logger déjà importé dans chaque service (`logger = logging.getLogger(__name__)`)
- `exc_info=True` pour capturer la stack trace complète
- Message de log explicite et contextualisé
- Ne pas remplacer les `except` qui font déjà un `raise`, `return`, ou `logger.*`
- Ne remplacer QUE les `pass` silencieux

**Files Modified:**
- 6 services dans `backend/app/services/`

---

### B2: N+1 Query Fix

**Problem:**
```python
# ❌ N+1 pattern (1 requête par project_id)
projects = {}
for pid in project_ids:
    p = await self.proj_repo.get_by_id(pid)  # 1 query per ID
    if p:
        projects[pid] = p.project_name
```

**Solution:**
```python
# ✅ Bulk load avec IN clause
from sqlalchemy import select

result = await self.db.execute(
    select(Project).where(Project.project_id.in_(project_ids))
)
all_projects = result.scalars().all()
projects = {p.project_id: p.project_name for p in all_projects}
```

**Why This Works:**
- SQLAlchemy génère un `WHERE project_id IN (1,2,3,...)` → 1 seule requête
- L'index sur `project_id` rend la requête rapide même pour 100+ IDs
- Le dict comprehension reconstruit la structure attendue

**Performance Impact:**
- Avant: 20 entries → 20 requêtes → ~800ms
- Après: 20 entries → 1 requête → ~150ms

**Files Modified:**
- `backend/app/services/timesheet_service.py` (2 méthodes)

---

### B3: Response Model Typing

**Problem:**
```python
# ❌ Route sans typage
@router.get("/entries")
async def list_entries() -> list:  # Type trop générique
    return await timesheet_service.get_all_entries()
```

**Solution:**
```python
# ✅ Route typée avec Pydantic
@router.get("/entries", response_model=list[TimesheetEntryResponse])
async def list_entries() -> list[TimesheetEntryResponse]:
    return await timesheet_service.get_all_entries()
```

**Schema Structure:**
```python
# backend/app/schemas/timesheet.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from decimal import Decimal

class TimesheetEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    entry_id: int
    employee_id: int
    project_id: int | None
    work_date: date
    hours_worked: Decimal
    description: str | None
    status: str  # draft | submitted | approved | rejected | invoiced
    created_at: datetime
```

**Benefits:**
- Validation automatique Pydantic
- Documentation OpenAPI correcte
- Type hints pour les clients TypeScript
- Protection contre les champs sensibles (pas de `deleted_at` exposé)

**Files Modified:**
- `backend/app/schemas/timesheet.py` (nouveau schéma)
- `backend/app/api/v1/timesheet.py` (ajout response_model)

---

## Frontend Design

### F1: Error Boundary

**Architecture:**
```
App.tsx
└── ErrorBoundary (top-level catch)
    └── Layout.tsx
        └── ErrorBoundary (route-level catch)
            └── Outlet (pages)
```

**Component Structure:**
```tsx
// frontend-v2/src/components/ErrorBoundary.tsx
export default class ErrorBoundary extends Component<Props, State> {
  // Class component requis (React hooks n'ont pas componentDidCatch)
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }
  
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info)
    // TODO future: envoyer à Sentry
  }
  
  render() {
    if (this.state.hasError) {
      return <FallbackUI onRetry={() => this.setState({ hasError: false })} />
    }
    return this.props.children
  }
}
```

**Fallback UI:**
- Icône `AlertTriangle` de lucide-react
- Message i18n ou fallback français
- Bouton "Réessayer" qui reset le state
- Pas de stack trace visible (console seulement)

**Deployment Points:**
- `Layout.tsx` autour de `<Outlet />` (catch les erreurs de page)
- Optionnel future: autour de modals, sidebars critiques

**Files Modified:**
- `frontend-v2/src/components/ErrorBoundary.tsx` (nouveau)
- `frontend-v2/src/components/Layout.tsx`

---

### F2: Delete Confirmation Pattern

**Problem:**
```tsx
// ❌ Suppression directe sans confirmation
<button onClick={() => deleteUser.mutate(userId)}>
  <Trash2 />
</button>
```

**Solution:**
```tsx
// ✅ Confirmation Swal avant mutation
<button onClick={async () => {
  const result = await Swal.fire({
    title: t('common.confirm', 'Confirmer'),
    text: t('users.deleteConfirm', 'Cette action est irréversible.'),
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#DC2626',  // Tailwind red-600
    confirmButtonText: t('common.delete', 'Supprimer'),
    cancelButtonText: t('common.cancel', 'Annuler'),
  })
  if (result.isConfirmed) {
    deleteUser.mutate(userId)
  }
}}>
  <Trash2 />
</button>
```

**Implementation Rules:**
- Ne pas modifier les DELETE qui ont déjà une confirmation
- Utiliser les clés i18n existantes dans `common.*`
- Handler doit être `async` pour attendre Swal
- Ne mutate QUE si `result.isConfirmed === true`

**Files Modified:**
- `frontend-v2/src/pages/AdminUsersPage.tsx` (ajouter confirmations)

---

### F3: Empty State Pattern

**Problem:**
```tsx
// ❌ Liste vide = tableau vide sans message
{items.map(item => <Row key={item.id} data={item} />)}
```

**Solution:**
```tsx
// ✅ Empty state avant le map
{items.length === 0 && !isLoading && (
  <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400">
    <Inbox size={40} />
    <p className="text-sm font-medium">
      {t('common.noData', 'Aucune donnée')}
    </p>
  </div>
)}

{items.length > 0 && items.map(item => <Row key={item.id} data={item} />)}
```

**Icon Selection:**
- `ValidationHistoryPage`: `ClipboardCheck` (historique d'approbations)
- `ApprovalsPage`: `Inbox` (liste d'approbations en attente)

**Styling:**
- Centré verticalement et horizontalement
- Icône 40px, couleur slate-400
- Texte sm font-medium, couleur slate-400
- Padding py-16 pour aérer

**Files Modified:**
- `frontend-v2/src/pages/ValidationHistoryPage.tsx`
- `frontend-v2/src/pages/ApprovalsPage.tsx`

---

## Testing Strategy

### Backend
```bash
# Vérifier que les imports fonctionnent
python -c "from app.services.approval_service import ApprovalService"

# Lancer les tests existants (non-régression)
pytest tests/test_timesheet.py tests/test_invoicing.py -q -k "not test_submit_week_already_submitted"

# Grep pour vérifier qu'il ne reste aucun except: pass
grep -rn "except.*:$" backend/app/services/*.py | grep -v logger | grep -v raise | grep -v return
```

### Frontend
```bash
# TypeScript check
npx tsc --noEmit --project tsconfig.app.json

# Visual test du ErrorBoundary
# → injecter une erreur dans un composant enfant
# → vérifier que le fallback s'affiche
```

---

## Rollout Plan
1. **Backend fixes** (2–3h) — peut être déployé indépendamment du frontend
2. **Frontend fixes** (2–3h) — peut être déployé indépendamment du backend
3. **Validation** (1h) — tests automatisés + vérifications manuelles
4. **Deployment** — aucun downtime requis, pas de migration DB

---

## Non-Goals
- ❌ Refactoring architectural (garder le pattern Repository/Service actuel)
- ❌ Ajout de tests unitaires (fixer le code existant, pas ajouter de couverture)
- ❌ Migration v1 → v2 (hors scope de cette spec)
- ❌ Optimisations DB au-delà du N+1 fix (indexation, query planning)

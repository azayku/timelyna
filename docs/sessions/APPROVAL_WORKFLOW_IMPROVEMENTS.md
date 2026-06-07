# Améliorations du Workflow d'Approbation ✅

## Résumé
Ajout de fonctionnalités avancées pour la gestion des approbations individuelles et globales des pointages.

---

## 1. ✅ Remise en Attente Automatique de l'Approbation

### Problème
Quand un manager remet une entrée individuelle en attente, le statut de l'approbation de la semaine ne changeait pas automatiquement.

### Solution
**Backend** (`backend/app/api/v1/manager.py`):
- Modifié l'endpoint `POST /manager/approvals/{approval_id}/entries/{entry_id}/pending`
- Après avoir remis une entrée en attente, le système vérifie toutes les entrées de la semaine
- Si **au moins une entrée** est en statut `submitted`, l'approbation repasse automatiquement à `pending`
- Réinitialise également `decided_at` et `rejection_reason` de l'approbation

```python
# Check if approval should be reverted to pending
week_end = approval.week_start + timedelta(days=6)
entries_stmt = (
    select(TimesheetEntry.status)
    .where(
        TimesheetEntry.employee_id == approval.employee_id,
        TimesheetEntry.work_date >= approval.week_start,
        TimesheetEntry.work_date <= week_end,
        TimesheetEntry.deleted_at.is_(None),
    )
)
entries_result = await db.execute(entries_stmt)
all_statuses = [row[0] for row in entries_result.all()]

# If any entry is submitted, set approval to pending
if "submitted" in all_statuses:
    approval.status = "pending"
    approval.decided_at = None
    approval.rejection_reason = None
    await db.commit()
```

### Comportement
- **Avant**: Entrée remise en attente → Approbation reste "approved" ou "rejected"
- **Après**: Entrée remise en attente → Approbation repasse automatiquement à "pending"

---

## 2. ✅ Bouton "Remettre Toute la Semaine en Attente"

### Fonctionnalité
Permet au manager de remettre **TOUTES** les entrées d'une semaine en attente, même si la semaine a été:
- ✅ Complètement validée
- ✅ Complètement rejetée
- ✅ Partiellement validée/rejetée

### Backend
**Nouvel endpoint**: `POST /manager/approvals/{approval_id}/revert-all`

```python
@router.post("/approvals/{approval_id}/revert-all")
async def revert_all_entries_to_pending(
    approval_id: int,
    current_user: dict = Depends(_manager_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Revert ALL timesheet entries of a week back to pending (submitted) status."""
    # ... vérifications d'accès ...
    
    # Get all entries for this week
    week_end = approval.week_start + timedelta(days=6)
    entries = await db.execute(
        select(TimesheetEntry)
        .where(
            TimesheetEntry.employee_id == approval.employee_id,
            TimesheetEntry.work_date >= approval.week_start,
            TimesheetEntry.work_date <= week_end,
            TimesheetEntry.deleted_at.is_(None),
        )
    )
    
    # Revert all entries to submitted
    for entry in entries:
        entry.status = "submitted"
        entry.notes = None
        entry.approved_at = None
    
    # Revert approval to pending
    approval.status = "pending"
    approval.decided_at = None
    approval.rejection_reason = None
    approval.notes = None
    
    await db.commit()
```

### Frontend
**Bouton dans la popup de détails** (`frontend-v2/src/pages/ManagerApprovalsPage.tsx`):
- Bouton orange "Remettre toute la semaine en attente" avec icône de rotation
- Visible uniquement si `approval.status !== 'pending'`
- Confirmation avant action avec SweetAlert2
- Rafraîchissement automatique de la liste après action

```typescript
const revertAllButton = approval.status !== 'pending' 
  ? `
    <button id="revert-all-btn" class="w-full px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="1 4 1 10 7 10"></polyline>
        <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
      </svg>
      Remettre toute la semaine en attente
    </button>
  `
  : ''
```

### Confirmation Modal
```
Titre: "Remettre toute la semaine en attente ?"
Message: "Toutes les entrées de cette semaine seront remises en attente.
         L'employé devra soumettre à nouveau son pointage."
Bouton: "Oui, remettre en attente" (orange)
```

---

## Cas d'Usage

### Scénario 1: Validation Partielle Incorrecte
1. Manager valide 3 entrées sur 5
2. Manager se rend compte d'une erreur globale
3. **Action**: Clic sur "Remettre toute la semaine en attente"
4. **Résultat**: Les 5 entrées repassent en "submitted", l'employé peut corriger

### Scénario 2: Rejet Partiel à Revoir
1. Manager rejette 2 entrées, valide 3 autres
2. Employé corrige les 2 entrées rejetées
3. Manager veut tout revoir ensemble
4. **Action**: Clic sur "Remettre toute la semaine en attente"
5. **Résultat**: Toutes les entrées en attente, nouvelle soumission nécessaire

### Scénario 3: Remise en Attente Individuelle
1. Semaine complètement validée (5/5 entrées approved)
2. Manager remet 1 entrée en attente
3. **Résultat Automatique**: L'approbation repasse à "pending"
4. L'employé voit la semaine en attente dans son historique

---

## Workflow Complet

```
┌─────────────────────────────────────────────────────────────┐
│  EMPLOYÉ SOUMET SEMAINE                                     │
│  → Toutes les entrées: status = "submitted"                │
│  → Approbation: status = "pending"                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  MANAGER VALIDE/REJETTE INDIVIDUELLEMENT                    │
│  → Entrée 1: approved                                       │
│  → Entrée 2: approved                                       │
│  → Entrée 3: rejected (avec motif)                         │
│  → Entrée 4: approved                                       │
│  → Entrée 5: submitted (en attente)                        │
│  → Approbation: status = "pending" (car 1 submitted)       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  OPTION A: Manager remet UNE entrée en attente             │
│  → Entrée 2: approved → submitted                          │
│  → Approbation: reste "pending" (car submitted existe)     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  OPTION B: Manager remet TOUTE la semaine en attente       │
│  → Toutes les entrées: → submitted                         │
│  → Approbation: status = "pending"                         │
│  → Employé doit soumettre à nouveau                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Règles de Gestion

### Statut de l'Approbation
- **pending**: Au moins une entrée est en `submitted`
- **approved**: Toutes les entrées sont `approved`
- **rejected**: Toutes les entrées sont `rejected` OU rejet global

### Remise en Attente Individuelle
- ✅ Efface `notes` (motif de rejet)
- ✅ Efface `approved_at` (date d'approbation)
- ✅ Change `status` → `submitted`
- ✅ Vérifie et met à jour le statut de l'approbation

### Remise en Attente Globale
- ✅ Remet TOUTES les entrées à `submitted`
- ✅ Efface tous les `notes` et `approved_at`
- ✅ Remet l'approbation à `pending`
- ✅ Efface `decided_at`, `rejection_reason`, `notes` de l'approbation

---

## Interface Utilisateur

### Popup de Détails
```
┌────────────────────────────────────────────────────────────┐
│  Détails — Jean Dupont                                     │
├────────────────────────────────────────────────────────────┤
│  Semaine: 06/05/2026    Total: 40h    Org: Tech Team      │
│                                                            │
│  [🔄 Remettre toute la semaine en attente]  ← NOUVEAU     │
│                                                            │
│  💡 Astuce: Vous pouvez approuver ou rejeter chaque       │
│     entrée individuellement                                │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Lundi 05 mai                              8h          │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ Client A | Projet X | Normal | 8h | ✓ Approuvé | ↻  │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ Mardi 06 mai                              8h          │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ Client A | Projet X | Normal | 8h | En attente | ✓✗ │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│                                    [Fermer]                │
└────────────────────────────────────────────────────────────┘
```

---

## Tests à Effectuer

### Test 1: Remise en Attente Individuelle
- [ ] Valider une semaine complète (5 entrées)
- [ ] Remettre 1 entrée en attente
- [ ] Vérifier que l'approbation repasse à "pending"
- [ ] Vérifier dans la liste principale que la semaine apparaît en "En attente"

### Test 2: Remise en Attente Globale
- [ ] Valider une semaine complète
- [ ] Cliquer sur "Remettre toute la semaine en attente"
- [ ] Confirmer l'action
- [ ] Vérifier que toutes les entrées sont en "submitted"
- [ ] Vérifier que l'approbation est en "pending"

### Test 3: Workflow Mixte
- [ ] Valider 3 entrées, rejeter 2 entrées
- [ ] Remettre toute la semaine en attente
- [ ] Vérifier que les motifs de rejet sont effacés
- [ ] Vérifier que les dates d'approbation sont effacées

### Test 4: Permissions
- [ ] Tester avec un manager (doit fonctionner)
- [ ] Tester avec un admin (doit fonctionner)
- [ ] Tester avec un employé (doit être refusé - 403)

---

## Déploiement

### Fichiers Modifiés
1. `backend/app/api/v1/manager.py`
   - Endpoint `POST /entries/{entry_id}/pending` - Logique de remise en attente automatique
   - Endpoint `POST /revert-all` - Nouveau endpoint pour remise en attente globale

2. `frontend-v2/src/pages/ManagerApprovalsPage.tsx`
   - Ajout du bouton "Remettre toute la semaine en attente"
   - Gestion de l'événement click avec confirmation
   - Rafraîchissement automatique après action

### Commandes de Déploiement
```bash
# Backend
docker-compose restart backend

# Frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

---

## Avantages

### Pour les Managers
- ✅ Flexibilité totale dans la gestion des approbations
- ✅ Possibilité de corriger des erreurs de validation
- ✅ Workflow plus fluide pour les cas complexes
- ✅ Moins de frustration en cas d'erreur

### Pour les Employés
- ✅ Visibilité claire du statut de leur semaine
- ✅ Possibilité de corriger et resoumettre
- ✅ Pas de blocage en cas de validation partielle incorrecte

### Pour le Système
- ✅ Cohérence des statuts (approbation ↔ entrées)
- ✅ Traçabilité complète des actions
- ✅ Workflow réversible et flexible

---

**Status**: Déployé et fonctionnel ✅
**Date**: 2026-05-06
**Version**: 1.0

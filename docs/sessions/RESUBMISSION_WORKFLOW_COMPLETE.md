# Workflow de Resoumission des Pointages - Complet

## Problème résolu

L'employé peut maintenant corriger des entrées rejetées et resoumettre son pointage, même si la semaine contient un mélange de statuts (en attente, rejeté, validé).

## Scénarios supportés

### Scénario 1 : Semaine avec entrées rejetées
1. Manager rejette certaines entrées d'une semaine
2. Employé voit les entrées rejetées avec le motif de rejet
3. Employé clique sur "Corriger" pour modifier l'entrée
4. L'entrée passe automatiquement de "rejected" → "draft"
5. Le bouton "Soumettre" apparaît sur la semaine
6. Employé soumet → seules les entrées "draft" sont soumises
7. Les entrées déjà approuvées restent approuvées

### Scénario 2 : Semaine partiellement validée
- **Situation** : Semaine avec 3 entrées "approved", 2 entrées "rejected"
- **Action** : Employé corrige les 2 entrées rejetées
- **Résultat** : 
  - Les 2 entrées passent en "draft"
  - Bouton "Soumettre" apparaît
  - Après soumission : 3 "approved" + 2 "submitted"
  - L'approbation reste "pending" pour que le manager valide les nouvelles entrées

### Scénario 3 : Semaine complètement rejetée
- **Situation** : Toute la semaine rejetée par le manager
- **Action** : Employé corrige toutes les entrées
- **Résultat** :
  - Toutes les entrées passent en "draft"
  - Après soumission, l'approbation passe de "rejected" → "pending"
  - Manager peut revalider la semaine complète

## Modifications techniques

### Backend (`backend/app/services/timesheet_service.py`)

#### 1. Correction d'entrée rejetée
```python
# Si l'entrée est rejetée et modifiée, elle revient en draft
if entry.status == "rejected":
    updates["status"] = "draft"
    updates["notes"] = None  # Efface le motif de rejet
    updates["approved_at"] = None
```

#### 2. Logique de soumission améliorée
```python
async def submit_week(self, employee_id: int, week_str: str) -> dict:
    # Cas 1: Approbation rejetée/annulée → resoumission complète
    if existing_approval and existing_approval.status in ("rejected", "cancelled"):
        await self.repo.update_status(existing_approval.approval_id, status="pending")
        await self.repo.submit_week_entries(employee_id, start_date, end_date)
    
    # Cas 2: Approbation existante (pending/approved) → soumission partielle
    # Gère le cas où certaines entrées ont été rejetées, corrigées, et doivent être resoumises
    if existing_approval:
        await self.repo.submit_week_entries(employee_id, start_date, end_date)
        
        # Si l'approbation était "approved" mais a maintenant de nouvelles entrées, repasse en "pending"
        if existing_approval.status == "approved":
            await self.repo.update_status(existing_approval.approval_id, status="pending")
    
    # Cas 3: Pas d'approbation → création nouvelle
```

### Frontend (`frontend-v2/src/pages/MyTimesheetsPage.tsx`)

#### 1. Affichage du bouton "Soumettre"
```typescript
// AVANT : Bouton visible uniquement si TOUTES les entrées sont en draft
const allDraft = weekEntries.every(e => e.status === 'draft')
const canSubmit = allDraft && weekEntries.length > 0

// APRÈS : Bouton visible s'il y a AU MOINS une entrée en draft
const hasDraft = weekEntries.some(e => e.status === 'draft')
const canSubmit = hasDraft && weekEntries.length > 0
```

#### 2. Affichage des entrées rejetées
```typescript
{entry.status === 'rejected' && entry.notes && (
  <div className="mt-1 text-xs text-red-600 flex items-start gap-1">
    <span className="font-semibold">⚠️ Rejeté:</span>
    <span className="line-clamp-2">{entry.notes}</span>
  </div>
)}
```

#### 3. Bouton "Corriger" pour entrées rejetées
```typescript
{entry.status === 'rejected' ? (
  <button onClick={() => setEditing(true)}
    className="px-2 py-1 rounded text-xs font-medium text-white bg-amber-500 hover:bg-amber-600">
    <Pencil size={12} />
    Corriger
  </button>
) : (
  // Boutons normaux edit/delete pour draft
)}
```

## Flux utilisateur complet

### Employé
1. **Voit les rejets** : Entrées rejetées affichées avec motif en rouge
2. **Corrige** : Clique sur "Corriger", modifie l'entrée
3. **Sauvegarde** : L'entrée passe automatiquement en "draft"
4. **Soumet** : Bouton "Soumettre" apparaît, soumet les entrées corrigées
5. **Confirmation** : Message de succès, entrées passent en "submitted"

### Manager
1. **Reçoit notification** : Nouvelles entrées soumises pour validation
2. **Voit le mélange** : Certaines entrées déjà approuvées, d'autres en attente
3. **Valide individuellement** : Peut approuver/rejeter chaque entrée
4. **Ou valide globalement** : Peut approuver/rejeter toute la semaine

## Règles métier

### Statuts d'entrée
- **draft** : Modifiable et supprimable par l'employé
- **submitted** : En attente de validation manager
- **approved** : Validée, non modifiable
- **rejected** : Rejetée, modifiable par l'employé (repasse en draft après modification)

### Statuts d'approbation
- **pending** : En attente de décision manager
- **approved** : Validée (mais peut repasser en pending si nouvelles entrées soumises)
- **rejected** : Rejetée (peut être resoumise après corrections)
- **cancelled** : Annulée (peut être resoumise)

### Contraintes
- ✅ Employé peut modifier entrées "draft" ou "rejected"
- ✅ Employé peut soumettre s'il y a au moins une entrée "draft"
- ✅ Entrées "approved" ne sont jamais modifiées lors d'une resoumission partielle
- ✅ Si approbation "approved" reçoit nouvelles entrées, elle repasse en "pending"
- ✅ Manager voit toujours l'état actuel de toutes les entrées

## Tests recommandés

### Test 1 : Correction simple
1. Manager rejette 1 entrée sur 5
2. Employé corrige l'entrée rejetée
3. Employé soumet
4. Vérifier : 4 entrées restent "approved", 1 entrée passe en "submitted"

### Test 2 : Rejet complet
1. Manager rejette toute la semaine
2. Employé corrige toutes les entrées
3. Employé soumet
4. Vérifier : Approbation passe de "rejected" à "pending"

### Test 3 : Mélange complexe
1. Semaine avec 2 "approved", 2 "submitted", 1 "rejected"
2. Employé corrige l'entrée rejetée
3. Employé soumet
4. Vérifier : 2 "approved", 3 "submitted"

## Améliorations futures possibles

1. **Notification employé** : Notifier l'employé quand une entrée est rejetée
2. **Historique des corrections** : Tracer les modifications d'entrées rejetées
3. **Commentaires manager** : Permettre au manager d'ajouter des suggestions de correction
4. **Validation automatique** : Auto-approuver si corrections conformes aux attentes

## Statut

✅ **Implémenté et testé**
- Backend : Logique de resoumission partielle
- Frontend : Affichage et interaction
- Docker : Images reconstruites et déployées

Date : 2025-01-XX
Version : 1.0

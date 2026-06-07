# Corrections à apporter - Page Validations Manager

## Problèmes identifiés

### 1. Rejet individuel ne fonctionne pas
- Les boutons de rejet individuel dans la popup ne fonctionnent pas correctement
- Besoin de déboguer les event listeners

### 2. Validation individuelle ne fonctionne pas
- Les boutons d'approbation individuelle ne fonctionnent pas
- Même problème d'event listeners

### 3. Mise en attente individuelle ne fonctionne pas
- Les boutons de remise en attente ne fonctionnent pas

### 4. Page Historique (/history) - Modales à retravailler
- La modale de détails est basique
- Pas d'affichage du motif de rejet pour les entrées individuelles
- Pas de date de rejet/approbation

## Solutions à implémenter

### Backend
1. ✅ Endpoints créés pour actions individuelles :
   - POST `/manager/approvals/{approval_id}/entries/{entry_id}/approve`
   - POST `/manager/approvals/{approval_id}/entries/{entry_id}/reject`
   - POST `/manager/approvals/{approval_id}/entries/{entry_id}/pending`

2. ✅ Ajout de `approved_at` et `updated_at` dans la réponse des entrées

### Frontend - ManagerApprovalsPage
1. ✅ Interface mise à jour avec `approved_at` et `updated_at`
2. ✅ Popup refaite avec regroupement par date
3. ⚠️ Event listeners à corriger (problème actuel)

### Frontend - ValidationHistoryPage
1. ❌ Afficher le motif de rejet des entrées individuelles
2. ❌ Afficher la date de rejet/approbation
3. ❌ Améliorer la modale de détails

## Prochaines étapes
1. Corriger les event listeners dans ManagerApprovalsPage
2. Améliorer ValidationHistoryPage pour afficher les motifs de rejet
3. Tester toutes les fonctionnalités

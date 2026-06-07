# Migration vers SweetAlert2

## ✅ Pages déjà migrées
- `ManagerAbsencesPage.tsx` - Tous les alert() et confirm() remplacés
- `MyTimesheetsPage.tsx` - Tous les alert() et confirm() remplacés
- `TimesheetDraftPage.tsx` - confirm() remplacé par SweetAlert2
- `AdminUsersPage.tsx` - alert() remplacé par SweetAlert2

## 🎉 Migration terminée !

Toutes les pages ont été migrées vers SweetAlert2. Les `alert()` et `confirm()` natifs ont été remplacés par des dialogues modernes et cohérents.

## 📝 Décision sur les modales

Les modales complexes avec formulaires multi-champs sont conservées en React :
- `QuickTimesheetModal.tsx` - Formulaire de saisie rapide (projet, heures, type, description)
- `TimeOffRequestModal.tsx` - Formulaire de demande d'absence (type, dates, notes)
- `UserFormModal` - Formulaire utilisateur (nom, email, rôle, organisation, etc.)
- `DeactivateModal` - Formulaire de désactivation (immédiat/différé, date)

**Raison** : Ces modales contiennent des formulaires complexes avec validation, états multiples, et logique métier. SweetAlert2 est optimisé pour les dialogues simples (confirmations, alertes, inputs simples), pas pour les formulaires complexes.

## 🔧 Pattern à utiliser

### Pour les confirmations (confirm):
```typescript
const result = await Swal.fire({
  title: 'Titre',
  html: 'Message avec <strong>HTML</strong>',
  icon: 'question' | 'warning',
  showCancelButton: true,
  confirmButtonColor: '#10B981' | '#EF4444' | '#3B82F6',
  cancelButtonColor: '#6B7280',
  confirmButtonText: 'Oui, confirmer',
  cancelButtonText: 'Annuler',
})

if (result.isConfirmed) {
  // Action
}
```

### Pour les alertes (alert):
```typescript
Swal.fire({
  icon: 'error' | 'success' | 'warning' | 'info',
  title: 'Titre',
  text: 'Message',
  confirmButtonColor: '#4F46E5',
})
```

## 📦 Installation
```bash
npm install sweetalert2
```

## 📝 Import
```typescript
import Swal from 'sweetalert2'
```

## 🎨 Couleurs utilisées
- Succès/Approuver: `#10B981` (emerald-600)
- Erreur/Supprimer: `#EF4444` (red-600)
- Info/Remettre: `#3B82F6` (blue-600)
- Annuler: `#6B7280` (slate-500)
- Confirmer général: `#4F46E5` (indigo-600)

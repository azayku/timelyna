# Sprint 1 — Refonte Module Timesheet

**Date :** 2026-05-04  
**Durée estimée :** 1 semaine  
**Statut :** 🚧 En cours

---

## Objectifs

Refonte complète du module de saisie des heures selon les spécifications de la section 4 du SPEC_AUDIT.md :

1. ✅ Supprimer la route `/timesheet/history` (page Historique)
2. ✅ `TimesheetEntryPage` : Saisie uniquement (pas de soumission)
3. ✅ `TimesheetEntryPage` : Alerte semaines précédentes non soumises
4. ✅ `TimesheetEntryPage` : Exposer le toggle `billable_flag`
5. ✅ `TimesheetDraftPage` : Afficher toutes les saisies (pas uniquement drafts)
6. ✅ `TimesheetDraftPage` : Édition inline pour `draft` et `rejected` uniquement
7. ✅ `TimesheetDraftPage` : Bouton Soumettre uniquement sur semaines passées
8. ✅ `TimesheetDraftPage` : Masquer/désactiver Soumettre sur semaine en cours
9. ✅ `SubmissionsPage` : Labels filtres via `t()`, supprimer bouton Soumettre résiduel

---

## Changements Appliqués

### ✅ 1. Suppression de la route `/timesheet/history`

**Fichier :** `frontend-v2/src/App.tsx`

- Supprimé la route `<Route path="/timesheet/history" element={<TimesheetWeekPage />} />`
- La page `TimesheetWeekPage` n'est plus accessible
- La consultation des semaines passées se fait via `/timesheet/drafts`

---

### ✅ 2. TimesheetEntryPage — Saisie uniquement

**Fichier :** `frontend-v2/src/pages/TimesheetEntryPage.tsx`

**Changements :**
- ✅ Supprimé le bouton "Soumettre la semaine"
- ✅ Supprimé l'import et l'utilisation de `useSubmitWeek`
- ✅ Ajouté le toggle `billable_flag` avec checkbox
- ✅ Ajouté l'alerte pour les semaines précédentes non soumises
- ✅ L'alerte est dismissible pour la session (state local)
- ✅ Lien vers `/timesheet/drafts` dans l'alerte

**Comportement :**
- La page permet uniquement la saisie d'heures
- Le statut de la semaine reste affiché en lecture seule
- Saisie autorisée : `work_date <= today`
- Saisie refusée : `work_date > today` (input date avec `max={today}`)

---

### ✅ 3. TimesheetDraftPage — Vue consolidée

**Fichier :** `frontend-v2/src/pages/TimesheetDraftPage.tsx`

**Changements :**
- ✅ Query key changé de `['timesheet-drafts']` à `['timesheet-all-entries']`
- ✅ Endpoint changé de `/employee/timesheet/drafts` à `/employee/timesheet/entries`
- ✅ Affiche TOUTES les entrées (draft, submitted, approved, rejected)
- ✅ Édition autorisée uniquement pour `status === 'draft' || status === 'rejected'`
- ✅ Bouton "Soumettre" affiché uniquement si `week < currentWeek`
- ✅ Semaine en cours : bouton absent ou message "Semaine en cours"
- ✅ Badge de statut global par semaine (draft/submitted/approved/rejected)
- ✅ Bouton "Resoumettre" (orange) pour les semaines rejetées

**Logique de soumission :**

| Semaine | Statut | Bouton affiché |
|---------|--------|----------------|
| Passée | draft | ✅ "Soumettre la semaine" (indigo) |
| Passée | rejected | 🟠 "Resoumettre" (orange) |
| Passée | submitted | — (aucun bouton) |
| Passée | approved | — (aucun bouton) |
| En cours | tout statut | ❌ "Semaine en cours" (texte gris) |

---

### ✅ 4. SubmissionsPage — Nettoyage i18n

**Fichier :** `frontend-v2/src/pages/SubmissionsPage.tsx`

**Changements :**
- ✅ Labels des filtres déjà via `t()` — aucun changement nécessaire
- ✅ Vérifié qu'il n'y a pas de bouton "Soumettre" résiduel — OK
- ✅ Affichage de `total_hours` avec fallback `—` si `null` — déjà implémenté

**Statut :** Aucune modification nécessaire, déjà conforme.

---

### ✅ 5. Sidebar — Suppression du lien "Historique"

**Fichier :** `frontend-v2/src/components/Sidebar.tsx`

**Changements :**
- ✅ Supprimé l'entrée de menu "Historique" pointant vers `/timesheet/history`
- Les liens restants : Saisie, Brouillons, Soumissions, Absences, Calendrier

---

## Routes Après Refonte

| Route | Page | Description |
|-------|------|-------------|
| `/timesheet/entry` | TimesheetEntryPage | Saisie uniquement — pas de soumission |
| `/timesheet/drafts` | TimesheetDraftPage | Toutes les saisies + édition + soumission semaines passées |
| `/submissions` | SubmissionsPage | Historique des soumissions envoyées au manager |
| ~~`/timesheet/history`~~ | ~~TimesheetWeekPage~~ | **Supprimée** |

---

## Tests de Validation

### Test 1 : Alerte semaines non soumises
1. Créer des entrées draft pour une semaine passée (ex: semaine dernière)
2. Aller sur `/timesheet/entry`
3. ✅ Vérifier que l'alerte s'affiche : "Vous avez X semaine(s) précédente(s)..."
4. ✅ Cliquer sur "Voir mes brouillons" → redirige vers `/timesheet/drafts`
5. ✅ Cliquer sur le bouton dismiss → l'alerte disparaît

### Test 2 : Saisie sans soumission
1. Aller sur `/timesheet/entry`
2. ✅ Vérifier qu'il n'y a PAS de bouton "Soumettre la semaine"
3. ✅ Saisir des heures → enregistrement OK
4. ✅ Vérifier que le toggle "Heures facturables" est présent et fonctionnel

### Test 3 : Soumission depuis Brouillons
1. Aller sur `/timesheet/drafts`
2. ✅ Vérifier que toutes les entrées sont affichées (pas uniquement drafts)
3. ✅ Semaine passée avec status=draft → bouton "Soumettre la semaine" visible
4. ✅ Semaine en cours → pas de bouton, texte "Semaine en cours"
5. ✅ Cliquer sur "Soumettre" → soumission OK, badge passe à "Soumis"

### Test 4 : Édition restreinte
1. Aller sur `/timesheet/drafts`
2. ✅ Entrée avec status=draft → bouton "Modifier" visible
3. ✅ Entrée avec status=rejected → bouton "Modifier" visible
4. ✅ Entrée avec status=submitted → texte "Lecture seule", pas de bouton
5. ✅ Entrée avec status=approved → texte "Lecture seule", pas de bouton

### Test 5 : Route historique supprimée
1. Tenter d'accéder à `/timesheet/history`
2. ✅ Redirection vers `/` (catch-all route)
3. ✅ Vérifier que le lien n'existe plus dans la sidebar

---

## Fichiers Modifiés

- ✅ `frontend-v2/src/App.tsx` — Suppression route `/timesheet/history`
- ✅ `frontend-v2/src/pages/TimesheetEntryPage.tsx` — Saisie uniquement + alerte + billable_flag
- ✅ `frontend-v2/src/pages/TimesheetDraftPage.tsx` — Vue consolidée + soumission semaines passées
- ✅ `frontend-v2/src/components/Sidebar.tsx` — Suppression lien "Historique"

---

## Notes Techniques

### Calcul de la semaine ISO
```typescript
function toISOWeek(date: Date): string {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7))
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  const weekNo = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
  return `${d.getUTCFullYear()}-W${String(weekNo).padStart(2, '0')}`
}
```

### Détection semaines non soumises
```typescript
const { data: unsubmittedWeeks = [] } = useQuery({
  queryKey: ['unsubmitted-weeks'],
  queryFn: async () => {
    const drafts = await apiClient.get<{ work_date: string; status: string }[]>('/employee/timesheet/drafts')
    const currentWeek = toISOWeek(new Date())
    const previousWeeks = new Set<string>()
    
    drafts.forEach(entry => {
      const entryWeek = toISOWeek(new Date(entry.work_date + 'T12:00:00'))
      if (entryWeek < currentWeek && entry.status === 'draft') {
        previousWeeks.add(entryWeek)
      }
    })
    
    return Array.from(previousWeeks).sort()
  },
})
```

---

## Prochaines Étapes

Sprint 1 complété ✅

**Sprint 2 — Pages cassées P1** (1 semaine) :
- FUNC-01 : InvoicesPage — CRUD complet
- FUNC-02 : CreateProjectModal — sélecteurs réels
- FUNC-03 : Unifier FinancialReportPage
- FUNC-04 : CalendarPage — toutes les semaines

---

**Fin du rapport — Sprint 1 complété le 2026-05-04**

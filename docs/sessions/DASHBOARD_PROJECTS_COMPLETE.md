# Dashboard - Affichage des Projets Assignés

## Résumé
Ajout d'une section "Mes projets" sur le dashboard qui affiche les projets assignés à l'employé pour cette semaine et la semaine prochaine (à partir de mercredi), avec les informations du client (nom et adresse).

## Changements Backend

### 1. **Schema ProjectResponse** (`backend/app/schemas/timesheet.py`)
Ajout de deux nouveaux champs optionnels:
- `client_name: Optional[str]` - Nom du client
- `client_address: Optional[str]` - Adresse du client

### 2. **ProjectRepository** (`backend/app/repositories/project_repository.py`)
- Ajout de l'import `Client` model
- Modification de `list_active_for_employee()`:
  - Retourne maintenant `list[dict]` au lieu de `list[Project]`
  - Joint la table `clients` pour récupérer `client_name` et `client_address`
  - Retourne des dictionnaires contenant toutes les infos projet + client

### 3. **API Projects** (`backend/app/api/v1/projects.py`)
- Mise à jour pour gérer les dictionnaires retournés par le repository
- Les employés reçoivent les projets avec infos client
- Les admins/finance reçoivent les projets sans infos client (pour l'instant)

## Changements Frontend

### 1. **UnifiedDashboardPage** (`frontend-v2/src/pages/UnifiedDashboardPage.tsx`)

#### Nouveaux imports:
- `Briefcase` - Icône pour les projets
- `MapPin` - Icône pour l'adresse

#### Nouvelles interfaces:
```typescript
interface Project {
  project_id: number
  project_name: string
  client_name?: string
  client_address?: string
  start_date: string
  end_date?: string
}
```

#### Nouvelles fonctions utilitaires:
- `getNextWeekDate()` - Calcule la date de la semaine prochaine
- `isWednesdayOrLater()` - Vérifie si on est mercredi ou après

#### Nouvelles requêtes API:
- `thisWeekProjects` - Projets assignés cette semaine
- `nextWeekProjects` - Projets assignés semaine prochaine (seulement si mercredi+)

#### Nouvelle section UI:
Carte "Mes projets" avec deux sous-sections:
1. **Cette semaine** (fond gris)
   - Liste des projets assignés
   - Nom du projet
   - Nom du client
   - Adresse du client avec icône MapPin
   
2. **Semaine prochaine** (fond bleu, visible uniquement à partir de mercredi)
   - Même structure que "Cette semaine"
   - Couleur différente pour distinguer visuellement

## Logique Métier

### Affichage de la semaine prochaine
- **Condition:** Visible uniquement à partir de mercredi (jour 3)
- **Raison:** Permet aux employés de voir leurs projets à venir dès le milieu de semaine
- **Implémentation:** `isWednesdayOrLater()` vérifie `dayOfWeek >= 3`

### Filtrage des projets
- L'API `/projects?active=true&date=YYYY-MM-DD` filtre automatiquement:
  - Projets actifs uniquement
  - Projets dont l'employé est manager OU membre de l'équipe
  - Projets dont la période (start_date/end_date) inclut la date demandée

## Design UI

### Carte "Cette semaine"
- Fond: `bg-slate-50 dark:bg-slate-700/50`
- Hover: `bg-slate-100 dark:bg-slate-700`
- Icône: Indigo (`text-indigo-600`)

### Carte "Semaine prochaine"
- Fond: `bg-blue-50 dark:bg-blue-900/20`
- Hover: `bg-blue-100 dark:bg-blue-900/30`
- Icône: Bleu (`text-blue-600`)

### Responsive
- Mobile: Cartes empilées verticalement
- Desktop: Grid 2 colonnes (Mes projets | Pointages récents)

## Exemple de Données Affichées

```
Mes projets
-----------

CETTE SEMAINE
┌─────────────────────────────────┐
│ 🎯 Refonte Site Web             │
│    Société Rossi SpA            │
│    📍 Via Roma 123, Milano, IT  │
└─────────────────────────────────┘

SEMAINE PROCHAINE (à partir de mercredi)
┌─────────────────────────────────┐
│ 🎯 Migration Cloud              │
│    Tech Solutions Srl           │
│    📍 Corso Italia 45, Roma, IT │
└─────────────────────────────────┘
```

## Avantages

1. **Visibilité immédiate** - L'employé voit ses projets dès l'accueil
2. **Planification** - Anticipe les projets de la semaine suivante
3. **Contexte client** - Nom et adresse disponibles directement
4. **UX optimisée** - Distinction visuelle claire entre semaines
5. **Performance** - Requêtes parallèles avec React Query

## Tests Recommandés

1. Connexion avec un employé assigné à plusieurs projets
2. Vérifier l'affichage avant mercredi (pas de section "Semaine prochaine")
3. Vérifier l'affichage après mercredi (section "Semaine prochaine" visible)
4. Tester avec des projets sans client_address
5. Tester responsive mobile/tablette
6. Vérifier que seuls les projets de la période sont affichés

## Fichiers Modifiés

### Backend:
- `backend/app/schemas/timesheet.py`
- `backend/app/repositories/project_repository.py`
- `backend/app/api/v1/projects.py`

### Frontend:
- `frontend-v2/src/pages/UnifiedDashboardPage.tsx`

## Déploiement

```bash
docker-compose up -d --build
```

Tous les containers reconstruits et déployés avec succès.

---

**Status:** ✅ Complete
**Date:** 2026-05-05
**Build:** Successful

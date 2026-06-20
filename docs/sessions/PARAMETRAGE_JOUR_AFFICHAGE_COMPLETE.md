# Paramétrage du Jour d'Affichage - Semaine Prochaine

## Résumé
Le jour d'affichage de la section "Semaine prochaine" sur le dashboard est maintenant **paramétrable** via les paramètres d'organisation. Par défaut, il est configuré sur **Mardi (jour 2)**.

## Changements Implémentés

### 1. Backend - Base de Données

**Colonne ajoutée à `org_settings`:**
```sql
ALTER TABLE org_settings 
ADD COLUMN next_week_display_day INTEGER NOT NULL DEFAULT 2;
```

- **Type:** INTEGER
- **Valeurs:** 0 = Dimanche, 1 = Lundi, 2 = Mardi, 3 = Mercredi, etc.
- **Défaut:** 2 (Mardi)

### 2. Backend - Modèle ORM

**Fichier:** `backend/app/models/org_settings.py`

Ajout du champ:
```python
next_week_display_day: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
```

### 3. Backend - API Admin

**Fichier:** `backend/app/api/v1/admin.py`

Mise à jour des endpoints `/admin/settings`:
- **GET:** Retourne `next_week_display_day`
- **PUT:** Permet de modifier `next_week_display_day`

**Schema de requête:**
```python
class OrgSettingsRequest:
    next_week_display_day: int | None = None  # 0-6 (Dimanche-Samedi)
```

### 4. Backend - API Publique

**Fichier:** `backend/app/api/v1/auth.py`

Nouvel endpoint accessible à tous les utilisateurs authentifiés:
```python
GET /api/v1/auth/org-config
```

**Réponse:**
```json
{
  "next_week_display_day": 2
}
```

### 5. Frontend - Dashboard

**Fichier:** `frontend-v2/src/pages/UnifiedDashboardPage.tsx`

**Fonction mise à jour:**
```typescript
function isWednesdayOrLater(displayDay: number = 2): boolean {
  const today = new Date()
  const dayOfWeek = today.getDay() // 0 = Sunday, 1 = Monday, etc.
  return dayOfWeek >= displayDay
}
```

**Récupération du paramètre:**
```typescript
const { data: orgConfig } = useQuery({
  queryKey: ['org-config'],
  queryFn: () => apiClient.get<{ next_week_display_day: number }>('/auth/org-config'),
  staleTime: 60 * 60 * 1000, // Cache 1 heure
})

const nextWeekDisplayDay = orgConfig?.next_week_display_day ?? 2
const showNextWeek = isWednesdayOrLater(nextWeekDisplayDay)
```

## Configuration

### Via Interface Admin (à venir)
Les administrateurs pourront modifier ce paramètre dans la page "Paramètres Organisation".

### Via API
```bash
# Récupérer les paramètres actuels
curl -X GET http://localhost:8000/api/v1/admin/settings \
  -H "Authorization: Bearer <admin_token>"

# Modifier le jour d'affichage (exemple: Lundi = 1)
curl -X PUT http://localhost:8000/api/v1/admin/settings \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"next_week_display_day": 1}'
```

### Via SQL Direct
```sql
UPDATE org_settings 
SET next_week_display_day = 1  -- Lundi
WHERE org_id = 1;
```

## Valeurs Possibles

| Valeur | Jour | Description |
|--------|------|-------------|
| 0 | Dimanche | Affiche dès dimanche |
| 1 | Lundi | Affiche dès lundi |
| 2 | Mardi | Affiche dès mardi (défaut) |
| 3 | Mercredi | Affiche dès mercredi |
| 4 | Jeudi | Affiche dès jeudi |
| 5 | Vendredi | Affiche dès vendredi |
| 6 | Samedi | Affiche dès samedi |

## Test - Projets Assignés à Achille Romano

**Script exécuté:** `backend/assign_projects_achille.py`

**Résultat:**
```
✅ Achille Romano trouvé: ID 31

📅 Cette semaine: 2026-05-04 → 2026-05-08
📅 Semaine prochaine: 2026-05-11 → 2026-05-15

✅ 10 projets disponibles
  ✅ Projet #1 'Ottimizzazione BI' assigné pour CETTE SEMAINE
  ✅ Projet #2 'Supporto Analytics' assigné pour CETTE SEMAINE
  ✅ Projet #3 'Formazione Desktop' assigné pour SEMAINE PROCHAINE
  ✅ Projet #4 'Monitoraggio DevOps' assigné pour SEMAINE PROCHAINE
  ✅ Projet #5 'API Database' assigné pour SEMAINE PROCHAINE

👤 Employé: Achille Romano (achille.romano@emp15.test.it)
📊 Cette semaine: 2 projets
📊 Semaine prochaine: 3 projets
```

## Comportement

### Avant Mardi (jour 0-1)
- Dashboard affiche uniquement "Cette semaine"
- Section "Semaine prochaine" masquée

### À partir de Mardi (jour 2+)
- Dashboard affiche "Cette semaine" ET "Semaine prochaine"
- Les employés peuvent anticiper leurs projets à venir

## Avantages

1. **Flexibilité:** Chaque organisation peut choisir son jour
2. **Anticipation:** Les employés voient leurs projets futurs à l'avance
3. **Paramétrable:** Modifiable sans redéploiement
4. **Cache:** Paramètre mis en cache 1h côté frontend pour performance

## Fichiers Modifiés

### Backend:
- `backend/app/models/org_settings.py`
- `backend/app/api/v1/admin.py`
- `backend/app/api/v1/auth.py`
- `backend/assign_projects_achille.py` (script utilitaire)

### Frontend:
- `frontend-v2/src/pages/UnifiedDashboardPage.tsx`

### Base de données:
- Colonne `next_week_display_day` ajoutée à `org_settings`

## Déploiement

```bash
# 1. Appliquer la modification SQL
docker exec timelyna-db psql -U timelyna -d timelyna \
  -c "ALTER TABLE org_settings ADD COLUMN IF NOT EXISTS next_week_display_day INTEGER NOT NULL DEFAULT 2;"

# 2. Rebuild les containers
docker-compose up -d --build backend frontend

# 3. (Optionnel) Assigner des projets de test
docker exec timelyna-backend python assign_projects_achille.py
```

## Test Utilisateur

1. Connectez-vous avec `achille.romano@emp15.test.it` / `password123`
2. Accédez au dashboard
3. Vérifiez la section "Mes projets":
   - **Cette semaine:** 2 projets (Ottimizzazione BI, Supporto Analytics)
   - **Semaine prochaine:** 3 projets (Formazione Desktop, Monitoraggio DevOps, API Database)
4. Chaque projet affiche:
   - Nom du projet
   - Nom du client
   - Adresse du client

---

**Status:** ✅ Complete
**Date:** 2026-05-05
**Configuration:** Mardi (jour 2) par défaut

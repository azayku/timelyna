# Implémentation des compétences pour les managers

## Problème actuel
Le backend a été modifié pour inclure les compétences des employés dans l'API `/api/v1/manager/team`, mais Docker ne reconstruit pas correctement l'image avec les nouvelles modifications.

## Modifications effectuées

### Backend (`backend/app/api/v1/manager.py`)

1. **Imports ajoutés**:
```python
from app.models.employee_skill import EmployeeSkill
from app.models.skill_rate import SkillRate
```

2. **TeamMemberResponse modifié**:
```python
class TeamMemberResponse(BaseModel):
    employee_id: int
    first_name: str
    last_name: str
    email: str
    hire_date: str | None
    organization_name: str
    skills: list[str]  # Liste des noms de compétences

    class Config:
        from_attributes = True
```

3. **Endpoint `/manager/team` modifié** pour récupérer les compétences:
```python
# Get employee skills
skills_stmt = (
    select(SkillRate.skill_name)
    .join(EmployeeSkill, EmployeeSkill.skill_rate_id == SkillRate.id)
    .where(EmployeeSkill.employee_id == employee.employee_id)
    .order_by(SkillRate.skill_name)
)
skills_result = await db.execute(skills_stmt)
skills = [row[0] for row in skills_result.all()]

response.append(
    TeamMemberResponse(
        employee_id=employee.employee_id,
        first_name=employee.first_name or "",
        last_name=employee.last_name or "",
        email=employee.email,
        hire_date=employee.hire_date.isoformat() if employee.hire_date else None,
        organization_name=org_name,
        skills=skills,
    )
)
```

## Instructions pour reconstruire le backend

### Option 1: Rebuild complet (RECOMMANDÉ)
```bash
cd d:\Projets\Perso\timelyna

# Arrêter et supprimer le container
docker-compose stop backend
docker-compose rm -f backend

# Supprimer l'image
docker rmi -f timelyna-backend

# Rebuild sans cache
docker-compose build --no-cache backend

# Redémarrer
docker-compose up -d backend

# Attendre 10 secondes
Start-Sleep -Seconds 10
```

### Option 2: Utiliser docker-compose down/up
```bash
cd d:\Projets\Perso\timelyna

# Arrêter tous les services
docker-compose down

# Rebuild backend
docker-compose build --no-cache backend

# Redémarrer tous les services
docker-compose up -d
```

## Vérification

### 1. Vérifier que le code est bien dans le container
```powershell
docker exec timelyna-backend grep -A 8 "class TeamMemberResponse" /app/app/api/v1/manager.py
```

**Résultat attendu**: Doit contenir `skills: list[str]`

### 2. Tester l'API
```powershell
$body = @{identifier='gianni.cappelli@manager.test.it'; password='password123'} | ConvertTo-Json
$response = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/auth/login' -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing
$token = ($response.Content | ConvertFrom-Json).access_token
$headers = @{Authorization="Bearer $token"}
$team = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/manager/team' -Headers $headers -UseBasicParsing
$team.Content | ConvertFrom-Json | Select-Object -First 1 | ConvertTo-Json
```

**Résultat attendu**: Chaque employé doit avoir un champ `skills` (tableau de strings)

## Frontend à modifier ensuite

Une fois le backend fonctionnel, il faudra modifier `frontend-v2/src/pages/ManagerTeamPage.tsx`:

1. **Ajouter le champ skills à l'interface**:
```typescript
interface TeamMember {
  employee_id: number
  first_name: string
  last_name: string
  email: string
  hire_date: string | null
  organization_name: string
  skills: string[]  // NOUVEAU
}
```

2. **Afficher les compétences dans le tableau**:
- Ajouter une colonne "Compétences" dans le tableau desktop
- Afficher les compétences sous forme de badges
- Ajouter les compétences dans les cartes mobiles

3. **Ajouter la possibilité de modifier les compétences**:
- Bouton "Modifier" pour chaque employé
- Modal avec liste des compétences disponibles
- Possibilité d'ajouter/retirer des compétences

## Endpoints à créer pour la modification

```python
# GET /api/v1/manager/available-skills
# Retourne toutes les compétences disponibles pour l'organisation

# POST /api/v1/manager/employee/{employee_id}/skills
# Body: {"skill_ids": [1, 2, 3]}
# Remplace les compétences de l'employé

# DELETE /api/v1/manager/employee/{employee_id}/skills/{skill_id}
# Retire une compétence spécifique
```

## Problème Docker connu

Le problème récurrent est que Docker ne prend pas toujours les modifications lors du build, même avec `--no-cache`. Cela peut être dû à:

1. **Cache de build Docker** qui persiste
2. **Volumes montés** qui écrasent le code
3. **Timing** entre le build et le copy des fichiers

**Solution**: Toujours faire un rebuild complet en supprimant l'image avant de rebuild.

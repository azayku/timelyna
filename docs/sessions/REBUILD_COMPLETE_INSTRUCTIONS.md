# Instructions complètes pour reconstruire Backend + Frontend

## Problèmes actuels
1. ❌ Page "Mes organisations" - toujours en cartes au lieu de tableau
2. ❌ Stats du dashboard - ne sont pas calculées  
3. ❌ Skills de l'équipe - ne s'affichent pas

## Cause
Les modifications du code ne sont pas dans les containers Docker car ils n'ont pas été reconstruits.

## Solution: Rebuild complet

### Étape 1: Arrêter tous les containers
```powershell
cd d:\Projets\Perso\timelyna
docker-compose down
```

### Étape 2: Supprimer les images
```powershell
docker rmi -f timelyna-backend
docker rmi -f timelyna-frontend
```

### Étape 3: Rebuild TOUT sans cache
```powershell
docker-compose build --no-cache
```
⏱️ Cela prendra 5-10 minutes

### Étape 4: Redémarrer tous les services
```powershell
docker-compose up -d
```

### Étape 5: Attendre que tout démarre
```powershell
Start-Sleep -Seconds 15
```

### Étape 6: Vérifier que tout fonctionne
```powershell
# Vérifier le backend
curl http://localhost:8000/health -UseBasicParsing

# Vérifier le frontend
curl http://localhost -UseBasicParsing
```

## Vérification des modifications

### 1. Backend - API Manager Organizations
```powershell
$body = @{identifier='gianni.cappelli@manager.test.it'; password='password123'} | ConvertTo-Json
$response = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/auth/login' -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing
$token = ($response.Content | ConvertFrom-Json).access_token
$headers = @{Authorization="Bearer $token"}

# Test organizations
$orgs = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/manager/organizations' -Headers $headers -UseBasicParsing
$orgs.Content | ConvertFrom-Json | Select-Object -First 1
```

**Résultat attendu**: Doit contenir `manager_name` et `created_at`

### 2. Backend - API Manager Team
```powershell
# Test team (avec les mêmes headers)
$team = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/manager/team' -Headers $headers -UseBasicParsing
$team.Content | ConvertFrom-Json | Select-Object -First 1
```

**Résultat attendu**: Doit contenir `skills` (tableau)

### 3. Frontend - Page Organisations
1. Ouvrir http://localhost
2. Login: `gianni.cappelli@manager.test.it` / `password123`
3. Menu GESTION → Mes organisations
4. **Résultat attendu**: Tableau avec colonnes (Organisation, Manager, Employés, Date de création, Actions)

### 4. Frontend - Page Équipe
1. Menu GESTION → Mon équipe
2. **Résultat attendu**: Tableau avec colonne Compétences (à implémenter après rebuild)

## Si ça ne marche toujours pas

### Option A: Rebuild un par un

#### Backend seulement
```powershell
docker-compose stop backend
docker-compose rm -f backend
docker rmi -f timelyna-backend
docker-compose build --no-cache backend
docker-compose up -d backend
Start-Sleep -Seconds 10
```

#### Frontend seulement
```powershell
docker-compose stop frontend
docker-compose rm -f frontend
docker rmi -f timelyna-frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
Start-Sleep -Seconds 5
```

### Option B: Vérifier les fichiers dans les containers

#### Vérifier backend
```powershell
# Vérifier que le code est à jour
docker exec timelyna-backend grep -A 3 "manager_name" /app/app/api/v1/manager.py
docker exec timelyna-backend grep -A 3 "skills:" /app/app/api/v1/manager.py
```

#### Vérifier frontend
```powershell
# Vérifier que le tableau est présent
docker exec timelyna-frontend grep -A 5 "Desktop Table" /usr/share/nginx/html/assets/*.js
```

## Modifications effectuées (pour référence)

### Backend (`backend/app/api/v1/manager.py`)

1. **OrganizationResponse** - Ajout de `manager_name` et `created_at`
2. **TeamMemberResponse** - Ajout de `skills: list[str]`
3. **get_manager_organizations()** - Récupère le nom du manager
4. **get_manager_team()** - Récupère les compétences de chaque employé

### Frontend (`frontend-v2/src/pages/ManagerOrganizationsPage.tsx`)

1. **Interface Organization** - Ajout de `manager_name` et `created_at`
2. **Tableau desktop** - 5 colonnes au lieu de 3
3. **Cartes mobile** - Affichage du manager et de la date
4. **Import** - Ajout de `User` depuis lucide-react

### Frontend (`frontend-v2/src/pages/ManagerTeamPage.tsx`)

À modifier après rebuild pour afficher les compétences.

## Temps estimé
- Rebuild complet: **5-10 minutes**
- Vérification: **2-3 minutes**
- **Total: 10-15 minutes**

## Notes importantes

1. **Toujours faire `docker-compose down` avant de rebuild** pour éviter les conflits
2. **Toujours utiliser `--no-cache`** pour forcer la reconstruction
3. **Attendre 10-15 secondes** après `docker-compose up -d` avant de tester
4. Si le problème persiste, **vérifier les logs**: `docker logs timelyna-backend --tail 50`

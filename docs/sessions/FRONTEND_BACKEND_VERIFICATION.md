# Vérification Frontend & Backend - Manager API

## Résumé des modifications

### ✅ Backend modifié
**Fichier**: `backend/app/api/v1/manager.py`

**Modifications**:
1. Ajout de logs de debug dans `get_manager_organizations()`:
   - Log de l'utilisateur courant
   - Log du nombre d'organisations trouvées
   - Log des détails de chaque organisation
   - Log du nombre d'employés

2. Ajout de logs de debug dans `get_manager_team()`:
   - Log de l'utilisateur courant
   - Log des IDs d'organisations trouvées
   - Log du nombre de membres

**Code vérifié**: ✅ Pas d'erreurs de syntaxe ou d'imports

### ✅ Frontend vérifié
**Fichiers vérifiés**:
- `frontend-v2/src/pages/ManagerOrganizationsPage.tsx` ✅
- `frontend-v2/src/pages/ManagerTeamPage.tsx` ✅
- `frontend-v2/src/components/Sidebar.tsx` ✅
- `frontend-v2/src/lib/apiClient.ts` ✅
- `frontend-v2/src/App.tsx` ✅

**Structure de données attendue**:
```typescript
// Organizations
interface Organization {
  organization_id: number
  organization_name: string
  employee_count: number
}

// Team members
interface TeamMember {
  employee_id: number
  first_name: string
  last_name: string
  email: string
  hire_date: string | null
  organization_name: string
}
```

**Routes configurées**:
- `/manager/organizations` → `ManagerOrganizationsPage`
- `/manager/team` → `ManagerTeamPage`

**Navigation**:
- Section "GESTION" dans le Sidebar (visible pour managers et admins)
- Liens vers les deux pages

### ✅ Scripts de test créés

1. **`backend/check_backend_status.py`**
   - Vérifie que le backend est en ligne
   - Teste le endpoint `/health`
   - Teste l'accessibilité de l'API

2. **`backend/test_manager_data.py`**
   - Test direct de la base de données
   - Vérifie les données de Gianni
   - Liste les organisations et employés

3. **`backend/test_manager_api.py`**
   - Test complet de l'API avec authentification
   - Appelle `/manager/organizations`
   - Appelle `/manager/team`

## Diagnostic du problème

### Causes possibles identifiées

1. **Backend non redémarré** ⚠️ CRITIQUE
   - Les modifications du code ne sont pas prises en compte
   - Solution: Redémarrer le serveur backend

2. **Données manquantes dans la DB**
   - Les organisations n'existent pas
   - Le `manager_id` ne correspond pas à l'`employee_id` de Gianni
   - Solution: Exécuter `backend/setup_gianni_final.sql`

3. **Problème d'authentification**
   - Le token JWT n'est pas valide
   - Le rôle n'est pas "manager" ou "admin"
   - Solution: Vérifier le login et le rôle

4. **Problème de mapping des colonnes**
   - ✅ CORRIGÉ: Le backend utilise maintenant `org_id` et `org_name`
   - ✅ CORRIGÉ: Le mapping vers `organization_id` et `organization_name` est fait

## Procédure de test complète

### Étape 1: Vérifier le backend
```bash
cd backend
python check_backend_status.py
```

**Si le backend n'est pas démarré:**
```bash
# Option 1: Docker
docker-compose up -d backend

# Option 2: Direct
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Étape 2: Tester la base de données
```bash
cd backend
python test_manager_data.py
```

**Résultat attendu:**
```
✅ Gianni trouvé: employee_id=8
✅ Nombre d'organisations trouvées: 3
   - Tech Solutions Italia (4 employés)
   - Digital Marketing Pro (4 employés)
   - Consulting & Advisory (4 employés)
```

**Si échec:** Exécuter le SQL
```bash
# Avec psql
psql -U postgres -d timesheetpro -f setup_gianni_final.sql

# Ou copier-coller dans votre client SQL
```

### Étape 3: Tester l'API
```bash
cd backend
python test_manager_api.py
```

**Résultat attendu:**
```
✅ Login réussi
✅ Nombre d'organisations: 3
   - Tech Solutions Italia (id=X, employees=4)
   - Digital Marketing Pro (id=Y, employees=4)
   - Consulting & Advisory (id=Z, employees=4)
✅ Nombre de membres: 12
```

### Étape 4: Vérifier les logs backend

Dans la console du serveur backend, vous devriez voir:
```
INFO:app.manager:[MANAGER] Getting organizations for user_id=8, email=gianni.cappelli@manager.test.it
INFO:app.manager:[MANAGER] Found 3 organizations
INFO:app.manager:[MANAGER] Processing org_id=1, org_name=Tech Solutions Italia
INFO:app.manager:[MANAGER] org_id=1 has 4 active employees
...
INFO:app.manager:[MANAGER] Returning 3 organizations
```

### Étape 5: Tester le frontend

1. Ouvrir: `http://localhost:5173`
2. Login:
   - Email: `gianni.cappelli@manager.test.it`
   - Mot de passe: `password123`
3. Vérifier le menu "GESTION" (visible uniquement pour managers/admins)
4. Cliquer sur "Mes organisations" → Devrait afficher 3 organisations
5. Cliquer sur "Mon équipe" → Devrait afficher 12 employés

### Étape 6: Debug frontend (si nécessaire)

Ouvrir la console développeur (F12):

1. **Onglet Network**:
   - Filtrer par "manager"
   - Vérifier les requêtes à `/api/v1/manager/organizations` et `/api/v1/manager/team`
   - Status code devrait être 200
   - Response devrait contenir les données

2. **Onglet Console**:
   - Vérifier qu'il n'y a pas d'erreurs JavaScript
   - Vérifier les erreurs de React Query

## Checklist de vérification

### Backend
- [ ] Serveur backend démarré sur le port 8000
- [ ] Endpoint `/health` répond avec `{"status": "ok"}`
- [ ] Logs de debug visibles dans la console
- [ ] Pas d'erreurs dans les logs

### Base de données
- [ ] Gianni Cappelli existe dans la table `employees`
- [ ] 3 organisations existent dans la table `organizations`
- [ ] Les organisations ont `manager_id` = employee_id de Gianni
- [ ] 12 employés ont leur `org_id` correspondant aux organisations

### API
- [ ] Login avec Gianni réussit
- [ ] `/api/v1/manager/organizations` retourne 3 organisations
- [ ] `/api/v1/manager/team` retourne 12 employés
- [ ] Les données sont correctement formatées (organization_id, organization_name)

### Frontend
- [ ] Frontend démarré sur le port 5173
- [ ] Login avec Gianni réussit
- [ ] Menu "GESTION" visible dans le Sidebar
- [ ] Page "Mes organisations" affiche 3 organisations
- [ ] Page "Mon équipe" affiche 12 employés
- [ ] Pagination fonctionne
- [ ] Pas d'erreurs dans la console

## Informations de connexion

### Gianni Cappelli (Manager)
- Email: `gianni.cappelli@manager.test.it`
- Mot de passe: `password123`
- Rôle: `manager`

### Autres utilisateurs de test
- Admin: `niccolo.randazzo@admin.test.it` / `password123`
- Employee: `*.test.it` / `password123`

## Structure de la base de données

### Table `organizations`
```sql
org_id          INTEGER PRIMARY KEY
org_name        VARCHAR(255)
manager_id      INTEGER (FK → employees.employee_id)
deleted_at      TIMESTAMP
```

### Table `employees`
```sql
employee_id         INTEGER PRIMARY KEY
email               VARCHAR(255)
first_name          VARCHAR(100)
last_name           VARCHAR(100)
role                VARCHAR(50)
org_id              INTEGER (FK → organizations.org_id)
employment_status   VARCHAR(50)
deleted_at          TIMESTAMP
```

## Prochaines étapes

Une fois que tout fonctionne:

1. **Retirer les logs de debug** (optionnel):
   - Soit les supprimer
   - Soit les mettre en niveau DEBUG au lieu de INFO

2. **Tester d'autres scénarios**:
   - Manager avec 0 organisation
   - Manager avec 1 seule organisation
   - Organisation sans employés
   - Filtres et recherche dans la page équipe

3. **Optimisations possibles**:
   - Ajouter un cache pour les organisations
   - Pagination côté backend si beaucoup d'organisations
   - Ajouter des filtres supplémentaires

## Support

Si le problème persiste après avoir suivi toutes ces étapes:

1. Vérifier les logs backend en détail
2. Vérifier la console frontend (F12)
3. Tester avec curl ou Postman
4. Vérifier la configuration de la base de données
5. Vérifier les variables d'environnement (.env)

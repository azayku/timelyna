# Debug Manager API - Instructions

## Problème
L'API `/api/v1/manager/organizations` et `/api/v1/manager/team` retournent des tableaux vides pour Gianni Cappelli, alors que les données existent dans la base de données.

## Modifications apportées

### Backend (`backend/app/api/v1/manager.py`)
✅ Ajout de logs de debug détaillés dans les deux endpoints:
- Log de l'utilisateur courant (employee_id, email)
- Log du nombre d'organisations trouvées
- Log des détails de chaque organisation
- Log du nombre d'employés par organisation

### Scripts de test créés

1. **`backend/test_manager_data.py`** - Test direct de la base de données
   - Vérifie l'existence de Gianni
   - Liste toutes les organisations où il est manager
   - Compte les employés dans chaque organisation

2. **`backend/test_manager_api.py`** - Test de l'API avec authentification
   - Login avec Gianni
   - Appel à `/manager/organizations`
   - Appel à `/manager/team`

## Instructions de test

### Étape 1: Redémarrer le backend
**CRITIQUE**: Les modifications du code ne seront pas prises en compte tant que le serveur n'est pas redémarré!

```bash
cd backend

# Si vous utilisez Docker
docker-compose restart backend

# Si vous lancez directement avec uvicorn
# Arrêter le serveur (Ctrl+C) puis relancer:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Étape 2: Tester la base de données directement

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

### Étape 3: Tester l'API

```bash
cd backend
python test_manager_api.py
```

**Résultat attendu:**
```
✅ Login réussi
✅ Nombre d'organisations: 3
✅ Nombre de membres: 12
```

### Étape 4: Vérifier les logs du backend

Après avoir testé l'API, vérifier les logs du serveur backend. Vous devriez voir:

```
INFO:app.manager:[MANAGER] Getting organizations for user_id=8, email=gianni.cappelli@manager.test.it
INFO:app.manager:[MANAGER] Found 3 organizations
INFO:app.manager:[MANAGER] Processing org_id=X, org_name=Tech Solutions Italia
INFO:app.manager:[MANAGER] org_id=X has 4 active employees
...
INFO:app.manager:[MANAGER] Returning 3 organizations
```

### Étape 5: Tester depuis le frontend

1. Ouvrir le navigateur: `http://localhost:5173`
2. Se connecter avec:
   - Email: `gianni.cappelli@manager.test.it`
   - Mot de passe: `password123`
3. Aller dans le menu "GESTION" → "Mes organisations"
4. Aller dans le menu "GESTION" → "Mon équipe"

## Diagnostic des problèmes

### Si test_manager_data.py échoue
❌ **Problème**: Les données n'existent pas dans la base
📝 **Solution**: Exécuter le script SQL `backend/setup_gianni_final.sql`

### Si test_manager_api.py échoue avec 401
❌ **Problème**: Authentification échouée
📝 **Solution**: Vérifier que le mot de passe de Gianni est bien `password123`

### Si test_manager_api.py retourne []
❌ **Problème**: Le backend ne trouve pas les organisations
📝 **Solution**: 
1. Vérifier que le backend a bien été redémarré
2. Vérifier les logs du backend pour voir les requêtes SQL
3. Vérifier que `manager_id` dans la table `organizations` correspond à `employee_id` de Gianni

### Si le frontend affiche "Aucune organisation"
❌ **Problème**: Problème de communication frontend-backend
📝 **Solution**:
1. Ouvrir la console développeur (F12)
2. Aller dans l'onglet "Network"
3. Vérifier la requête à `/api/v1/manager/organizations`
4. Vérifier le status code et la réponse

## Données de test

### Utilisateur manager
- Email: `gianni.cappelli@manager.test.it`
- Mot de passe: `password123`
- Role: `manager`
- Employee ID: 8 (peut varier selon votre base)

### Organisations créées
1. **Tech Solutions Italia** - 4 employés
2. **Digital Marketing Pro** - 4 employés
3. **Consulting & Advisory** - 4 employés

### Colonnes de la base de données
- Table `organizations`: `org_id`, `org_name`, `manager_id`
- Table `employees`: `employee_id`, `org_id`, `employment_status`, `deleted_at`

## Structure de l'API

### GET /api/v1/manager/organizations
**Response:**
```json
[
  {
    "organization_id": 1,
    "organization_name": "Tech Solutions Italia",
    "employee_count": 4
  }
]
```

### GET /api/v1/manager/team
**Response:**
```json
[
  {
    "employee_id": 1,
    "first_name": "Marco",
    "last_name": "Rossi",
    "email": "marco.rossi@test.it",
    "hire_date": "2024-01-15",
    "organization_name": "Tech Solutions Italia"
  }
]
```

## Prochaines étapes

Une fois que les tests fonctionnent:
1. ✅ Les logs de debug peuvent être retirés ou mis en niveau DEBUG
2. ✅ Le frontend devrait afficher correctement les organisations et l'équipe
3. ✅ La pagination devrait fonctionner (10 orgs par page, 15 membres par page)

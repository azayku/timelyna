# 🚀 Démarrage de TimesheetPro

## ✅ Vérifications Préalables

### Backend
- ✅ Module `manager.py` importé avec succès
- ✅ Application FastAPI chargée : **125 routes** enregistrées
- ✅ Tous les routers configurés correctement

### Frontend
- ✅ Traductions complètes (FR, EN, IT, ES)
- ✅ Composants mis à jour avec pagination
- ✅ Nouveaux endpoints intégrés

## 📋 Instructions de Démarrage

### 1️⃣ Démarrer le Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Vérification :**
- Backend accessible sur : http://localhost:8000
- Documentation API : http://localhost:8000/docs
- Health check : http://localhost:8000/health

### 2️⃣ Démarrer le Frontend

```bash
cd frontend-v2
npm run dev
```

**Vérification :**
- Frontend accessible sur : http://localhost:5173
- Hot reload activé

### 3️⃣ Démarrer avec Docker Compose (Optionnel)

```bash
docker-compose up -d
```

## 🧪 Tests des Nouvelles Fonctionnalités

### 1. Page de Connexion
- [ ] Vérifier que le bouton Google n'apparaît plus
- [ ] Tester la connexion avec email/mot de passe
- [ ] Tester le sélecteur de langue (FR, EN, IT, ES)

### 2. Dashboard - Pagination des Projets
- [ ] Se connecter en tant qu'employé
- [ ] Vérifier la section "Mes projets"
- [ ] Tester la pagination "Cette semaine" (5 projets/page)
- [ ] Tester la pagination "Semaine prochaine" (5 projets/page)
- [ ] Vérifier les boutons précédent/suivant
- [ ] Vérifier l'indicateur de page (Page X / Y)

### 3. Dashboard Manager - Organisations
- [ ] Se connecter en tant que manager
- [ ] Vérifier la section "Mes organisations"
- [ ] Vérifier l'affichage du nombre d'employés
- [ ] Cliquer sur "Voir tout" pour accéder aux organisations

### 4. Dashboard Manager - Équipe
- [ ] Vérifier la section "Mon équipe"
- [ ] Vérifier l'affichage : Nom, Prénom, Organisation, Date d'entrée
- [ ] Tester la pagination (5 membres/page)
- [ ] Vérifier les boutons précédent/suivant

### 5. API Manager - Nouveaux Endpoints

#### Test GET /api/v1/manager/organizations
```bash
curl -X GET "http://localhost:8000/api/v1/manager/organizations" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Réponse attendue :**
```json
[
  {
    "organization_id": 1,
    "organization_name": "Organisation A",
    "employee_count": 15
  }
]
```

#### Test GET /api/v1/manager/team
```bash
curl -X GET "http://localhost:8000/api/v1/manager/team" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Réponse attendue :**
```json
[
  {
    "employee_id": 1,
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean.dupont@example.com",
    "hire_date": "2024-01-15",
    "organization_name": "Organisation A"
  }
]
```

## 🔍 Vérification des Traductions

### Tester les 4 Langues

1. **Français (FR)**
   - Connexion → "Connexion"
   - Dashboard → "Mes projets", "Mon équipe"

2. **Anglais (EN)**
   - Login → "Sign in"
   - Dashboard → "My projects", "My team"

3. **Italien (IT)**
   - Login → "Accedi"
   - Dashboard → "I miei progetti", "Il mio team"

4. **Espagnol (ES)** 🆕
   - Login → "Iniciar sesión"
   - Dashboard → "Mis proyectos", "Mi equipo"

## 📊 Données de Test

### Créer un Manager avec Organisations

```sql
-- Créer une organisation avec un manager
INSERT INTO organizations (organization_name, manager_id) 
VALUES ('Test Org', 1);

-- Assigner des employés à l'organisation
UPDATE employees 
SET org_id = 1 
WHERE employee_id IN (2, 3, 4, 5, 6);
```

### Créer des Projets pour Tester la Pagination

```sql
-- Créer 10 projets pour tester la pagination
INSERT INTO projects (project_name, client_id, start_date, end_date, status)
VALUES 
  ('Projet 1', 1, '2024-01-01', '2024-12-31', 'active'),
  ('Projet 2', 1, '2024-01-01', '2024-12-31', 'active'),
  -- ... (8 autres projets)
```

## 🐛 Dépannage

### Erreur : "Cannot import name 'Employee'"
✅ **Résolu** - Import corrigé de `app.models.auth` vers `app.models.employee`

### Erreur : "Manager router not found"
✅ **Résolu** - Router ajouté dans `app/main.py`

### Pagination ne fonctionne pas
- Vérifier que vous avez plus de 5 projets/membres
- Vérifier la console du navigateur pour les erreurs
- Vérifier que les endpoints API retournent des données

### Traductions manquantes
- Vérifier que `fr-complete.json` a été copié vers `fr.json`
- Vérifier que `es.json` existe
- Vérifier que `i18n.ts` importe toutes les langues

## 📝 Logs à Surveiller

### Backend
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Frontend
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

## ✅ Checklist de Démarrage

- [ ] Backend démarré sur port 8000
- [ ] Frontend démarré sur port 5173
- [ ] Base de données accessible
- [ ] Connexion réussie avec un compte test
- [ ] Dashboard s'affiche correctement
- [ ] Pagination des projets fonctionne
- [ ] Sections manager visibles (si rôle manager)
- [ ] Traductions fonctionnent dans les 4 langues

## 🎯 Prochaines Étapes

1. Tester toutes les fonctionnalités en tant qu'employé
2. Tester toutes les fonctionnalités en tant que manager
3. Vérifier les traductions dans chaque langue
4. Tester la pagination avec différents volumes de données
5. Vérifier les performances avec beaucoup de projets/membres

## 📞 Support

En cas de problème :
1. Vérifier les logs backend et frontend
2. Vérifier la console du navigateur (F12)
3. Vérifier que la base de données contient des données de test
4. Consulter `DASHBOARD_MANAGER_IMPROVEMENTS.md` pour les détails techniques

---

**Status : ✅ PRÊT À DÉMARRER**

Toutes les vérifications préalables sont passées avec succès !

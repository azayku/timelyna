# Import CSV — Documentation Backend

## 📦 Fichiers créés

### Service
- **`backend/app/services/import_service.py`**
  - `parse_csv()`: Parse le contenu CSV et valide les colonnes requises
  - `ImportService.import_employees_csv()`: Import d'employés depuis CSV
  - `ImportService.import_projects_csv()`: Import de projets depuis CSV

### Router
- **`backend/app/api/v1/imports.py`**
  - Routes d'import protégées par le rôle `admin`
  - 4 endpoints disponibles

### Tests
- **`backend/tests/unit/test_import_service.py`**
  - 5 tests unitaires pour la fonction `parse_csv()`
  - Tous les tests passent ✅

## 🔌 Endpoints

### 1. Import d'employés
```http
POST /api/v1/admin/import/employees
Authorization: Bearer <token_admin>
Content-Type: multipart/form-data

file: <fichier.csv>
```

**Colonnes CSV requises:**
- `email` (obligatoire)
- `first_name` (obligatoire)
- `last_name` (obligatoire)

**Colonnes optionnelles:**
- `role` (valeurs: `employee`, `manager`, `admin`, `finance` — défaut: `employee`)
- `phone`
- `department`
- `hire_date` (format: `YYYY-MM-DD`)

**Réponse:**
```json
{
  "success": 10,
  "skipped": 2,
  "errors": ["Ligne 5: email invalide 'bad-email'"],
  "message": "10 employé(s) créé(s), 2 ignoré(s)"
}
```

**Comportement:**
- Les employés existants (même email) sont **ignorés** (pas d'erreur)
- Un **username** unique est généré automatiquement (`email@domain.com` → `email`)
- Un **mot de passe temporaire** est généré et hashé (bcrypt)
- Le champ `must_change_password` est défini à `true`
- Les employés sont créés avec `employment_status = 'active'`

---

### 2. Import de projets
```http
POST /api/v1/admin/import/projects
Authorization: Bearer <token_admin>
Content-Type: multipart/form-data

file: <fichier.csv>
```

**Colonnes CSV requises:**
- `project_name` (obligatoire)
- `project_code` (obligatoire, unique)
- `client_name` **OU** `client_id` (l'un des deux obligatoire)

**Colonnes optionnelles:**
- `description`
- `start_date` (format: `YYYY-MM-DD` — défaut: aujourd'hui)
- `end_date` (format: `YYYY-MM-DD`)
- `budget_hours` (nombre décimal)
- `manager_email` (email d'un employé existant — défaut: premier admin de l'org)
- `billing_rate` (taux de facturation — défaut: 0.0)

**Réponse:**
```json
{
  "success": 5,
  "skipped": 1,
  "errors": ["Ligne 3: client 'Unknown Corp' introuvable"],
  "message": "5 projet(s) créé(s), 1 ignoré(s)"
}
```

**Comportement:**
- Les projets existants (même `project_code`) sont **ignorés**
- Le client est résolu soit par `client_id`, soit par `client_name`
- Le manager est résolu par `manager_email` (si fourni)
- Cache interne pour optimiser les requêtes répétées (clients, managers)
- Les projets sont créés avec `status = 'active'`

---

### 3. Template CSV employés
```http
GET /api/v1/admin/import/employees/template
Authorization: Bearer <token_admin>
```

**Réponse:** Fichier CSV `template_employees.csv`
```csv
email,first_name,last_name,role,phone,department,hire_date
john.doe@example.com,John,Doe,employee,+33612345678,IT,2026-01-15
jane.smith@example.com,Jane,Smith,manager,+33698765432,Finance,2025-12-01
```

---

### 4. Template CSV projets
```http
GET /api/v1/admin/import/projects/template
Authorization: Bearer <token_admin>
```

**Réponse:** Fichier CSV `template_projects.csv`
```csv
project_name,project_code,client_name,description,start_date,end_date,budget_hours,manager_email,billing_rate
Projet Alpha,ALPHA-2026,Acme Corp,Développement application mobile,2026-01-01,2026-12-31,1600,manager@example.com,85.00
Projet Beta,BETA-2026,Beta Inc,Refonte site web,2026-02-01,,800,manager@example.com,90.00
```

---

## ⚙️ Configuration

### Limites
- **Taille max:** 5 MB par fichier
- **Format:** `.csv` uniquement
- **Encodage:** UTF-8 (avec ou sans BOM) ou Latin-1

### Sécurité
- **Auth:** JWT Bearer obligatoire
- **Role:** `admin` ou `superadmin` requis
- **Multi-tenant:** Les données sont créées dans l'organisation de l'utilisateur (`org_id`)

---

## 🧪 Tests

### Lancer les tests unitaires
```bash
cd backend
pytest tests/unit/test_import_service.py -v
```

**Résultat:**
```
tests/unit/test_import_service.py::test_parse_csv_valid PASSED
tests/unit/test_import_service.py::test_parse_csv_missing_columns PASSED
tests/unit/test_import_service.py::test_parse_csv_utf8_bom PASSED
tests/unit/test_import_service.py::test_parse_csv_empty PASSED
tests/unit/test_import_service.py::test_parse_csv_strips_whitespace PASSED

======================== 5 passed ========================
```

---

## 📝 Exemple d'utilisation (curl)

### Import d'employés
```bash
curl -X POST http://localhost:8000/api/v1/admin/import/employees \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "file=@employees.csv"
```

### Télécharger template
```bash
curl http://localhost:8000/api/v1/admin/import/employees/template \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -o template_employees.csv
```

---

## 🔍 Logs

Les employés créés avec des mots de passe temporaires sont loggés (niveau INFO):
```
Employee créé: john.doe@example.com (username: john.doe, password: Xy8z...)
```

⚠️ **Important:** Ces logs contiennent des mots de passe en clair (temporaires). Ne pas exposer en production.

---

## ✅ Checklist de validation

- [x] Service `ImportService` créé avec parsing CSV
- [x] Router `/admin/import/*` créé et protégé (role admin)
- [x] 4 endpoints fonctionnels (employees, projects, 2× templates)
- [x] Enregistré dans `main.py`
- [x] Tests unitaires `parse_csv()` (5 tests ✅)
- [x] Gestion des erreurs (colonnes manquantes, encodage, doublons)
- [x] Validation email, dates, rôles
- [x] Multi-tenant (`org_id`)
- [x] Génération username + password temporaire
- [x] Cache pour optimisation (clients, managers)
- [x] Documentation complète

---

## 🚀 Prochaines étapes suggérées

1. **Tests d'intégration**: tester les endpoints avec une DB de test
2. **Validation avancée**: règles métier spécifiques (ex: budget_hours > 0)
3. **Notifications**: envoyer les credentials par email aux nouveaux employés
4. **Historique**: logger les imports dans une table `import_logs`
5. **Export**: endpoint pour exporter les données en CSV
6. **Batch processing**: support de gros fichiers (>1000 lignes) avec Celery

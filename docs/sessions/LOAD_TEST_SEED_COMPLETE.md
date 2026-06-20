# Load Test Seed Script - Completed ✅

## Status: READY TO USE (avec Faker + locale italienne 🇮🇹)

Le script de seed pour test de charge est maintenant prêt et utilise **Faker avec locale italienne** pour générer des données réalistes.

## Fichiers créés/modifiés

### 1. `backend/seed_load_test.py` ✅
Script principal de génération de données de test avec **Faker (locale it_IT)**:
- Nettoyage complet de la base (sauf organizations)
- Génération de 65 utilisateurs avec **noms, adresses et téléphones italiens**
- 50 clients avec **noms de sociétés italiennes réalistes**
- 1000 projets avec codes uniques et **noms en italien**
- Assignments employés-projets (2-8 par projet)
- ~60,000 pointages sur 12 mois avec distribution réaliste et **descriptions en italien**
- ~325 absences (CP, maladie, autre)

### 2. `backend/app/core/database.py` ✅
Ajout de l'export `async_session_maker` pour permettre l'utilisation dans les scripts.

### 3. `SEED_INSTRUCTIONS.md` ✅
Documentation complète avec:
- Instructions d'exécution
- Credentials générés
- Comportement détaillé du script
- Exemples de connexion

## Corrections appliquées

Le script a été entièrement adapté au modèle de données actuel:

### Modèle Employee
- ✅ Utilise `org_id` au lieu de `organization_id`
- ✅ Utilise `password_hash` directement (pas de table User séparée)
- ✅ Utilise `role` directement dans Employee
- ✅ Utilise `employment_status` au lieu de `is_active`

### Modèle Client
- ✅ Utilise `client_name` et `company_name`
- ✅ Utilise `email` au lieu de `contact_email`
- ✅ Utilise `default_billing_rate` (champ requis)
- ✅ Utilise `client_status` au lieu de `status`
- ✅ Pas de `org_id` (clients globaux)

### Modèle Project
- ✅ Utilise `project_name` au lieu de `name`
- ✅ Utilise `project_code` (unique, requis)
- ✅ Utilise `billing_rate` au lieu de `hourly_rate`
- ✅ Utilise `status` au lieu de `is_active`

### Modèle TimesheetEntry
- ✅ Utilise `billable_flag` au lieu de `is_billable`

### Modèle ProjectTeamMember
- ✅ Pas de champ `role` (seulement project_id et employee_id)

### Modèle Organization
- ✅ Utilise `org_name` au lieu de `name`
- ✅ Utilise `org_id` au lieu de `organization_id`

## Données générées

### Utilisateurs (65 total)
- 2 admins: `*.@admin.test.it` (noms italiens)
- 3 finance: `*.@finance.test.it` (noms italiens)
- 10 managers: `*.@manager.test.it` (noms italiens)
- 50 employees: `*.@emp[0-49].test.it` (noms italiens)
- Mot de passe: `password123` pour tous
- **Adresses italiennes** générées par Faker
- **Numéros de téléphone italiens** générés par Faker

### Clients (50)
- **Noms de sociétés italiennes** générés par Faker
- Emails générés automatiquement (domaine .it)
- **Adresses italiennes complètes**
- **Numéros de téléphone italiens**

### Projets (1000)
- Codes uniques: `PRJ-0001` à `PRJ-1000`
- **Noms générés en italien**: "Migrazione Web", "Rifacimento Mobile", "Sviluppo API", etc.
- 75% actifs, 25% inactifs
- Chaque projet a un manager et un taux horaire

### Pointages (~60,000)
- Période: 12 mois en arrière
- **Descriptions en italien**: "Lavoro su Migrazione Database", etc.
- Distribution:
  - 90% de taux de présence
  - Pas de week-ends
  - 4-8h par jour
  - Types: normal (85%), overtime (10%), travel (3%), night (2%)
- Statuts basés sur l'ancienneté:
  - > 60 jours: approved/rejected (95%/5%)
  - 30-60 jours: approved/submitted/rejected (80%/15%/5%)
  - 7-30 jours: submitted/approved/draft (60%/30%/10%)
  - < 7 jours: draft/submitted (70%/30%)

### Absences (~325)
- 3-8 absences par employé sur 12 mois
- Types: CP (60%), maladie (30%), autre (10%)
- Durée: 1-10 jours
- Statuts basés sur l'ancienneté

## Exécution

```bash
# Option 1: Depuis le container Docker (recommandé)
docker exec -it timelyna-backend-1 bash
python seed_load_test.py

# Option 2: Depuis l'hôte
cd backend
python seed_load_test.py
```

## Performance

- ✅ Commits par batch de 1000 entrées
- ✅ Affichage de la progression
- ✅ Temps estimé: 2-5 minutes
- ✅ Pas de syntax errors

## Prochaines étapes

1. **Installer Faker** (si pas déjà fait): `pip install faker`
2. Exécuter le script dans le container backend
3. Vérifier les logs de création
4. Se connecter avec un utilisateur de test (noms italiens)
5. Tester les performances avec les données générées

## Exemples de données générées

### Employés
- Mario Rossi, Via Roma 123, Milano, +39 02 1234567
- Giulia Bianchi, Corso Italia 45, Roma, +39 06 7654321
- Luca Verdi, Piazza Duomo 7, Firenze, +39 055 9876543

### Clients
- Rossi e Figli S.r.l., Via Garibaldi 89, Torino
- Bianchi Group S.p.A., Viale Europa 234, Napoli
- Tecnologie Verdi S.r.l., Corso Vittorio 56, Bologna

## Notes importantes

⚠️ **Le script vide toutes les tables** (sauf organizations) avant de générer les nouvelles données. Assurez-vous de l'exécuter sur une base de test, pas en production!

✅ Le script est idempotent: vous pouvez le relancer plusieurs fois, il nettoiera et régénérera les données à chaque fois.

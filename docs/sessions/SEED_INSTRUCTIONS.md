# Load Test Seed Script - Instructions

## Overview
Script de génération de données de test pour TimesheetPro avec des volumes réalistes pour tester la charge de l'application.

**🇮🇹 Utilise Faker avec locale italienne** pour générer des données réalistes (noms, adresses, téléphones, sociétés).

## Données générées
- **65 utilisateurs** : 50 employés + 10 managers + 2 admins + 3 finance
- **50 clients**
- **1000 projets** (75% actifs)
- **Pointages sur 12 mois** (~60,000 entrées estimées)
- **Absences** (~325 absences estimées)

## Prérequis
- Backend Docker container en cours d'exécution
- Base de données PostgreSQL accessible
- Variables d'environnement configurées dans `backend/.env`
- **Bibliothèque Faker installée** : `pip install faker`

## Exécution

### Option 1: Depuis le container Docker (recommandé)
```bash
# Entrer dans le container backend
docker exec -it timesheetpro-backend-1 bash

# Exécuter le script
python seed_load_test.py
```

### Option 2: Depuis l'hôte (si Python configuré localement)
```bash
cd backend
python seed_load_test.py
```

## Credentials générés

Tous les utilisateurs ont le même mot de passe: `password123`

Format des emails:
- **Admins**: `[nome].[cognome]@admin.test.it`
- **Managers**: `[nome].[cognome]@manager.test.it`
- **Finance**: `[nome].[cognome]@finance.test.it`
- **Employés**: `[nome].[cognome]@emp[N].test.it`

### Exemples (noms italiens générés par Faker)
```
mario.rossi@admin.test.it / password123
giulia.bianchi@manager.test.it / password123
luca.verdi@finance.test.it / password123
anna.ferrari@emp0.test.it / password123
```

## Comportement du script

1. **Nettoyage**: Vide toutes les tables (sauf organizations)
2. **Organisation**: Crée ou réutilise l'organisation existante
3. **Utilisateurs**: Crée les employés avec leurs rôles (noms, adresses, téléphones italiens)
4. **Clients**: Génère 50 clients avec noms de sociétés italiennes réalistes
5. **Projets**: Crée 1000 projets avec codes uniques et noms en italien
6. **Assignments**: Assigne 2-8 employés par projet actif
7. **Pointages**: Génère des entrées sur 12 mois avec:
   - 90% de taux de présence
   - Pas de pointages le week-end
   - Heures réalistes (4-8h par jour)
   - Types variés: normal (85%), overtime (10%), travel (3%), night (2%)
   - Statuts basés sur l'ancienneté (plus vieux = approuvé)
   - Descriptions en italien
8. **Absences**: Crée 3-8 absences par employé:
   - CP (60%), maladie (30%), autre (10%)
   - Durée: 1-10 jours

## Performance

- Commits par batch de 1000 entrées
- Temps d'exécution estimé: 2-5 minutes
- Affichage de la progression en temps réel

## Après l'exécution

Vous pouvez vous connecter avec n'importe quel utilisateur généré pour tester l'application avec des données réalistes.

Pour voir la liste complète des utilisateurs créés, consultez les logs du script ou interrogez la base:
```sql
SELECT email, role FROM employees ORDER BY role, email;
```

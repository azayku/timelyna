# Script de Seed avec Faker - Locale Italienne 🇮🇹

## ✅ Modifications complétées

Le script de seed a été entièrement refactorisé pour utiliser **Faker avec locale italienne (it_IT)**.

## 🎯 Changements appliqués

### 1. Bibliothèque Faker intégrée
```python
from faker import Faker
fake = Faker('it_IT')
```

### 2. Données italiennes générées

#### Employés
- **Noms et prénoms italiens** : Mario, Giulia, Luca, Anna, etc.
- **Adresses italiennes complètes** : Via Roma 123, Milano, etc.
- **Numéros de téléphone italiens** : +39 02 1234567, etc.
- **Emails** : mario.rossi@admin.test.it

#### Clients
- **Noms de sociétés italiennes** : Rossi e Figli S.r.l., Bianchi Group S.p.A., etc.
- **Adresses italiennes**
- **Téléphones italiens**
- **Emails avec domaine .it** : info@rossiefigli.it

#### Projets
- **Noms en italien** : Migrazione Web, Rifacimento Mobile, Sviluppo API, etc.
- **Préfixes italiens** : Migrazione, Rifacimento, Sviluppo, Manutenzione, etc.

#### Pointages
- **Descriptions en italien** : "Lavoro su Migrazione Database", etc.

### 3. Normalisation des caractères
Les caractères italiens (à, è, é, ì, ò, ù) sont normalisés pour les emails :
```python
def generate_email(first_name: str, last_name: str, domain: str = "test.it") -> str:
    first = first_name.lower().replace("à", "a").replace("è", "e")...
    return f"{first}.{last}@{domain}"
```

### 4. Gestion des doublons
- Emails uniques avec compteur automatique
- Noms de sociétés uniques
- Codes projets uniques

## 📦 Installation

### Dans le container Docker
```bash
docker exec -it timelyna-backend-1 bash
pip install faker
python seed_load_test.py
```

### Ou rebuild du container
```bash
docker-compose build backend
docker-compose up -d backend
docker exec -it timelyna-backend-1 python seed_load_test.py
```

## 📊 Exemples de données générées

### Employés
```
Mario Rossi
Via Roma 123, 20100 Milano MI
+39 02 1234567
mario.rossi@admin.test.it

Giulia Bianchi
Corso Italia 45, 00100 Roma RM
+39 06 7654321
giulia.bianchi@manager.test.it

Luca Verdi
Piazza Duomo 7, 50100 Firenze FI
+39 055 9876543
luca.verdi@finance.test.it
```

### Clients
```
Rossi e Figli S.r.l.
Via Garibaldi 89, 10100 Torino TO
+39 011 2345678
info@rossiefigli.it

Bianchi Group S.p.A.
Viale Europa 234, 80100 Napoli NA
+39 081 8765432
info@bianchigroup.it

Tecnologie Verdi S.r.l.
Corso Vittorio 56, 40100 Bologna BO
+39 051 3456789
info@tecnologieverdi.it
```

### Projets
```
PRJ-0001: Migrazione Web
PRJ-0002: Rifacimento Mobile
PRJ-0003: Sviluppo API
PRJ-0004: Manutenzione Database
PRJ-0005: Supporto Cloud
PRJ-0006: Audit Sicurezza
PRJ-0007: Ottimizzazione Performance
PRJ-0008: Integrazione CRM
PRJ-0009: Formazione DevOps
PRJ-0010: Consulenza Infrastruttura
```

### Pointages
```
2024-01-15: Lavoro su Migrazione Web - 8h
2024-01-16: Lavoro su Sviluppo API - 7.5h
2024-01-17: Lavoro su Manutenzione Database - 6h
```

## 🔐 Credentials de test

Tous les utilisateurs ont le mot de passe : `password123`

### Exemples d'emails générés
```
mario.rossi@admin.test.it
giulia.bianchi@manager.test.it
luca.verdi@finance.test.it
anna.ferrari@emp0.test.it
```

## ✨ Avantages de Faker

1. **Données réalistes** : Noms, adresses, téléphones authentiques
2. **Locale spécifique** : Données 100% italiennes
3. **Pas de listes statiques** : Génération dynamique
4. **Diversité** : Chaque exécution génère des données différentes
5. **Maintenance** : Pas besoin de maintenir des listes de noms

## 📝 Fichiers modifiés

- ✅ `backend/seed_load_test.py` - Script refactorisé avec Faker
- ✅ `backend/requirements.txt` - Ajout de faker==28.4.1
- ✅ `SEED_INSTRUCTIONS.md` - Documentation mise à jour
- ✅ `LOAD_TEST_SEED_COMPLETE.md` - Documentation complète mise à jour

## 🚀 Prêt à l'emploi

Le script est maintenant prêt à générer des données de test réalistes avec des informations italiennes authentiques!

# Utilisateurs Disponibles - TimesheetPro

## ⚠️ IMPORTANT

Le script de seed a **effacé toutes les anciennes données** et créé de nouveaux utilisateurs avec des noms italiens.

L'ancien utilisateur `brigitte17@example.net` n'existe plus!

## 🔐 Nouveaux Comptes Créés

### Admins (2)
- `niccolo.randazzo@admin.test.it` / `password123`
- `piermaria.palazzo@admin.test.it` / `password123`

### Finance (3)
- `lolita.simeoni@finance.test.it` / `password123`
- `mauro.casarin@finance.test.it` / `password123`
- `serafina.valmarana@finance.test.it` / `password123`

### Managers (10)
- `alderano.santoro@manager.test.it` / `password123`
- `gianni.cappelli@manager.test.it` / `password123`
- `gioachino.rosselli@manager.test.it` / `password123`
- `griselda.duse@manager.test.it` / `password123`
- `paoletta.malacarne@manager.test.it` / `password123`
- ... (5 autres managers)

### Employés (50)
- `achille.romano@emp15.test.it` / `password123` ✅ **486 pointages**
- `agnolo.baglioni@emp43.test.it` / `password123`
- `alessandra.moschino@emp33.test.it` / `password123`
- `annibale.toso@emp10.test.it` / `password123`
- `armando.crespi@emp26.test.it` / `password123`
- ... (45 autres employés)

## 📊 Données Créées

- **65 utilisateurs** (2 admins, 3 finance, 10 managers, 50 employés)
- **50 clients** italiens
- **1000 projets** avec noms italiens
- **28,814 pointages** sur 12 mois
- **360 absences** (congés, maladie, autre)

## 🎯 Utilisateur Recommandé pour Test

**Email**: `achille.romano@emp15.test.it`
**Password**: `password123`
**Données**: 486 pointages (436 approuvés, 32 soumis, 18 rejetés)

## 🔄 Pour Lister Tous les Utilisateurs

```bash
docker exec timesheetpro-backend python list_users.py
```

## 💡 Prochaines Étapes

1. **Déconnectez-vous** de l'application
2. **Reconnectez-vous** avec un des nouveaux comptes ci-dessus
3. Vous verrez maintenant tous les pointages créés!

## 🇮🇹 Note

Tous les utilisateurs ont des noms, adresses, téléphones et sociétés italiennes générés avec Faker (locale it_IT).

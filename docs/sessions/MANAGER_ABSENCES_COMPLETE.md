# Manager Absences - Implémentation Complète

## Date: 2026-05-06

## Résumé

La page "Absences équipe" pour les managers est maintenant complètement fonctionnelle avec les endpoints backend créés.

---

## Backend API

### Endpoints Créés

#### 1. GET `/api/v1/manager/absences`
Récupère toutes les absences des employés des organisations gérées par le manager.

**Query Parameters:**
- `status` (optional): `pending`, `approved`, `rejected`

**Réponse:**
```json
[
  {
    "absence_id": 1,
    "employee_id": 5,
    "employee_name": "Mario Rossi",
    "absence_type": "cp",
    "start_date": "2026-05-10",
    "end_date": "2026-05-15",
    "reason": "Vacances d'été",
    "status": "pending",
    "rejection_reason": null,
    "created_at": "2026-05-01T10:00:00"
  }
]
```

**Logique:**
- Récupère les organisations où `manager_id = current_user.employee_id`
- Filtre les absences des employés de ces organisations
- Optionnel: filtre par statut
- Tri par date de création (DESC)

---

#### 2. POST `/api/v1/manager/absences/{absence_id}/approve`
Approuve une demande d'absence.

**Réponse:**
```json
{
  "message": "Absence approved"
}
```

**Logique:**
- Vérifie que l'absence existe
- Vérifie que le manager gère l'organisation de l'employé
- Met à jour: `status = "approved"`, `approved_at`, `approved_by`

**Erreurs:**
- `404`: Absence non trouvée
- `403`: Manager non autorisé

---

#### 3. POST `/api/v1/manager/absences/{absence_id}/reject`
Rejette une demande d'absence avec un motif.

**Body:**
```json
{
  "reason": "Période de forte activité"
}
```

**Réponse:**
```json
{
  "message": "Absence rejected"
}
```

**Logique:**
- Vérifie que l'absence existe
- Vérifie que le manager gère l'organisation de l'employé
- Met à jour: `status = "rejected"`, `rejection_reason`, `approved_at`, `approved_by`

**Erreurs:**
- `404`: Absence non trouvée
- `403`: Manager non autorisé

---

## Frontend

### Page: `ManagerAbsencesPage.tsx`

**Route:** `/manager/absences`

**Fonctionnalités:**
- ✅ KPIs: Compteurs pour pending/approved/rejected
- ✅ Filtres par statut (boutons)
- ✅ Tableau avec colonnes:
  - Employé (avec avatar)
  - Type (CP, Maladie, Autre)
  - Date début
  - Date fin
  - Statut (badge)
  - Actions (Approuver/Rejeter)
- ✅ Modal de rejet avec champ motif
- ✅ Gestion des erreurs API
- ✅ Loading states
- ✅ Traductions i18n

**Droits d'accès:**
- Rôles autorisés: `manager`, `admin`
- Protection via `RoleRoute` component

---

## Modèle de Données

### Table: `absences`

**Champs utilisés:**
- `id` (PK) - Mappé à `absence_id` dans l'API
- `employee_id` (FK → employees)
- `absence_type`: `cp` | `sick` | `other`
- `start_date`: Date
- `end_date`: Date
- `notes`: Texte libre (mappé à `reason` dans l'API)
- `status`: `pending` | `approved` | `rejected`
- `rejection_reason`: Motif du rejet
- `approved_by` (FK → employees)
- `approved_at`: DateTime
- `created_at`: DateTime
- `updated_at`: DateTime

---

## Sécurité & Autorisations

### Vérifications Backend

1. **Authentication**: JWT token requis
2. **Role Check**: Manager ou Admin uniquement
3. **Organization Check**: 
   - Le manager ne peut voir/approuver que les absences des employés de SES organisations
   - Vérification: `Organization.manager_id == current_user.employee_id`

### Workflow

```
Employee → Crée absence (status: pending)
    ↓
Manager → Voit dans /manager/absences
    ↓
Manager → Approuve OU Rejette
    ↓
Employee → Voit le statut dans /history
```

---

## Traductions

### Clés i18n utilisées:
- `submissions.pending`
- `submissions.approved`
- `submissions.rejected`
- `common.employee`
- `common.type`
- `absences.start`
- `absences.end`
- `common.status`
- `common.actions`
- `managerAbsences.approve`
- `managerAbsences.reject`
- `managerAbsences.rejectReason`
- `managerAbsences.confirmReject`
- `common.cancel`

---

## Tests Manuels

### Scénario 1: Liste des absences
1. Se connecter en tant que manager (gianni.cappelli@manager.test.it)
2. Aller sur `/manager/absences`
3. Vérifier que les KPIs s'affichent
4. Vérifier que le tableau contient les absences des employés

### Scénario 2: Approuver une absence
1. Cliquer sur "Approuver" pour une absence pending
2. Vérifier que le statut passe à "Approuvé"
3. Vérifier que l'absence disparaît du filtre "En attente"
4. Vérifier qu'elle apparaît dans le filtre "Approuvés"

### Scénario 3: Rejeter une absence
1. Cliquer sur "Rejeter" pour une absence pending
2. Saisir un motif dans la modal
3. Cliquer sur "Confirmer"
4. Vérifier que le statut passe à "Rejeté"
5. Vérifier que l'absence apparaît dans le filtre "Rejetés"

### Scénario 4: Sécurité
1. Essayer d'approuver une absence d'un employé d'une autre organisation
2. Vérifier que l'API retourne 403 Forbidden

---

## Améliorations Futures

### Design
- [ ] Ajouter pagination (actuellement toutes les absences chargées)
- [ ] Ajouter recherche par nom d'employé
- [ ] Ajouter filtre par type d'absence
- [ ] Ajouter filtre par date
- [ ] Vue calendrier des absences

### Fonctionnalités
- [ ] Notifications email lors de l'approbation/rejet
- [ ] Historique des modifications
- [ ] Export CSV/PDF
- [ ] Statistiques d'absences par employé
- [ ] Validation des chevauchements d'absences
- [ ] Solde de congés restants

### UX
- [ ] Design responsive amélioré pour mobile
- [ ] Cartes au lieu de tableau sur mobile
- [ ] Actions groupées (approuver plusieurs absences)
- [ ] Commentaires sur les absences

---

## Fichiers Modifiés

### Backend
- ✅ `backend/app/api/v1/manager.py` - Ajout des 3 endpoints absences

### Frontend
- ✅ `frontend-v2/src/pages/ManagerAbsencesPage.tsx` - Déjà existant, fonctionnel
- ✅ `frontend-v2/src/features/absences/api.ts` - Déjà existant
- ✅ `frontend-v2/src/features/absences/hooks.ts` - Déjà existant
- ✅ `frontend-v2/src/App.tsx` - Route déjà configurée

---

## Statut Final

✅ **BACKEND COMPLET** - Tous les endpoints créés et testés
✅ **FRONTEND COMPLET** - Page déjà existante et fonctionnelle
✅ **SÉCURITÉ** - Vérifications d'autorisation en place
✅ **TRADUCTIONS** - i18n configuré
✅ **DOCKER** - Backend redémarré avec succès

**Prêt pour utilisation!**

---

## Commandes Docker

Pour redémarrer après modifications:
```bash
docker-compose restart backend
```

Pour rebuild complet:
```bash
docker-compose down
docker rmi -f timesheetpro-backend
docker-compose build --no-cache backend
docker-compose up -d
```

---

**Dernière mise à jour**: 2026-05-06
**Status**: ✅ Opérationnel

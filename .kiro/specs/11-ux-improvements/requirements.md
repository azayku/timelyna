# Requirements — UX Improvements & Operational Features

## Feature Overview
Ensemble de corrections et nouvelles fonctionnalités opérationnelles : correction de la saisie des heures, génération automatique des identifiants employés, vue de disponibilité, grilles AG Grid, templates d'emails paramétrables, rappels automatiques de saisie, et déclaration d'absences.

---

## User Stories & Acceptance Criteria

### US-01 — Correction de la saisie des heures (navigation semaine)
**As an** employee,
**I want to** naviguer librement entre les semaines passées et saisir des heures sur n'importe quelle semaine passée,
**So that** je puisse corriger ou compléter des oublis.

**Acceptance Criteria:**
- WHEN un employé navigue vers une semaine passée sur `TimesheetEntryPage` THE SYSTEM SHALL afficher uniquement les projets auxquels il est affecté pour le jour sélectionné
- WHEN un employé sélectionne une date THE SYSTEM SHALL filtrer la liste des projets disponibles selon l'appartenance de l'employé à l'équipe du projet à cette date
- WHEN un employé navigue en arrière depuis `TimesheetWeekPage` THE SYSTEM SHALL conserver la semaine sélectionnée dans l'URL et la propager à `TimesheetEntryPage` via un query param `?date=`
- WHEN un employé est sur `TimesheetEntryPage` THE SYSTEM SHALL permettre de saisir des heures pour n'importe quelle date passée (pas seulement aujourd'hui)
- WHEN la date sélectionnée est dans le futur THE SYSTEM SHALL désactiver le formulaire de saisie avec un message explicatif

### US-02 — Génération automatique du username et mot de passe par défaut
**As an** admin,
**I want to** que le système génère automatiquement un username et un mot de passe par défaut lors de la création d'un employé,
**So that** je n'ai pas à les saisir manuellement.

**Acceptance Criteria:**
- WHEN un admin crée un employé THE SYSTEM SHALL générer automatiquement un `username` : 4 premières lettres du nom (last_name) + 4 premières lettres du prénom (first_name), en minuscules, sans accents
- WHEN le username généré existe déjà THE SYSTEM SHALL ajouter un suffixe numérique incrémental (ex: `martjean01`)
- WHEN un admin crée un employé avec une date de naissance THE SYSTEM SHALL générer le mot de passe par défaut : `username` + date de naissance au format `DDMMYYYY` (ex: `martjean01012000`)
- WHEN aucune date de naissance n'est fournie THE SYSTEM SHALL générer un mot de passe aléatoire sécurisé (16 caractères)
- THE SYSTEM SHALL stocker le `username` sur le modèle `Employee` (nouveau champ)
- THE SYSTEM SHALL stocker la `birth_date` sur le modèle `Employee` (nouveau champ)
- WHEN l'employé se connecte pour la première fois THE SYSTEM SHALL le forcer à changer son mot de passe (`must_change_password` flag)
- THE SYSTEM SHALL afficher le username généré dans la réponse de création (visible une seule fois pour l'admin)

### US-03 — Vue de disponibilité des employés
**As an** admin or manager,
**I want to** voir quels employés sont disponibles à une date précise ou sur une plage de dates,
**So that** je puisse planifier les affectations de projets.

**Acceptance Criteria:**
- WHEN un admin/manager consulte la vue disponibilité THE SYSTEM SHALL afficher tous les employés actifs avec leur statut pour chaque jour de la plage
- THE SYSTEM SHALL calculer la disponibilité en tenant compte des absences déclarées (US-07) et des heures déjà saisies
- WHEN un employé a des heures saisies pour un jour THE SYSTEM SHALL afficher le total d'heures et le pourcentage d'occupation (heures saisies / standard_hours_per_day)
- WHEN un employé est absent (CP, maladie) THE SYSTEM SHALL afficher le type d'absence
- THE SYSTEM SHALL supporter une plage de dates de 1 à 31 jours maximum
- THE SYSTEM SHALL permettre de filtrer par département et par projet

### US-04 — Intégration AG Grid
**As a** user,
**I want to** naviguer dans les tableaux de données avec des filtres par colonne, tri et pagination,
**So that** je puisse trouver rapidement les informations dont j'ai besoin.

**Acceptance Criteria:**
- THE SYSTEM SHALL remplacer les tableaux HTML natifs par AG Grid Community sur les pages : `AdminUsersPage`, `AdminProjectsPage`, `AdminClientsPage`, `ApprovalsPage`, `SubmissionsPage`, `InvoicesPage`, `FinancialReportPage`
- WHEN un utilisateur charge un tableau THE SYSTEM SHALL afficher 25 lignes par défaut (configurable : 10, 25, 50, 100)
- THE SYSTEM SHALL activer les filtres dans les en-têtes de colonnes (text filter, number filter, date filter selon le type)
- THE SYSTEM SHALL activer le tri par colonne (clic sur l'en-tête)
- THE SYSTEM SHALL persister les préférences de filtre/tri dans `localStorage` par page
- THE SYSTEM SHALL afficher le nombre total de résultats et la pagination en bas du tableau
- WHEN les données sont chargées côté serveur THE SYSTEM SHALL utiliser le server-side row model d'AG Grid avec pagination API

### US-05 — Templates d'emails paramétrables
**As an** admin,
**I want to** personnaliser les templates d'emails envoyés aux employés,
**So that** les communications correspondent à l'identité de mon organisation.

**Acceptance Criteria:**
- THE SYSTEM SHALL rendre paramétrables les templates suivants : `welcome_new_employee` (invitation à se connecter et changer le mot de passe), `password_reset` (mot de passe oublié)
- WHEN un admin modifie un template THE SYSTEM SHALL sauvegarder le contenu personnalisé en base de données
- THE SYSTEM SHALL supporter les variables de substitution : `{{first_name}}`, `{{last_name}}`, `{{username}}`, `{{setup_link}}`, `{{org_name}}`, `{{reset_link}}`
- WHEN aucun template personnalisé n'existe THE SYSTEM SHALL utiliser le template par défaut (Jinja2 HTML)
- THE SYSTEM SHALL fournir un aperçu en temps réel du rendu du template avec des données fictives
- WHEN un admin envoie un email de test THE SYSTEM SHALL envoyer un email de prévisualisation à son adresse

### US-06 — Rappels automatiques de saisie des heures
**As a** system,
**I want to** envoyer des rappels automatiques aux employés qui n'ont pas saisi leurs heures,
**So that** les timesheets soient complets et soumis à temps.

**Acceptance Criteria:**
- THE SYSTEM SHALL envoyer un rappel par email chaque lundi à 16h00 aux employés qui n'ont pas saisi d'heures pour la semaine précédente (au moins un projet actif affecté)
- THE SYSTEM SHALL envoyer un rappel mensuel le dernier jour du mois à 12h00 aux employés qui ont des semaines non soumises dans le mois écoulé
- WHEN un employé a déjà soumis toutes ses semaines du mois THE SYSTEM SHALL ne pas lui envoyer le rappel mensuel
- WHEN un employé n'a aucun projet actif affecté THE SYSTEM SHALL ne pas lui envoyer de rappel
- THE SYSTEM SHALL inclure dans l'email : la liste des semaines manquantes, un lien direct vers la saisie
- WHEN un employé a désactivé les rappels dans ses préférences de notification THE SYSTEM SHALL respecter ce choix
- THE SYSTEM SHALL logger chaque envoi de rappel dans `notification_logs`

### US-08 — Activation / Désactivation de compte employé (Admin)
**As an** admin,
**I want to** désactiver ou réactiver le compte d'un employé,
**So that** je puisse gérer les accès sans supprimer les données historiques.

**Acceptance Criteria:**
- WHEN un admin désactive un employé THE SYSTEM SHALL passer son `employment_status` à `inactive` et révoquer tous ses refresh tokens actifs
- WHEN un employé désactivé tente de se connecter THE SYSTEM SHALL retourner une erreur 403 avec le message "Compte désactivé"
- WHEN un admin réactive un employé THE SYSTEM SHALL passer son `employment_status` à `active`
- WHEN un employé est désactivé THE SYSTEM SHALL l'exclure des rappels de saisie (US-06) et des calculs de disponibilité (US-03)
- THE SYSTEM SHALL afficher clairement le statut actif/inactif dans `AdminUsersPage` avec un bouton toggle
- WHEN un admin désactive un employé THE SYSTEM SHALL empêcher toute nouvelle saisie d'heures par cet employé
- THE SYSTEM SHALL conserver toutes les données historiques (timesheets, approbations, factures) lors d'une désactivation

### US-07 — Déclaration d'absences
**As an** employee,
**I want to** déclarer une absence (congé payé, arrêt maladie, autre),
**So that** mon manager et l'admin soient informés et que mes heures ne soient pas réclamées.

**Acceptance Criteria:**
- WHEN un employé déclare une absence THE SYSTEM SHALL créer un enregistrement avec : `employee_id`, `absence_type` (cp / sick_leave / other), `start_date`, `end_date`, `notes`, `status` (pending / approved / rejected)
- WHEN une absence est soumise THE SYSTEM SHALL notifier le manager de l'employé
- WHEN un manager approuve une absence THE SYSTEM SHALL mettre à jour le statut et notifier l'employé
- WHEN un manager rejette une absence THE SYSTEM SHALL exiger une raison et notifier l'employé
- WHEN un employé a une absence approuvée sur une journée THE SYSTEM SHALL exclure cette journée des rappels de saisie (US-06)
- WHEN un employé tente de saisir des heures sur un jour avec absence approuvée THE SYSTEM SHALL afficher un avertissement (mais ne pas bloquer)
- THE SYSTEM SHALL afficher le solde de congés restants si `annual_leave_days` est configuré sur l'employé
- WHEN un admin consulte la vue disponibilité (US-03) THE SYSTEM SHALL inclure les absences approuvées

</content>

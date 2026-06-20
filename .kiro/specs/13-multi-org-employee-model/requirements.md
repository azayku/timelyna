# Requirements Document

## Introduction

Cette fonctionnalité étend le modèle employé/organisation de Timelyna pour supporter
le multi-organisation avec gestion des compétences, affectation intelligente aux projets,
reporting par manager, mutation d'employés entre organisations, et gestion multi-équipes.
Le modèle existant (tables `employees`, `projects`, `skill_rates`, `org_settings`,
`project_team_members`) est étendu sans rupture de compatibilité.

## Glossaire

- **Organization** : entité structurelle regroupant des employés sous un manager responsable.
  Correspond à une ligne dans la table `organizations` (nouvelle table).
- **Employee** : utilisateur avec le rôle `employee` ou `manager`, rattaché à exactement une organisation.
- **Manager** : employé avec le rôle `manager`, responsable d'une ou plusieurs organisations.
- **Admin** : employé avec le rôle `admin`, disposant d'un accès complet à toutes les organisations.
- **CRA** (Compte Rendu d'Activité) : feuille de temps hebdomadaire soumise par un employé pour validation.
  Correspond à la table `approvals` existante.
- **Skill** : compétence déclarée dans la page de paramétrage, référencée dans `skill_rates`.
- **Employee_Skill** : association entre un employé et une compétence (table `employee_skills`).
- **Project** : mission client portée par un manager, avec une liste de compétences attendues.
- **Project_Skill** : compétence requise pour un projet (table `project_required_skills`).
- **Mutation** : transfert administratif d'un employé d'une organisation vers une autre.
- **Mutation_Log** : enregistrement historique d'une mutation (table `employee_mutation_logs`).
- **Availability_Period** : période de disponibilité d'un employé, dérivée de l'absence de chevauchement avec d'autres projets actifs.
- **System** : le backend Timelyna (FastAPI + SQLAlchemy async).
- **UI** : le frontend Timelyna (React + TypeScript).

---

## Requirements

### Requirement 1 : Modèle Organisation

**User Story :** En tant qu'admin, je veux gérer des organisations distinctes avec chacune un manager responsable, afin de structurer les équipes de l'entreprise.

#### Acceptance Criteria

1. THE System SHALL stocker chaque organisation dans une table `organizations` avec les champs : `org_id`, `org_name`, `manager_id` (FK vers `employees`), `created_at`, `updated_at`, `deleted_at`.
2. THE System SHALL conserver la colonne `org_id` existante dans la table `employees` comme clé étrangère vers `organizations.org_id`.
3. WHEN un admin crée une organisation, THE System SHALL exiger un `org_name` non vide et un `manager_id` valide pointant vers un employé avec le rôle `manager` ou `admin`.
4. WHEN un admin met à jour l'email d'un employé, THE System SHALL valider que le nouvel email est unique dans la table `employees` avant de persister la modification.
5. WHEN un admin met à jour le type (rôle) d'un employé, THE System SHALL accepter uniquement les valeurs `employee`, `manager`, `admin`, `finance`.
6. IF un `manager_id` fourni lors de la création ou mise à jour d'une organisation ne correspond à aucun employé actif, THEN THE System SHALL retourner une erreur `422` avec le code `invalid_manager`.
7. THE System SHALL appliquer un soft-delete (`deleted_at`) sur les organisations supprimées sans supprimer les employés rattachés.

---

### Requirement 2 : CRA — Soumission et validation par le manager de l'organisation

**User Story :** En tant qu'employé, je veux soumettre mon CRA à mon manager d'organisation pour validation, afin que les heures travaillées soient officiellement approuvées.

#### Acceptance Criteria

1. WHEN un employé soumet un CRA, THE System SHALL identifier le manager responsable via `organizations.manager_id` en utilisant l'`org_id` de l'employé.
2. WHEN un CRA est soumis, THE System SHALL créer ou mettre à jour l'enregistrement `approvals` avec le `manager_id` résolu depuis l'organisation de l'employé.
3. IF un employé n'est rattaché à aucune organisation valide au moment de la soumission, THEN THE System SHALL retourner une erreur `422` avec le code `no_valid_organization`.
4. WHILE un CRA a le statut `pending`, THE System SHALL permettre au manager de l'organisation de l'approuver ou de le rejeter.
5. WHEN un manager approuve ou rejette un CRA, THE System SHALL enregistrer `decided_at` et mettre à jour le statut dans `approvals`.
6. THE UI SHALL afficher dans la liste des CRA en attente uniquement les CRA des employés appartenant aux organisations dont l'utilisateur connecté est manager.

---

### Requirement 3 : Compétences employé

**User Story :** En tant qu'admin, je veux associer des compétences à chaque employé depuis une liste centralisée, afin de pouvoir les affecter aux projets selon leurs aptitudes.

#### Acceptance Criteria

1. THE System SHALL stocker les compétences disponibles dans la table `skill_rates` existante (champ `skill_name`), par organisation (`org_id`).
2. THE System SHALL stocker les compétences d'un employé dans une table `employee_skills` avec les champs : `id`, `employee_id` (FK), `skill_rate_id` (FK vers `skill_rates`), `assigned_at`.
3. THE System SHALL garantir l'unicité de la paire `(employee_id, skill_rate_id)` dans `employee_skills`.
4. WHEN un admin ajoute une compétence à un employé, THE System SHALL vérifier que la compétence (`skill_rate_id`) appartient à la même organisation que l'employé.
5. WHEN un admin retire une compétence d'un employé, THE System SHALL supprimer la ligne correspondante dans `employee_skills` sans affecter les entrées `project_team_members` existantes.
6. THE UI SHALL afficher la liste des compétences disponibles dans une page de paramétrage dédiée, permettant l'ajout et la suppression de compétences par organisation.
7. THE UI SHALL afficher les compétences d'un employé dans sa fiche et permettre leur modification par un admin.

---

### Requirement 4 : Compétences requises par projet et suggestion automatique d'employés

**User Story :** En tant que manager, je veux saisir les compétences attendues lors de la création d'un projet et recevoir automatiquement une liste d'employés disponibles et compétents, afin de constituer rapidement l'équipe projet.

#### Acceptance Criteria

1. THE System SHALL stocker les compétences requises d'un projet dans une table `project_required_skills` avec les champs : `id`, `project_id` (FK), `skill_rate_id` (FK), `quantity` (nombre d'employés requis avec cette compétence).
2. WHEN un manager crée ou modifie un projet, THE System SHALL permettre de définir une liste de `skill_rate_id` requis avec leur quantité.
3. WHEN un manager demande les suggestions d'employés pour un projet, THE System SHALL retourner les employés qui : (a) possèdent au moins une des compétences requises via `employee_skills`, (b) n'ont pas d'absence approuvée couvrant la totalité de la période `[project.start_date, project.end_date]`, (c) appartiennent à une organisation active.
4. THE System SHALL trier les suggestions par nombre de compétences requises correspondantes (décroissant).
5. IF aucun employé ne correspond aux critères de suggestion, THEN THE System SHALL retourner une liste vide sans erreur.
6. THE UI SHALL afficher les suggestions d'employés avec leurs compétences correspondantes lors de la création ou modification d'un projet.
7. WHEN un projet est créé, THE System SHALL exiger un `manager_id` valide pointant vers un employé avec le rôle `manager` ou `admin`.
8. THE System SHALL permettre à un manager d'avoir zéro ou plusieurs projets associés via `projects.manager_id`.

---

### Requirement 5 : Reporting manager

**User Story :** En tant que manager, je veux accéder au reporting consolidé de mon organisation et de mon équipe, afin de suivre les heures, les absences et l'activité de mes collaborateurs.

#### Acceptance Criteria

1. WHEN un manager accède au reporting, THE System SHALL retourner uniquement les données (heures, absences, CRA) des employés appartenant aux organisations dont il est manager (`organizations.manager_id = current_user.employee_id`).
2. THE System SHALL agréger les heures travaillées par employé, par projet et par période pour les organisations du manager.
3. THE System SHALL inclure dans le reporting le statut des CRA (pending, approved, rejected) pour chaque employé de l'organisation.
4. WHERE le rôle de l'utilisateur est `admin`, THE System SHALL retourner le reporting de toutes les organisations sans restriction.
5. THE UI SHALL afficher un tableau de bord de reporting accessible depuis le menu principal pour les rôles `manager` et `admin`.

---

### Requirement 6 : Mutation d'employé entre organisations

**User Story :** En tant qu'admin, je veux transférer un employé d'une organisation à une autre, afin de refléter les changements structurels de l'entreprise.

#### Acceptance Criteria

1. WHEN un admin déclenche une mutation, THE System SHALL mettre à jour `employees.org_id` avec le nouvel `org_id` cible.
2. THE System SHALL enregistrer chaque mutation dans une table `employee_mutation_logs` avec les champs : `id`, `employee_id`, `from_org_id`, `to_org_id`, `mutated_by` (FK vers `employees`), `mutated_at`, `reason` (optionnel, String 500).
3. THE System SHALL conserver l'historique complet des mutations dans `employee_mutation_logs` sans soft-delete.
4. IF l'`org_id` cible d'une mutation ne correspond à aucune organisation active, THEN THE System SHALL retourner une erreur `422` avec le code `invalid_target_organization`.
5. IF l'employé à muter est lui-même manager d'une organisation, THEN THE System SHALL retourner une erreur `422` avec le code `employee_is_org_manager` et exiger une réaffectation préalable du manager de cette organisation.
6. WHEN une mutation est effectuée, THE System SHALL mettre à jour `employees.manager_id` avec le `manager_id` de la nouvelle organisation si l'employé n'a pas de manager explicitement défini.
7. THE UI SHALL proposer une action "Muter" dans la fiche employé, accessible uniquement aux admins, avec sélection de l'organisation cible et saisie optionnelle d'un motif.

---

### Requirement 7 : Multi-équipes — un manager peut gérer plusieurs organisations

**User Story :** En tant que manager, je veux pouvoir être responsable de plusieurs organisations, afin de gérer des équipes distinctes au sein de la même entreprise.

#### Acceptance Criteria

1. THE System SHALL permettre qu'un même `employee_id` soit référencé comme `manager_id` dans plusieurs lignes de la table `organizations`.
2. WHEN un manager accède à ses équipes, THE System SHALL retourner la liste de toutes les organisations dont il est manager, avec le nombre d'employés par organisation.
3. THE System SHALL agréger les CRA en attente de toutes les organisations du manager dans une vue unifiée.
4. THE UI SHALL afficher un sélecteur d'organisation dans les vues manager (CRA, reporting, équipe) permettant de filtrer par organisation ou d'afficher toutes les organisations à la fois.
5. THE System SHALL appliquer les mêmes règles de visibilité (Requirement 2 et 5) pour chaque organisation gérée par le manager, sans exception.

---

### Requirement 8 : Intégrité et rétrocompatibilité du modèle existant

**User Story :** En tant que développeur, je veux que les extensions du modèle n'impactent pas les fonctionnalités existantes, afin de garantir la stabilité de la plateforme.

#### Acceptance Criteria

1. THE System SHALL créer une migration Alembic additive (sans `DROP COLUMN` ni modification de contraintes existantes) pour toutes les nouvelles tables et colonnes.
2. THE System SHALL initialiser `organizations` avec une ligne par défaut (`org_id = 1`, `org_name = "Organisation par défaut"`) lors de la migration, en rattachant le premier admin existant comme manager.
3. THE System SHALL conserver la valeur `org_id = 1` dans `employees` pour tous les employés existants après migration.
4. FOR ALL enregistrements `approvals` existants, THE System SHALL conserver le `manager_id` déjà stocké sans le recalculer automatiquement.
5. THE System SHALL conserver la table `org_settings` existante et y ajouter une FK optionnelle vers `organizations` sans contrainte `NOT NULL` pour assurer la rétrocompatibilité.
6. IF une migration échoue partiellement, THEN THE System SHALL permettre un rollback complet via `alembic downgrade`.

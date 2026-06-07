# Requirements — Module Finance Pro, AG Grid, i18n, Dark Mode & Employee Enhancements

## Feature Overview
Refonte complète du module finance inspirée des outils professionnels (Sage, QuickBooks, Harvest), intégration AG Grid sur tous les tableaux, mode sombre, support multilingue (FR/EN/IT), système de licence spécifique au module finance, désactivation différée de compte, et enrichissement du profil employé (date de naissance obligatoire + adresse).

---

## US-01 — Licence du module Finance Pro

### Description
Le module Finance Pro est une fonctionnalité premium activée par une clé de licence spécifique. L'admin saisit la clé dans la page de gestion des licences. Si la clé est valide et non expirée, le module est visible et accessible. Dès que la licence expire (au 01/01 de l'année suivante), le module disparaît entièrement de l'interface.

### Mécanisme de la clé de licence (obfuscation de la date d'expiration)

La clé de licence est une chaîne encodée qui contient la date d'expiration de façon obfusquée. L'algorithme est le suivant :

**Génération de la clé (côté publisher) :**
1. Prendre la date d'expiration au format `YYYYMMDD` (ex: `20261231`)
2. Calculer un HMAC-SHA256 de cette date avec une clé secrète partagée (`FINANCE_LICENSE_SECRET`)
3. Prendre les 8 premiers caractères du HMAC en hexadécimal → `hmac_prefix`
4. XOR chaque caractère de la date avec les caractères cycliques du `hmac_prefix` → `xored_date` (en hex)
5. Construire la clé finale : `FIN-{xored_date}-{hmac_prefix}-{checksum}` où `checksum` = CRC32 des 3 premiers segments en base36

**Validation de la clé (côté app) :**
1. Parser la clé : extraire `xored_date`, `hmac_prefix`, `checksum`
2. Vérifier le checksum CRC32
3. Recalculer le HMAC-SHA256 de la date candidate avec `FINANCE_LICENSE_SECRET`
4. Vérifier que les 8 premiers caractères du HMAC correspondent à `hmac_prefix`
5. Décoder la date par XOR inverse
6. Vérifier que la date d'expiration est dans le futur (> aujourd'hui)

**Avantages :** La date n'est jamais en clair dans la clé. Sans la clé secrète `FINANCE_LICENSE_SECRET`, il est impossible de forger une clé valide ou de lire la date d'expiration.

### Acceptance Criteria
- WHEN un admin saisit une clé valide THE SYSTEM SHALL activer le module Finance Pro et afficher la date d'expiration
- WHEN la clé est invalide (mauvais format, checksum incorrect, HMAC invalide) THE SYSTEM SHALL retourner une erreur explicite
- WHEN la date d'expiration est dépassée THE SYSTEM SHALL refuser la clé avec le message "Licence expirée"
- WHEN la licence est active THE SYSTEM SHALL afficher un badge "Finance Pro — expire le JJ/MM/AAAA" dans la page licences
- WHEN la date du serveur atteint le 01/01 de l'année suivante THE SYSTEM SHALL masquer automatiquement le module Finance Pro sans action admin
- WHEN la licence est à moins de 30 jours d'expiration THE SYSTEM SHALL afficher un bandeau d'avertissement à l'admin
- THE SYSTEM SHALL stocker la clé validée en base de données dans `org_settings` (champ `finance_license_key`)
- THE SYSTEM SHALL vérifier la validité de la licence à chaque requête sur les routes Finance Pro via un middleware dédié

---

## US-02 — Dashboard Finance Pro

### Description
Dashboard financier complet inspiré de Sage/Harvest avec KPIs temps réel, graphiques interactifs et widgets responsives.

### Acceptance Criteria
- THE SYSTEM SHALL afficher les KPIs suivants : CA du mois, CA de l'année, heures facturables vs non-facturables, taux de recouvrement, marge brute, nombre de factures en attente
- THE SYSTEM SHALL afficher un graphique de CA mensuel sur 12 mois glissants (courbe + barres combinées)
- THE SYSTEM SHALL afficher un graphique de répartition du CA par client (donut chart)
- THE SYSTEM SHALL afficher un graphique d'évolution heures facturées vs budget par projet (barres groupées)
- THE SYSTEM SHALL afficher un tableau des 5 dernières factures avec statut et montant
- THE SYSTEM SHALL afficher un widget "Factures en retard" (sent > 30 jours sans paiement marqué)
- WHEN un widget est cliqué THE SYSTEM SHALL naviguer vers la vue détaillée correspondante
- THE SYSTEM SHALL être entièrement responsive (mobile, tablette, desktop)
- THE SYSTEM SHALL supporter le mode sombre pour tous les graphiques et widgets

---

## US-03 — Gestion avancée des factures

### Description
Interface de facturation professionnelle avec workflow complet, aperçu PDF, et suivi des paiements.

### Acceptance Criteria
- THE SYSTEM SHALL afficher la liste des factures dans un tableau AG Grid avec filtres : client, statut (draft/ready/sent/paid/overdue), période, montant
- WHEN une facture est créée THE SYSTEM SHALL générer automatiquement un numéro séquentiel au format `FAC-YYYY-NNNN`
- THE SYSTEM SHALL permettre d'ajouter des lignes manuelles à une facture (en plus des heures importées)
- THE SYSTEM SHALL calculer automatiquement : sous-total HT, TVA (taux paramétrable dans OrgSettings), total TTC
- THE SYSTEM SHALL afficher un aperçu PDF en temps réel dans un panneau latéral
- WHEN une facture est envoyée THE SYSTEM SHALL enregistrer la date d'envoi et calculer la date d'échéance (30j par défaut, paramétrable)
- THE SYSTEM SHALL permettre de marquer une facture comme "Payée" avec la date de paiement
- WHEN une facture dépasse sa date d'échéance THE SYSTEM SHALL la marquer automatiquement `overdue` via une tâche Celery quotidienne
- THE SYSTEM SHALL afficher un historique des actions sur chaque facture (audit trail)

---

## US-04 — Rapports financiers avancés

### Acceptance Criteria
- THE SYSTEM SHALL fournir un rapport P&L (Profit & Loss) par période : revenus, coûts internes, marge brute, marge nette
- THE SYSTEM SHALL fournir un rapport de rentabilité par projet : budget vs réel, heures vs facturation, marge
- THE SYSTEM SHALL fournir un rapport de vieillissement des créances (aging report) : 0-30j, 31-60j, 61-90j, >90j
- THE SYSTEM SHALL fournir un rapport de prévision de trésorerie sur 3 mois
- WHEN un rapport est exporté THE SYSTEM SHALL générer un PDF ou CSV avec en-tête organisation
- THE SYSTEM SHALL permettre de comparer deux périodes côte à côte

---

## US-05 — Intégration AG Grid (tous les tableaux)

### Description
Tous les tableaux de l'application doivent utiliser AG Grid Community avec filtres dans les en-têtes, tri, et pagination configurable.

### Acceptance Criteria
- THE SYSTEM SHALL utiliser AG Grid Community sur toutes les pages à tableau : `AdminUsersPage`, `AdminProjectsPage`, `AdminClientsPage`, `ApprovalsPage`, `SubmissionsPage`, `InvoicesPage`, `FinancialReportPage`, `AbsencesPage`, `ManagerAbsencesPage`, `AvailabilityPage`
- WHEN un utilisateur charge un tableau THE SYSTEM SHALL afficher 25 lignes par défaut (configurable : 10, 25, 50, 100)
- THE SYSTEM SHALL activer les filtres flottants dans les en-têtes de colonnes (text, number, date selon le type)
- THE SYSTEM SHALL activer le tri par colonne (clic sur l'en-tête)
- THE SYSTEM SHALL persister les préférences de filtre/tri dans `localStorage` par page via `storageKey`
- THE SYSTEM SHALL afficher le nombre total de résultats et la pagination en bas du tableau
- THE SYSTEM SHALL adapter le thème AG Grid au mode sombre (`ag-theme-alpine-dark`)

---

## US-06 — Désactivation différée d'un compte employé

### Description
L'admin peut programmer la désactivation d'un compte à une date future (ex: fin de contrat), au lieu de désactiver immédiatement.

### Acceptance Criteria
- WHEN un admin désactive un employé THE SYSTEM SHALL proposer deux options : "Immédiatement" ou "À une date précise"
- WHEN une date de désactivation future est choisie THE SYSTEM SHALL stocker `deactivation_scheduled_at` sur l'employé
- THE SYSTEM SHALL afficher un badge "Désactivation prévue le JJ/MM/AAAA" dans la liste des employés
- WHEN la date de désactivation est atteinte THE SYSTEM SHALL exécuter la désactivation automatiquement via une tâche Celery quotidienne (`process_scheduled_deactivations`)
- WHEN la désactivation automatique s'exécute THE SYSTEM SHALL révoquer tous les refresh tokens de l'employé
- WHEN un admin annule une désactivation programmée THE SYSTEM SHALL supprimer `deactivation_scheduled_at`
- THE SYSTEM SHALL envoyer un email de notification à l'employé 7 jours avant la désactivation programmée

---

## US-07 — Enrichissement du profil employé (date de naissance + adresse)

### Description
La date de naissance et l'adresse sont désormais obligatoires à la création d'un employé. La date de naissance est utilisée pour générer le mot de passe par défaut (spec 11). L'adresse est nécessaire pour les documents légaux et la paie.

### Acceptance Criteria
- WHEN un admin crée un employé THE SYSTEM SHALL exiger : `first_name`, `last_name`, `email`, `role`, `birth_date`, `address`
- WHEN `birth_date` est absent THE SYSTEM SHALL retourner une erreur 422 "La date de naissance est obligatoire"
- WHEN `address` est absent THE SYSTEM SHALL retourner une erreur 422 "L'adresse est obligatoire"
- THE SYSTEM SHALL stocker `address` sur le modèle `Employee` (nouveau champ `VARCHAR(500)`)
- THE SYSTEM SHALL utiliser `birth_date` pour générer le mot de passe par défaut : `username + DDMMYYYY`
- THE SYSTEM SHALL afficher `birth_date` et `address` dans le formulaire de création/édition admin
- THE SYSTEM SHALL afficher l'âge calculé (en années) à côté de la date de naissance dans la fiche employé
- WHEN un employé est édité THE SYSTEM SHALL permettre de modifier `address` et `birth_date`

---

## US-08 — Internationalisation (i18n)

### Acceptance Criteria
- WHEN un utilisateur arrive sur la page de connexion THE SYSTEM SHALL afficher un sélecteur de langue (FR 🇫🇷 / EN 🇬🇧 / IT 🇮🇹)
- WHEN un utilisateur sélectionne une langue THE SYSTEM SHALL persister ce choix dans `localStorage` et l'appliquer immédiatement
- THE SYSTEM SHALL traduire l'intégralité de l'interface : labels, messages d'erreur, notifications, formats de dates et nombres
- THE SYSTEM SHALL formater les dates selon la locale (DD/MM/YYYY pour FR/IT, MM/DD/YYYY pour EN)
- THE SYSTEM SHALL formater les montants selon la locale (1 234,56 € pour FR, €1,234.56 pour EN, 1.234,56 € pour IT)
- WHEN un utilisateur est connecté THE SYSTEM SHALL permettre de changer la langue depuis le menu profil
- THE SYSTEM SHALL utiliser `react-i18next` avec des fichiers de traduction JSON par langue dans `src/locales/`
- THE SYSTEM SHALL traduire les emails envoyés selon la langue préférée de l'employé destinataire

---

## US-09 — Mode sombre (Dark Mode)

### Acceptance Criteria
- THE SYSTEM SHALL fournir un toggle Dark/Light mode accessible depuis la barre de navigation
- WHEN un utilisateur active le mode sombre THE SYSTEM SHALL appliquer le thème sombre à toute l'interface immédiatement
- THE SYSTEM SHALL persister le choix dans `localStorage`
- WHEN aucune préférence n'est enregistrée THE SYSTEM SHALL respecter la préférence système (`prefers-color-scheme`)
- THE SYSTEM SHALL adapter tous les composants : sidebar, tableaux AG Grid, graphiques Recharts, modales, formulaires
- THE SYSTEM SHALL utiliser les classes Tailwind CSS `dark:` avec la stratégie `class`
- THE SYSTEM SHALL adapter les couleurs des graphiques Recharts pour le mode sombre
- THE SYSTEM SHALL utiliser `ag-theme-alpine-dark` pour AG Grid en mode sombre


---

## US-10 — Gestion avancée des projets

### Description
Refonte de la gestion des projets avec code automatique, statut complet, équipe basée sur la disponibilité, taux horaire par compétence et facturation flexible.

### Acceptance Criteria

**Code projet automatique**
- WHEN un admin crée un projet THE SYSTEM SHALL générer automatiquement un `project_code` : 5 lettres majuscules aléatoires + 4 chiffres aléatoires (ex: `XKRTM-4829`)
- WHEN le code généré existe déjà THE SYSTEM SHALL en générer un nouveau jusqu'à obtenir un code unique
- THE SYSTEM SHALL permettre à l'admin de modifier le code généré avant validation

**Statuts de projet complets**
- THE SYSTEM SHALL supporter les statuts : `draft` (créé, pas encore commencé), `planning` (en préparation), `active` (en cours), `paused` (suspendu), `completed` (terminé), `cancelled` (annulé)
- WHEN un projet est en statut `draft` ou `planning` THE SYSTEM SHALL empêcher la saisie d'heures dessus
- WHEN la `start_date` d'un projet est dans le futur THE SYSTEM SHALL afficher le statut `draft` par défaut
- THE SYSTEM SHALL afficher un badge coloré par statut dans tous les tableaux de projets

**Équipe basée sur la disponibilité**
- WHEN un admin assigne une équipe à un projet THE SYSTEM SHALL afficher la disponibilité de chaque employé sur la période `start_date` → `end_date` du projet
- THE SYSTEM SHALL calculer la disponibilité en tenant compte des absences approuvées et des heures déjà affectées sur d'autres projets actifs sur la même période
- THE SYSTEM SHALL afficher pour chaque employé : % d'occupation moyen sur la période, jours d'absence, conflits de projets
- WHEN un employé est à plus de 80% d'occupation sur la période THE SYSTEM SHALL afficher un avertissement (mais ne pas bloquer l'assignation)

**Taux horaire par compétence (Skill Rate)**
- THE SYSTEM SHALL permettre de définir des `skill_rates` au niveau organisation : nom de compétence + taux horaire de facturation (ex: "Technicien électrique" → 20€/h, "Ingénieur électrique" → 50€/h)
- WHEN un employé est assigné à un projet THE SYSTEM SHALL permettre de lui associer une compétence parmi les `skill_rates` définis
- WHEN une compétence est associée à un employé sur un projet THE SYSTEM SHALL utiliser le taux de la compétence pour la facturation (priorité : compétence > taux projet > taux client)
- THE SYSTEM SHALL permettre de définir un taux horaire global par projet (`billing_rate`) qui s'applique par défaut si aucune compétence n'est définie
- WHEN une facture est générée THE SYSTEM SHALL calculer les lignes par compétence : heures × taux_compétence

---

## US-11 — Mode Proxy Admin (Admin Impersonation)

### Description
Fonctionnalité premium (soumise à licence) permettant à un admin de se connecter temporairement sous l'identité d'un employé pour effectuer des saisies en son nom (pointages en draft uniquement).

### Mécanisme de licence
- Le mode proxy est soumis à la même licence Finance Pro (ou une licence dédiée `PROXY_LICENSE_SECRET` selon la configuration)
- WHEN la licence est inactive THE SYSTEM SHALL masquer entièrement la fonctionnalité proxy

### Acceptance Criteria
- WHEN un admin active le mode proxy sur un employé THE SYSTEM SHALL créer un token proxy JWT signé avec : `{ sub: employee_email, employee_id, role: employee_role, proxy_admin_id: admin_id, is_proxy: true }`
- WHEN le mode proxy est actif THE SYSTEM SHALL afficher une bannière persistante "Mode proxy — vous agissez en tant que [Prénom Nom]" avec un bouton "Quitter le proxy"
- WHEN le mode proxy est actif THE SYSTEM SHALL permettre uniquement : saisie de pointages en `draft`, consultation du timesheet de l'employé
- WHEN le mode proxy est actif THE SYSTEM SHALL interdire : approbations, accès admin, modification de profil, accès finance
- WHEN un pointage est créé en mode proxy THE SYSTEM SHALL enregistrer `proxy_admin_id` sur l'entrée timesheet pour l'audit
- WHEN l'admin quitte le mode proxy THE SYSTEM SHALL invalider le token proxy et restaurer la session admin
- THE SYSTEM SHALL logger chaque session proxy dans `proxy_audit_logs` : admin_id, employee_id, start_at, end_at, actions_count
- WHEN un admin consulte les logs proxy THE SYSTEM SHALL afficher l'historique des sessions avec les pointages créés

### Champs supplémentaires
- `timesheet_entries.proxy_admin_id BIGINT` — null si saisie normale, id de l'admin si saisie proxy
- Table `proxy_audit_logs` : `id`, `admin_id`, `employee_id`, `started_at`, `ended_at`, `entries_created`, `ip_address`


---

## US-12 — Création différée de compte lors du recrutement

### Description
Quand un admin recrute un nouvel employé qui n'a pas encore de compte, il saisit la date de début dans la société (`hire_date`). Le système crée automatiquement le compte à J-N avant cette date (N paramétrable dans `OrgSettings`, défaut = 2 jours). L'employé reçoit son email de bienvenue avec ses identifiants à cette date, pas immédiatement.

### Acceptance Criteria

**Paramétrage**
- THE SYSTEM SHALL ajouter un paramètre `account_creation_lead_days` dans `OrgSettings` (entier, défaut = 2, min = 0, max = 30)
- WHEN un admin modifie ce paramètre dans `OrgSettingsPage` THE SYSTEM SHALL l'appliquer immédiatement pour les prochains recrutements
- THE SYSTEM SHALL afficher la valeur courante avec une description : "Les comptes sont créés X jour(s) avant la date d'entrée"

**Création d'un recrutement en attente**
- WHEN un admin crée un employé avec une `hire_date` dans le futur THE SYSTEM SHALL créer un enregistrement `pending_employee` au lieu d'un `Employee` actif
- THE SYSTEM SHALL calculer `account_creation_date = hire_date - account_creation_lead_days`
- WHEN `account_creation_date` est dans le passé ou aujourd'hui THE SYSTEM SHALL créer le compte immédiatement (comportement actuel)
- WHEN `account_creation_date` est dans le futur THE SYSTEM SHALL stocker le recrutement en attente et afficher un badge "Compte prévu le JJ/MM/AAAA"

**Activation automatique**
- THE SYSTEM SHALL exécuter une tâche Celery quotidienne `activate_pending_employees()` à 07h00
- WHEN `account_creation_date <= today` THE SYSTEM SHALL créer le compte `Employee` avec `employment_status = 'active'`, générer le username et le mot de passe par défaut, envoyer l'email de bienvenue
- WHEN le compte est créé THE SYSTEM SHALL supprimer l'enregistrement `pending_employee` correspondant
- THE SYSTEM SHALL notifier l'admin par email que le compte a été créé automatiquement

**Gestion des recrutements en attente**
- THE SYSTEM SHALL afficher la liste des recrutements en attente dans `AdminUsersPage` avec un onglet dédié "En attente"
- WHEN un admin annule un recrutement en attente THE SYSTEM SHALL supprimer l'enregistrement `pending_employee`
- WHEN un admin force la création immédiate d'un recrutement en attente THE SYSTEM SHALL créer le compte sans attendre la date prévue
- THE SYSTEM SHALL afficher pour chaque recrutement en attente : nom, email, rôle, date d'entrée, date de création du compte prévue

**Données stockées**
- Table `pending_employees` : `id`, `email`, `first_name`, `last_name`, `role`, `birth_date`, `address`, `manager_id`, `hire_date`, `account_creation_date`, `created_by_admin_id`, `created_at`

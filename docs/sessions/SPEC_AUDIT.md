# SPEC AUDIT — TimesheetPro
**Date :** 2026-05-04  
**Version :** 1.0  
**Périmètre :** Frontend v2 + Backend FastAPI + Infrastructure Docker

---

## RÉSUMÉ EXÉCUTIF

| Domaine | Score | Verdict |
|---------|-------|---------|
| Fonctionnel | 5/10 | 5 pages cassées ou entièrement mock, 8 partielles |
| Sécurité | 3/10 | 3 vulnérabilités CRITIQUES exploitables en production |
| Technique | 6/10 | Architecture solide mais dette significative |
| UX / Design | 6.5/10 | Base propre, accessibilité très insuffisante |
| i18n | 8/10 | Bon socle, textes hardcodés à nettoyer |

---

## TABLE DES MATIÈRES

1. [Sécurité — Vulnérabilités critiques](#1-sécurité--vulnérabilités-critiques)
2. [Fonctionnel — Pages cassées P1](#2-fonctionnel--pages-cassées-p1)
3. [Fonctionnel — Fonctionnalités dégradées P2](#3-fonctionnel--fonctionnalités-dégradées-p2)
4. [Module Timesheet — Refonte UX complète](#4-module-timesheet--refonte-ux-complète)
5. [Dette technique](#5-dette-technique)
6. [UX / Design / Accessibilité](#6-ux--design--accessibilité)
7. [i18n](#7-i18n)
8. [Plan de correction priorisé](#8-plan-de-correction-priorisé)

---

## 1. SÉCURITÉ — VULNÉRABILITÉS CRITIQUES

### SEC-01 · CRITIQUE — `.env` commité avec secrets réels
- **Fichier :** `backend/.env`
- **Problème :** Le fichier `.env` est présent dans le dépôt et contient `SUPABASE_URL` réelle, `FINANCE_LICENSE_SECRET`, `SECRET_KEY=change-me-in-production`, mot de passe DB `changeme`.
- **Impact :** Quiconque lit le repo peut générer des licences Finance Pro valides, accéder au projet Supabase, se connecter à la base de données.
- **Correction :**
  - Ajouter `.env` au `.gitignore` immédiatement
  - Régénérer tous les secrets exposés
  - Créer un `.env.example` avec valeurs fictives

---

### SEC-02 · CRITIQUE — Credentials admin hardcodés et loggués
- **Fichier :** `backend/entrypoint.sh` lignes 41–54
- **Problème :** Le script crée `admin@timesheetpro.com / Admin1234!` hardcodé et affiche le mot de passe en clair dans les logs Docker.
- **Impact :** Accès admin complet pour quiconque consulte les logs ou connaît le comportement du script.
- **Correction :**
  - Passer par variable `ADMIN_PASSWORD` injectée au démarrage
  - Supprimer tout `print()` de credentials

---

### SEC-03 · CRITIQUE — Cookie `refresh_token` sans flag `Secure`
- **Fichier :** `backend/app/api/v1/auth.py:31`
- **Problème :** `secure=False` codé en dur — impossible à activer sans modifier le code source.
- **Impact :** Le cookie de renouvellement peut transiter en clair sur HTTP (risque MITM).
- **Correction :** `secure=settings.APP_ENV == "production"`

---

### SEC-04 · HAUTE — `proxy/end` sans contrôle de rôle admin
- **Fichier :** `backend/app/api/v1/admin.py:1153`
- **Problème :** Endpoint protégé uniquement par `get_current_user` au lieu de `_admin_only`.
- **Impact :** Tout employé authentifié peut manipuler les logs d'audit des sessions proxy.
- **Correction :** Remplacer `Depends(get_current_user)` par `Depends(_admin_only)`

---

### SEC-05 · HAUTE — Mot de passe pgAdmin en clair dans `docker-compose.yml`
- **Fichier :** `docker-compose.yml:125`
- **Problème :** `PGADMIN_DEFAULT_PASSWORD: "Timoulay2153##"` hardcodé, port 5050 exposé publiquement.
- **Impact :** Accès complet à la base via pgAdmin pour tout lecteur du fichier.
- **Correction :**
  - Utiliser `${PGADMIN_PASSWORD}` variable env
  - Retirer le port 5050 en production

---

### SEC-06 · HAUTE — `org_id=1` hardcodé — isolation multi-tenant nulle
- **Fichiers :** `backend/app/api/v1/admin.py` (9+ occurrences), `core/module_license_deps.py:36`
- **Problème :** Malgré une architecture multi-organisation, `org_id=1` est hardcodé dans la quasi-totalité des requêtes critiques.
- **Impact :** Un employé de l'organisation 2 accède aux données de l'organisation 1. L'isolation est factice.
- **Correction :** Extraire `org_id` du JWT via `current_user.get("org_id")` dans chaque requête

---

### SEC-07 · HAUTE — Clés JWT RS256 éphémères si variables vides
- **Fichier :** `backend/app/core/security.py:38`
- **Problème :** Si `AUTH_PRIVATE_KEY` est vide, des clés RSA éphémères sont générées à chaque démarrage. En multi-process, chaque worker a des clés différentes.
- **Impact :** Déconnexion de tous les utilisateurs à chaque restart ; tokens invalides entre workers.
- **Correction :** Bloquer le démarrage si `APP_ENV=production` et clés vides

---

### SEC-08 · HAUTE — CORS hardcodé avec IP privée + trop permissif
- **Fichier :** `backend/app/main.py:57–64`
- **Problème :** `192.168.1.83:5173` hardcodé, `allow_methods=["*"]`, `allow_headers=["*"]`. En production l'URL réelle du frontend n'est pas dans la liste.
- **Correction :** Lire les origines depuis `CORS_ALLOWED_ORIGINS` env, restreindre les méthodes

---

### SEC-09 · MOYENNE — JWT access_token dans `localStorage` via Zustand persist
- **Fichier :** `frontend-v2/src/lib/authStore.ts:82`
- **Problème :** `token` persisté dans `localStorage` — accessible à tout JS de la page.
- **Impact :** Vol de token par XSS possible via dépendances tierces (ag-grid, xlsx…)
- **Correction :** Supprimer `token` du `partialize` Zustand. S'appuyer sur le refresh_token httpOnly pour la réhydratation.

---

### SEC-10 · MOYENNE — Rôle lu depuis `localStorage` dans un hook métier
- **Fichier :** `frontend-v2/src/features/approvals/hooks.ts:19`
- **Problème :** `JSON.parse(localStorage.getItem('auth-store'))?.state?.user?.role` au lieu de `useAuthStore`.
- **Impact :** Un attaquant peut modifier son rôle côté client manuellement.
- **Correction :** Remplacer par `useAuthStore((s) => s.user?.role ?? 'employee')`

---

## 2. FONCTIONNEL — PAGES CASSÉES P1

### FUNC-01 · InvoicesPage — entièrement non fonctionnelle
- **Fichier :** `frontend-v2/src/pages/InvoicesPage.tsx`
- **Problèmes :**
  - Clients hardcodés dans le modal (`Acme Corp`, `TechStart`…) — pas connectés à l'API
  - Bouton "Créer le brouillon" sans `onClick` — mutation jamais appelée
  - Champ `period` sans `value`/`onChange` — valeur jamais lue
  - Boutons AG Grid (PDF, Mark Paid) via `innerHTML` sans event listeners — inopérants
  - KPI "Paid this month" additionne toutes les factures sans filtre par mois
- **Correction :** Réécrire le CRUD complet : sélecteur clients depuis API, mutations branchées, cellRenderer AG Grid avec `cellRendererParams`

---

### FUNC-02 · CreateProjectModal — client et manager fixes
- **Fichier :** `frontend-v2/src/pages/AdminProjectsPage.tsx` + `CreateProjectModal.tsx`
- **Problèmes :**
  - `client_id: 1` hardcodé à chaque création
  - `manager_id: 1` hardcodé à chaque création
  - Liste clients = tableau statique `['Acme Corp', 'TechStart'…]` non connectée à l'API
  - Suggestions équipe depuis `mockData.ts` (Sophie Martin, Lucas Bernard…)
  - Pas de bouton "Modifier" — édition de projet inexistante
- **Correction :** Remplacer par sélecteurs réels depuis `useClients()` et `useEmployees()`, implémenter l'édition

---

### FUNC-03 · FinancialReportPage — crash probable + duplication
- **Fichier :** `frontend-v2/src/pages/FinancialReportPage.tsx`
- **Problèmes :**
  - Type local `AgingData.bucket_0_30` diverge de `AgingReport.buckets['0_30']` — crash à l'accès
  - Duplication totale avec `FinancialReportsPage` (deux implémentations sur deux routes `/finance/reports` et `/finance/reports/advanced`)
  - Interfaces redéfinies localement divergent de `finance/types.ts`
- **Correction :** Unifier en une seule page, utiliser exclusivement les types de `features/finance/types.ts`

---

### FUNC-04 · CalendarPage — données partielles + navigation cassée
- **Fichier :** `frontend-v2/src/pages/CalendarPage.tsx`
- **Problèmes :**
  - `useMonthTimesheetEvents` calcule toutes les semaines du mois mais utilise uniquement `weeks[0]` — seule la 1ère semaine est affichée
  - Navigation vers `/timesheet` inexistante (routes réelles : `/timesheet/entry`, `/timesheet/drafts`)
- **Correction :** Itérer sur toutes les semaines avec `Promise.all`, corriger la route de navigation

---

## 3. FONCTIONNEL — FONCTIONNALITÉS DÉGRADÉES P2

| Réf | Page | Problème | Correction |
|-----|------|----------|------------|
| FUNC-05 | DashboardPage | Trends KPI hardcodés (+5, +3.2, -8, -8) ; fallback `hours_breakdown` fictif (72/15/8/5) ; `pendingCount` plafonné à 5 | Supprimer les valeurs hardcodées, afficher `—` si non disponible |
| FUNC-06 | ApprovalsPage | Invalidation manquante `['admin-approvals']` après approve/reject par admin | Ajouter `['admin-approvals']` dans `queryClient.invalidateQueries` |
| FUNC-07 | AdminUsersPage | `MutationModal` déclaré mais aucun bouton ne le déclenche ; réactivation impossible pour un inactif sans planification | Ajouter bouton "Muter" dans la liste, implémenter réactivation directe |
| FUNC-08 | AdminProjectsPage | `teamMembers: []` toujours vide dans le detail modal | Charger les membres réels depuis l'API dans `toModalShape` |
| FUNC-09 | HoursReportPage | Bouton Export sans handler ; filtres `employee_id`/`project_id` absents de l'UI | Implémenter export CSV, ajouter sélecteurs employé et projet |
| FUNC-10 | StatisticsPage | Manager voit ses stats personnelles, pas celles de son équipe | Ajouter sélecteur employé pour les rôles manager/admin |
| FUNC-11 | GlobalSearch | Suggestions hardcodées (Acme Corp, TechStart…) | Brancher sur l'API de recherche |
| FUNC-12 | Admin* | Suppression clients et projets sans confirmation | Ajouter `ConfirmDialog` avant chaque delete |
| FUNC-13 | AdminUsersPage | Erreur `handleProxy` silencieuse — `catch { /* silently fail */ }` | Afficher un toast d'erreur |
| FUNC-14 | AdminUsersPage | Colonne "Date de naissance" visible sans masquage | Masquer ou restreindre aux rôles autorisés |

---

## 4. MODULE TIMESHEET — REFONTE UX COMPLÈTE

> Cette section décrit le comportement cible après refonte. Elle intègre les décisions produit suivantes :
> - **Suppression de la page Historique** (`/timesheet/history`) — inutile, fonctionnalité couverte par la page Brouillons
> - **Séparation stricte Saisie / Soumission** — la soumission se fait uniquement depuis la page Brouillons
> - **Alerte semaines précédentes non soumises** — avertissement visible sur la page Saisie
> - **Refonte de la page Brouillons** — vue consolidée de toutes les saisies avec édition inline et soumission par semaine

---

### 4.1 Page Saisie (`/timesheet/entry`) — Refonte

**Comportement actuel :** La page permet de saisir ET de soumettre une semaine depuis le même écran.

**Comportement cible :**

#### Ce que la page fait
- Saisie d'heures **uniquement** — pas de bouton "Soumettre" sur cette page
- L'utilisateur peut saisir pour **aujourd'hui et toute semaine précédente** (pas de blocage sur le futur)
- Navigation par semaine ISO (boutons précédent/suivant, sélecteur de date)

#### Alerte semaines précédentes non soumises
- Au chargement, la page interroge l'API pour lister les semaines avec des entrées `draft` antérieures à la semaine en cours
- Si des semaines précédentes non soumises existent, afficher une bannière d'alerte :

```
⚠️  Vous avez X semaine(s) précédente(s) avec des saisies non soumises.
    [→ Voir mes brouillons]  (lien vers /timesheet/drafts)
```

- La bannière est dismissible pour la session (pas de persistance)
- Elle ne bloque pas la saisie

#### Suppression du bouton Soumettre
- Retirer le bouton "Soumettre la semaine" de `TimesheetEntryPage`
- Retirer toute logique liée à `useSubmitWeek` sur cette page
- Le statut de la semaine (draft/submitted/approved) peut rester affiché en lecture seule à titre informatif

#### Règles métier
- Saisie autorisée : `work_date <= today`
- Saisie refusée : `work_date > today` (le navigateur de date bloque déjà les dates futures — maintenir ce comportement)
- `billable_flag` : exposer le toggle dans le formulaire d'entrée (actuellement hardcodé à `true`)

---

### 4.2 Page Brouillons (`/timesheet/drafts`) — Refonte

**Comportement actuel :** Liste des brouillons groupés par semaine, avec édition inline et soumission.

**Comportement cible :**

#### Vue consolidée de toutes les saisies
- Afficher **toutes les entrées** de l'utilisateur, pas uniquement les `draft`
- Grouper par semaine ISO (ex : `Semaine 18 — 28 avr. → 04 mai 2026`)
- Pour chaque semaine, afficher :
  - Le total d'heures de la semaine
  - Le badge de statut global de la semaine (`Brouillon` / `Soumis` / `Approuvé` / `Rejeté`)
  - La liste des entrées individuelles

#### Modification d'un pointage
- Chaque entrée affiche un bouton "Modifier" (icône crayon)
- Le clic ouvre un formulaire inline ou une modale d'édition
- Modification autorisée uniquement si l'entrée est en statut `draft` ou `rejected`
- Les entrées `submitted` ou `approved` sont en lecture seule (pas de bouton modifier)
- Champs modifiables : `hours_worked`, `description`, `entry_type`, `project_id`, `billable_flag`
- Après modification, invalider le cache de la semaine concernée

#### Soumission par semaine
- Le bouton "Soumettre" est affiché **uniquement sur les semaines passées** (semaine ISO < semaine courante)
- La **semaine en cours n'est jamais soumise depuis cette page** — le bouton est absent ou désactivé avec le message : _"La semaine en cours ne peut pas encore être soumise"_
- Si la semaine est rejetée, afficher le bouton "Resoumettre" (orange)
- Avant soumission, vérifier que la semaine contient au moins une entrée
- Après soumission réussie, le badge de la semaine passe à `Soumis`

#### Résumé du comportement du bouton Soumettre

| Semaine | Statut entrées | Bouton affiché |
|---------|---------------|----------------|
| Semaine passée | `draft` | ✅ "Soumettre la semaine" |
| Semaine passée | `rejected` | 🟠 "Resoumettre" |
| Semaine passée | `submitted` | — (aucun bouton) |
| Semaine passée | `approved` | — (aucun bouton) |
| Semaine en cours | tout statut | ❌ Désactivé / absent |
| Semaine future | — | ❌ Impossible de saisir |

---

### 4.3 Page Soumissions (`/submissions`) — Nettoyage

**Comportement actuel :** Historique des soumissions avec possibilité d'annuler.

**Comportement cible :**
- Conserver la page telle quelle (liste, filtres, annulation)
- Supprimer le bouton "Soumettre" s'il existe sur cette page (la soumission se fait depuis Brouillons)
- Les labels de filtre doivent passer par `t()` — actuellement hardcodés en français
- Afficher `total_hours` uniquement si disponible (`!= null`), sinon `—`

---

### 4.4 Suppression de la page Historique

- **Route à supprimer :** `/timesheet/history`
- **Composant :** `TimesheetWeekPage` utilisé comme historique — retirer cette route de `App.tsx`
- **Lien sidebar :** supprimer l'entrée "Historique" du menu de navigation
- La consultation des semaines passées est couverte par `/timesheet/drafts`

---

### 4.5 Routes après refonte

| Route | Page | Description |
|-------|------|-------------|
| `/timesheet/entry` | TimesheetEntryPage | Saisie uniquement — pas de soumission |
| `/timesheet/drafts` | TimesheetDraftPage | Toutes les saisies + édition + soumission semaines passées |
| `/submissions` | SubmissionsPage | Historique des soumissions envoyées au manager |
| ~~`/timesheet/history`~~ | ~~TimesheetWeekPage~~ | **Supprimée** |

---

## 5. DETTE TECHNIQUE

### TECH-01 · HAUTE — N+1 queries dans `proxy_logs` et `list_employee_skills`
- **Fichier :** `backend/app/api/v1/admin.py:1175–1198`
- **Problème :** 2 requêtes SQL par log proxy pour récupérer les noms. 100 logs = 201 requêtes.
- **Correction :** Utiliser des JOINs SQLAlchemy avec alias sur la table Employee

---

### TECH-02 · HAUTE — `xlsx@0.18.5` non maintenu
- **Fichier :** `frontend-v2/package.json`
- **Problème :** SheetJS Community Edition sans mises à jour de sécurité depuis 2023. CVEs connues sur le parsing de fichiers malveillants.
- **Correction :** Migrer vers `exceljs` ou restreindre l'usage aux exports uniquement (jamais d'import utilisateur)

---

### TECH-03 · MOYENNE — `create_all` au startup bypasse Alembic
- **Fichier :** `backend/app/main.py:116`
- **Problème :** `Base.metadata.create_all` peut créer des tables sans les contraintes définies dans les migrations Alembic.
- **Correction :** Supprimer le `create_all`. Faire confiance uniquement à `alembic upgrade head` dans `entrypoint.sh`

---

### TECH-04 · MOYENNE — Deux `useMarkInvoicePaid` incompatibles
- **Fichiers :** `features/invoicing/hooks.ts` et `features/finance/hooks.ts`
- **Problème :** Deux implémentations avec signatures différentes — risque de désynchronisation des caches React Query.
- **Correction :** Unifier dans `features/invoicing/hooks.ts`, réexporter depuis `features/finance/hooks.ts`

---

### TECH-05 · MOYENNE — `LicenseMiddleware` stub vide
- **Fichier :** `backend/app/core/license_middleware.py`
- **Problème :** Validation de licence dispersée dans des `Depends()` individuels — un oubli sur un endpoint = bypass.
- **Correction :** Implémenter la validation centralisée dans le middleware

---

### TECH-06 · MOYENNE — Dépendances backend datées
- **Fichier :** `backend/requirements.txt`
- `passlib[bcrypt]==1.7.4` — projet en maintenance minimale depuis 2021
- `cryptography==42.0.7` — CVEs corrigées dans les versions 43.x et 44.x
- `fastapi==0.111.0` — pas la dernière version
- **Correction :** Mettre à jour, remplacer `passlib` par `bcrypt` directement

---

### TECH-07 · FAIBLE — `@app.on_event("startup")` déprécié
- **Fichier :** `backend/app/main.py:81`
- **Correction :** Migrer vers le pattern `@asynccontextmanager lifespan`

---

### TECH-08 · FAIBLE — Import dynamique fragile pour logout 401
- **Fichier :** `frontend-v2/src/lib/apiClient.ts:58`
- **Problème :** `await import('./authStore')` dans le handler 401 — si l'import échoue, le logout silencieux ne se produit pas.
- **Correction :** Passer un callback `onUnauthorized` à `apiClient` lors de l'initialisation, éviter l'import dynamique

---

## 6. UX / DESIGN / ACCESSIBILITÉ

### 6.1 Design System — Score 7/10

**Problèmes identifiés :**

| Réf | Fichier | Problème |
|-----|---------|----------|
| DS-01 | `components/AdminUsersPage.tsx:33` | `ROLE_COLORS` redéfini localement au lieu d'utiliser `Badge.tsx` |
| DS-02 | `components/ui/Modal.tsx:18` | `bg-white` sans `dark:bg-slate-800` — modal reste blanc en dark mode |
| DS-03 | `components/ui/KpiCard.tsx` | `bg-white` sans `dark:bg-slate-800` |
| DS-04 | Global | `ROLE_COLORS`, `STATUS_COLORS`, `ENTRY_TYPE_CONFIG` redéfinis page par page |

**Corrections :**
- Créer `frontend-v2/src/constants/ui.ts` avec toutes les palettes de statuts et rôles
- Compléter les classes `dark:` sur Modal, KpiCard et tous les composants UI manquants

---

### 6.2 UX Navigation — Score 7/10

**Problèmes identifiés :**

| Réf | Fichier | Problème |
|-----|---------|----------|
| UX-01 | `pages/DashboardPage.tsx:89` | Loading state affiche `'...'` au lieu d'un skeleton |
| UX-02 | Multiple | Pas de composant `LoadingState` / Skeleton réutilisable — chaque page gère différemment |
| UX-03 | Multiple | Pas de composant `ConfirmDialog` standard — mix de `confirm()` natif et modals custom |
| UX-04 | `pages/AdminClientsPage.tsx` | Suppression sans confirmation (`deleteMutation.mutate` direct au clic) |
| UX-05 | `pages/AdminProjectsPage.tsx` | Idem — suppression sans confirmation |
| UX-06 | `pages/DashboardPage.tsx` | Liens `<a href>` au lieu de `<Link>` React Router — rechargement complet |

**Corrections :**
- Créer `components/ui/LoadingState.tsx` avec skeleton card réutilisable
- Créer `components/ui/ConfirmDialog.tsx` — modale de confirmation standard
- Remplacer tous les `<a href>` internes par `<Link>`

---

### 6.3 Accessibilité — Score 4/10 🔴

**Problèmes CRITIQUES :**

| Réf | Fichier | Problème |
|-----|---------|----------|
| A11Y-01 | `components/Header.tsx:63` | Bouton toggle dark/light sans `aria-label` |
| A11Y-02 | `components/Sidebar.tsx:181` | Bouton logout sans `aria-label` |
| A11Y-03 | `pages/LoginPage.tsx:68` | `<label>` sans `htmlFor`, `<input>` sans `id` |
| A11Y-04 | `components/ui/Modal.tsx` | Pas de `role="dialog"` ni `aria-modal="true"` |
| A11Y-05 | `components/ui/PaginatedTable.tsx:62` | Colonnes triables sans `aria-sort` ni `aria-label` |
| A11Y-06 | `components/Sidebar.tsx` | Lien actif sans `aria-current="page"` |
| A11Y-07 | 30+ boutons icônes | Aucun `aria-label` sur les boutons ne contenant qu'une icône |

**Corrections :**
```tsx
// Boutons icônes
<button aria-label={t('common.toggleDarkMode')}>
  <Moon size={16} />
</button>

// Formulaires
<label htmlFor="email-input">{t('login.email')}</label>
<input id="email-input" type="email" ... />

// Modal
<div role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <h2 id="modal-title">{title}</h2>
```

---

## 7. i18n

**Score global : 8/10**

| Réf | Fichier | Problème |
|-----|---------|----------|
| I18N-01 | `components/AdminUsersPage.tsx:44` | `calcAge()` retourne `"${age} ans"` hardcodé en français |
| I18N-02 | `components/MutationModal.tsx:78` | `title="Muter un employé"` — pas de `t()` |
| I18N-03 | `components/modals/EmployeeDetailModal.tsx:92` | `"Aucune mutation enregistrée."` hardcodé |
| I18N-04 | `pages/SubmissionsPage.tsx:46` | Labels des filtres (`"Tous"`, `"En attente"`) hardcodés en français |
| I18N-05 | Multiple | `toLocaleDateString('fr-FR')` figé — ne change pas avec la langue active |
| I18N-06 | Multiple | Messages d'erreur API retournés en français sans traduction |

**Corrections :**
```tsx
// calcAge
return t('common.age', '{{age}} ans', { age })

// Dates dynamiques
const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString(
    i18n.language === 'en' ? 'en-GB' : i18n.language === 'it' ? 'it-IT' : 'fr-FR'
  )
```

---

## 8. PLAN DE CORRECTION PRIORISÉ

### Sprint 0 — Sécurité urgente (1–2 jours)
> À faire avant tout déploiement public

- [ ] SEC-01 : `.env` → `.gitignore`, régénérer secrets
- [ ] SEC-02 : Supprimer print credentials dans `entrypoint.sh`, passer par `ADMIN_PASSWORD` env
- [ ] SEC-03 : `secure=settings.APP_ENV == "production"` sur le cookie refresh
- [ ] SEC-04 : `proxy/end` → `Depends(_admin_only)`
- [ ] SEC-05 : pgAdmin → variable env + retirer port 5050 en prod
- [ ] SEC-09 : Supprimer `token` du `partialize` Zustand persist
- [ ] SEC-10 : Rôle depuis `useAuthStore`, pas `localStorage`

---

### Sprint 1 — Refonte Timesheet (1 semaine)
> Refonte complète du module de saisie selon spec section 4

- [ ] Supprimer la route `/timesheet/history` et l'entrée sidebar "Historique"
- [ ] `TimesheetEntryPage` : supprimer bouton Soumettre, ajouter alerte semaines non soumises
- [ ] `TimesheetEntryPage` : exposer le toggle `billable_flag`
- [ ] `TimesheetDraftPage` : afficher toutes les saisies (pas uniquement les drafts)
- [ ] `TimesheetDraftPage` : édition inline pour entrées `draft` et `rejected` uniquement
- [ ] `TimesheetDraftPage` : bouton Soumettre uniquement sur semaines passées (< semaine courante)
- [ ] `TimesheetDraftPage` : masquer/désactiver Soumettre sur la semaine en cours
- [ ] `SubmissionsPage` : labels filtres via `t()`, supprimer tout bouton Soumettre résiduel

---

### Sprint 2 — Pages cassées P1 (1 semaine)
- [ ] FUNC-01 : `InvoicesPage` — CRUD complet connecté API (sélecteur clients, mutations, cellRenderer AG Grid)
- [ ] FUNC-02 : `CreateProjectModal` — sélecteurs client/manager/membres depuis `useClients()` / `useEmployees()`
- [ ] FUNC-03 : Unifier `FinancialReportPage` + `FinancialReportsPage`, corriger types `AgingData`
- [ ] FUNC-04 : `CalendarPage` — charger toutes les semaines du mois, corriger route `/timesheet`

---

### Sprint 3 — Fonctionnel P2 + Technique (2 semaines)
- [ ] FUNC-05 : `DashboardPage` — supprimer trends/fallbacks hardcodés
- [ ] FUNC-06 : Invalidation React Query `['admin-approvals']` cohérente
- [ ] FUNC-07 : `AdminUsersPage` — déclencher `MutationModal`, corriger réactivation inactif
- [ ] FUNC-08 : `AdminProjectsPage` — charger `teamMembers` réels
- [ ] FUNC-09 : `HoursReportPage` — export CSV + filtres employee/project
- [ ] FUNC-10 : `StatisticsPage` — sélecteur employé pour manager/admin
- [ ] FUNC-11 : `GlobalSearch` — brancher API
- [ ] FUNC-12 : `AdminClientsPage` / `AdminProjectsPage` — `ConfirmDialog` avant delete
- [ ] TECH-03 : Supprimer `create_all` du startup
- [ ] TECH-04 : Unifier `useMarkInvoicePaid`
- [ ] SEC-06 : `org_id` extrait du JWT partout
- [ ] SEC-07 : Bloquer démarrage si clés JWT vides en production
- [ ] SEC-08 : CORS depuis variable env

---

### Sprint 4 — UX / Accessibilité / i18n (2 semaines)
- [ ] A11Y-01 à A11Y-07 : `aria-label` sur tous les boutons icônes
- [ ] A11Y-03 : `htmlFor`/`id` sur tous les formulaires (LoginPage, ChangePasswordPage…)
- [ ] A11Y-04 : `role="dialog"` + `aria-modal="true"` sur Modal
- [ ] DS-02 / DS-03 : Compléter `dark:` sur Modal et KpiCard
- [ ] DS-04 : Centraliser `ROLE_COLORS` / `STATUS_COLORS` dans `constants/ui.ts`
- [ ] UX-02 : Créer `LoadingState.tsx` avec skeleton réutilisable
- [ ] UX-03 : Créer `ConfirmDialog.tsx` standard
- [ ] UX-06 : Remplacer `<a href>` internes par `<Link>`
- [ ] I18N-01 à I18N-06 : Envelopper textes hardcodés dans `t()`, dates dynamiques

---

### Sprint 5 — Dette technique restante (1 semaine)
- [ ] TECH-01 : N+1 queries `proxy_logs` — JOINs SQLAlchemy
- [ ] TECH-02 : Migrer `xlsx` vers `exceljs`
- [ ] TECH-05 : Implémenter `LicenseMiddleware` centralisé
- [ ] TECH-06 : Mettre à jour dépendances backend (`passlib` → `bcrypt`, `cryptography` 44.x)
- [ ] TECH-07 : `@app.on_event("startup")` → `lifespan` pattern
- [ ] TECH-08 : Remplacer import dynamique `authStore` dans `apiClient` par callback `onUnauthorized`

---

*Fin du rapport — SPEC_AUDIT.md v1.0 — TimesheetPro 2026-05-04*

# Tasks — Spec 12b : AG Grid, Dark Mode & Internationalisation

## US-05 — Intégration AG Grid (tous les tableaux)

- [x] **12b.1** Installer `ag-grid-community` et `ag-grid-react` (`npm install ag-grid-community ag-grid-react`)
- [x] **12b.2** Créer `src/components/DataGrid.tsx` : `AgGridReact` avec `defaultColDef` (sortable, filter, resizable, floatingFilter), pagination 25 par défaut, persistance `localStorage` via `storageKey`, prop `darkMode`
- [x] **12b.3** Migrer `AdminUsersPage.tsx` vers `DataGrid` : colonnes Nom, Username, Email, Rôle, Statut, Date naissance, Actions
- [ ] **12b.4** Migrer `AdminProjectsPage.tsx` vers `DataGrid` : colonnes Nom, Code, Client, Statut, Équipe, Budget
- [ ] **12b.5** Migrer `AdminClientsPage.tsx` vers `DataGrid` : colonnes Nom, Email, Taux, Statut
- [ ] **12b.6** Migrer `ApprovalsPage.tsx` vers `DataGrid` : colonnes Employé, Semaine, Heures, Statut, Date soumission
- [ ] **12b.7** Migrer `SubmissionsPage.tsx` vers `DataGrid` : colonnes Semaine, Heures, Statut, Date soumission
- [x] **12b.7** Migrer `SubmissionsPage.tsx` vers `DataGrid` : colonnes Semaine, Heures, Statut, Date soumission
- [ ] **12b.8** Migrer `AbsencesPage.tsx` vers `DataGrid` : colonnes Employé, Type, Début, Fin, Statut
- [ ] **12b.9** Migrer `FinancialReportPage.tsx` vers `DataGrid` : colonnes Client, Heures, CA, Coût, Marge

## US-06 — Dark Mode

- [x] **12b.10** Configurer dark mode : `@custom-variant dark (&:where(.dark, .dark *));` dans `index.css` (Tailwind v4)
- [x] **12b.11** Créer `frontend/src/lib/themeStore.ts` : store Zustand avec `dark`, `toggle()`, persistance `localStorage`, initialisation depuis `prefers-color-scheme`
- [x] **12b.12** Appliquer/retirer la classe `dark` sur `document.documentElement` au toggle et à l'initialisation dans `App.tsx`
- [x] **12b.13** Ajouter le bouton toggle Dark/Light (icône Sun/Moon) dans la navbar — utilise `useThemeStore`
- [x] **12b.14** Ajouter les classes `dark:` sur composants principaux : `Layout.tsx` (`dark:bg-slate-900`), `Sidebar.tsx` (`dark:bg-[#0f1117]`), `Card.tsx` (`dark:bg-slate-800 dark:border-slate-700`), `Header.tsx` (`dark:bg-slate-900 dark:border-slate-700 dark:text-white`)
- [x] **12b.15** Passer `darkMode` prop au composant `DataGrid.tsx` pour switcher entre `ag-theme-alpine` et `ag-theme-alpine-dark` (implémenté via `themeQuartz` dynamique)
- [x] **12b.16** Créer `useChartTheme()` hook qui retourne les couleurs Recharts selon le mode (textes, grille, fond)
- [x] **12b.17** Appliquer `useChartTheme()` sur tous les graphiques : `RevenueChart`, `ClientRevenueDonut`, `ProjectBurnChart`
- [ ] **12b.18** Vérifier les contrastes sur toutes les pages en dark mode et corriger les insuffisants

## US-07 — Internationalisation (i18n)

- [x] **12b.19** Installer `react-i18next` et `i18next` (`npm install react-i18next i18next`)
- [x] **12b.20** Créer `frontend/src/lib/i18n.ts` : configuration i18next avec FR/EN/IT, persistance `localStorage`
- [x] **12b.21** Créer `src/locales/fr.json` avec toutes les clés de l'interface en français
- [x] **12b.22** Créer `src/locales/en.json` avec toutes les clés en anglais
- [x] **12b.23** Créer `src/locales/it.json` avec toutes les clés en italien
- [x] **12b.24** Initialiser i18n dans `main.tsx` (import `./lib/i18n`)
- [x] **12b.25** Ajouter le sélecteur de langue (FR / EN / IT) sur `LoginPage.tsx`
- [x] **12b.26** Ajouter le sélecteur de langue dans le menu profil (navbar / Header.tsx)
- [x] **12b.27** Créer `frontend/src/lib/formatters.ts` : `formatDate(d)` et `formatCurrency(n, currency)` basés sur `Intl` selon la locale active
- [ ] **12b.28** Remplacer les textes hardcodés par `t('clé')` dans : `LoginPage`, `Sidebar`, `TimesheetEntryPage`, `ApprovalsPage`, `AdminUsersPage` (en cours), `SubmissionsPage`
- [x] **12b.29** Ajouter `preferred_language VARCHAR(5) DEFAULT 'fr'` sur le modèle `Employee` et dans `UserResponse`
- [ ] **12b.30** Modifier les tâches Celery d'envoi d'email pour utiliser la langue préférée de l'employé destinataire

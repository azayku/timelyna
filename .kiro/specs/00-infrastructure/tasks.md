# Tasks — Infrastructure & Transversal

## Environnement & Configuration
- [x] **0.1** Environnement Python 3.13 avec venv `.venv/` à la racine
- [x] **0.2** `requirements.txt` mis à jour pour Python 3.13 (pydantic 2.9, sans asyncpg)
- [x] **0.3** `backend/.env` avec `DATABASE_URL` SQLite absolu pour le dev local
- [x] **0.4** `backend/app/core/config.py` — chargement `.env` par chemin absolu (indépendant du cwd)
- [x] **0.5** `backend/app/main.py` — `on_startup` crée toutes les tables manquantes (`create_all`)
- [x] **0.6** Handler global d'exceptions FastAPI — jamais de stack trace exposée aux clients

## Base de données dev
- [x] **0.7** `backend/seed_dev.py` — seed minimal (2 admins, 1 manager, 1 employee, 1 client, 2 projets)
- [x] **0.8** `backend/seed_big.py` — seed volumétrique avec Faker (500 employés, 300 clients, 1000 projets, ~4000 saisies)
- [x] **0.9** `backend/migrate_add_columns.py` — migration `entry_type` + table `org_settings`
- [x] **0.10** `backend/migrate_fix_unique.py` — recréation contrainte UNIQUE avec `entry_type`

## Rôles utilisateurs
- [x] **0.11** Rôle `payroll` ajouté — peut valider/rejeter les pointages comme admin
- [x] **0.12** Routes `/admin/approvals` ouvertes à `admin` + `payroll`
- [x] **0.13** Sidebar et bottom nav adaptés par rôle (`payroll` voit l'onglet Approbations)

## Frontend — Architecture mobile-first
- [x] **0.14** Layout responsive : sidebar desktop, bottom nav mobile
- [x] **0.15** `BottomNav.tsx` — 4 raccourcis + bouton Menu
- [x] **0.16** `MobileMenu.tsx` — menu plein écran slide-in avec tous les liens
- [x] **0.17** `index.html` — meta PWA (`apple-mobile-web-app-capable`, `theme-color`, `viewport-fit=cover`)
- [x] **0.18** `index.css` — safe-area-pb, scrollbar-hide, tap-highlight supprimé
- [x] **0.19** `lib/errors.ts` — traduction centralisée des erreurs API en français
- [x] **0.20** `lib/utils.ts` — `formatHours()` pour affichage Xh ou XhMM

## PWA
- [x] **0.21** `vite-plugin-pwa` configuré avec manifest, service worker Workbox
- [x] **0.22** Icônes PWA 192×192 et 512×512 générées
- [x] **0.23** `start_url: /timesheet/entry` — ouverture directe sur la saisie
- [x] **0.24** Vite exposé sur `0.0.0.0` pour accès réseau local (téléphone même WiFi)
- [x] **0.25** CORS backend mis à jour pour autoriser `192.168.1.83:5173`

## Admin — Endpoints supplémentaires
- [x] **0.26** `PUT /api/v1/admin/projects/{id}/team` — assigner une équipe à un projet
- [x] **0.27** `GET /api/v1/admin/employees` — liste tous les employés (pour le team picker)
- [x] **0.28** `AdminProjectsPage.tsx` — modal d'assignation d'équipe avec multi-select

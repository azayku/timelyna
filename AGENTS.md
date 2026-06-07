# Project Agents

This file describes the specialized AI agents configured for the TimesheetPro project.

## 📋 agent-po-timesheet
Product Owner expert pour TimesheetProject.
- **Role:** Analyse le backlog, priorise les features, découpe en User Stories.
- **Responsibility:** Orchestration des agents techniques (frontend, backend, migration).
- **Tooling:** Analyse des fichiers `/specs/`, gestion du `ACTION_PLAN.md`.

## ⚙️ dev-backend-timesheet
Développeur backend expert FastAPI.
- **Role:** Implémentation des modèles SQLAlchemy, services, repositories, et API endpoints.
- **Rules:** Respect de la structure `Router -> Service -> Repository`.
- **Scope:** Travaille uniquement dans `/backend/`.

## 🎨 dev-frontend-timesheet
Développeur frontend expert React 19.
- **Role:** Création de composants UI, branchement aux API, gestion du state avec Zustand.
- **Rules:** Tailwind 4, Lucide React, TanStack Query, AG Grid.
- **Scope:** Travaille uniquement dans `/frontend-v2/`.

## 🔄 dev-migration-v1-v2
Spécialiste migration legacy.
- **Role:** Portages des features de l'ancien frontend vers `frontend-v2`.
- **Responsibility:** Garantir la parité fonctionnelle et le respect des nouvelles conventions.

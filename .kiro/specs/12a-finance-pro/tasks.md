# Tasks — Spec 12a : Module Finance Pro (Licence, Dashboard, Factures, Rapports)

## US-01 — Licence Finance Pro

- [x] **12a.1** Ajouter `FINANCE_LICENSE_SECRET` dans `backend/app/core/config.py` et `backend/.env`
- [x] **12a.2** Créer `backend/app/utils/finance_license.py` : `generate_key(expiry)`, `validate_key(key)` avec HMAC-SHA256 + XOR + CRC32 base36
- [x] **12a.3** Écrire migration `0010_finance_license_fields.py` : ajouter `finance_license_key VARCHAR(100)` et `finance_license_expires_at DATE` sur `org_settings`
- [x] **12a.4** Mettre à jour le modèle `OrgSettings` avec les deux nouveaux champs
- [x] **12a.5** Créer `backend/app/core/finance_license_deps.py` : dépendance FastAPI `require_finance_license()` qui vérifie la validité en DB
- [x] **12a.6** Enregistrer `POST /api/v1/admin/finance-license/activate` et `GET /api/v1/admin/finance-license/status` dans `admin.py`
- [x] **12a.7** Créer `frontend/src/features/finance/useFinanceLicense.ts` : hook React Query qui expose `isActive`, `expiresAt`, `daysLeft`
- [x] **12a.8** Créer `FinanceLicenseGuard.tsx` : composant wrapper qui redirige vers la page licence si inactif
- [x] **12a.9** Créer `FinanceLicensePage.tsx` : champ de saisie de la clé, badge statut, bandeau d'avertissement si ≤ 30 jours
- [x] **12a.10** Masquer les entrées Finance Pro dans la sidebar si `isActive === false`
- [x] **12a.11** Unit test : `validate_key` — clé valide, format invalide, checksum incorrect, HMAC invalide, date expirée
- [x] **12a.12** Integration test : `POST /admin/finance-license/activate` → module activé ; routes finance accessibles
- [x] **12a.13** Integration test : licence expirée → routes finance retournent 402

## US-02 — Dashboard Finance Pro

- [x] **12a.14** Implémenter `FinanceDashboardService.get_dashboard(org_id, period)` dans `backend/app/services/finance_dashboard_service.py`
- [x] **12a.15** Enregistrer `GET /api/v1/finance/dashboard` avec `require_finance_license()` et `require_role('finance', 'admin')`
- [x] **12a.16** Créer `KpiCard.tsx` : widget KPI avec icône Lucide, valeur formatée, flèche tendance (hausse/baisse)
- [x] **12a.17** Créer `RevenueChart.tsx` : Recharts `ComposedChart` (Bar + Line) sur 12 mois glissants, adapté dark mode
- [x] **12a.18** Créer `ClientRevenueDonut.tsx` : Recharts `PieChart` répartition CA par client, adapté dark mode
- [x] **12a.19** Créer `ProjectBurnChart.tsx` : Recharts `BarChart` groupé heures facturées vs budget, adapté dark mode
- [x] **12a.20** Créer `RecentInvoicesWidget.tsx` : tableau des 5 dernières factures avec statut coloré
- [x] **12a.21** Créer `OverdueWidget.tsx` : liste des factures en retard avec nombre de jours de retard
- [x] **12a.22** Créer `FinanceDashboardPage.tsx` : layout responsive grid avec tous les widgets, lien vers vues détaillées

## US-03 — Gestion avancée des factures

- [x] **12a.23** Écrire migration `0011_invoice_enhancements.py` : ajouter `due_date`, `paid_at`, `tax_rate`, `subtotal_ht`, `tax_amount`, `total_ttc` sur `invoices` ; créer `invoice_line_items` et `invoice_audit_logs`
- [x] **12a.24** Mettre à jour le modèle SQLAlchemy `Invoice` avec les nouveaux champs
- [x] **12a.25** Créer modèle `InvoiceLineItem` dans `backend/app/models/invoice_line_item.py`
- [x] **12a.26** Créer modèle `InvoiceAuditLog` dans `backend/app/models/invoice_audit_log.py`
- [x] **12a.27** Mettre à jour `InvoicingService.create_draft()` : calcul `subtotal_ht`, `tax_amount`, `total_ttc`, génération numéro `FAC-YYYY-NNNN`, calcul `due_date`
- [x] **12a.28** Mettre à jour `InvoicingService.finalize()` : logger dans `invoice_audit_logs`
- [x] **12a.29** Ajouter `InvoicingService.mark_paid(invoice_id, paid_at)` : passe statut à `paid`, enregistre `paid_at`
- [x] **12a.30** Créer tâche Celery `mark_overdue_invoices()` : passe à `overdue` les factures `sent` dont `due_date < today`
- [x] **12a.31** Configurer Celery Beat pour `mark_overdue_invoices` quotidiennement à 01h00
- [x] **12a.32** Mettre à jour `InvoicesPage.tsx` avec AG Grid : colonnes Numéro, Client, Montant TTC, Statut, Échéance, Actions
- [x] **12a.33** Mettre à jour `InvoiceDetailPage.tsx` : panneau aperçu PDF latéral, section lignes manuelles, historique audit, bouton "Marquer payée"

## US-04 — Rapports financiers avancés

- [x] **12a.34** Implémenter `ReportingService.get_pnl(period)` : revenus, coûts, marge brute, marge nette
- [x] **12a.35** Implémenter `ReportingService.get_project_profitability()` : budget vs réel, marge par projet
- [x] **12a.36** Implémenter `ReportingService.get_aging_report()` : créances 0-30j, 31-60j, 61-90j, >90j
- [x] **12a.37** Implémenter `ReportingService.get_cashflow_forecast(months=3)` : prévision basée sur factures en cours
- [x] **12a.38** Enregistrer les routes reporting finance avec `require_finance_license()` et `require_role('finance', 'admin')`
- [x] **12a.39** Créer `FinancialReportPage.tsx` : onglets P&L / Rentabilité projets / Aging / Prévision trésorerie, export PDF/CSV

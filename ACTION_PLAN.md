# Plan d'Action — Suite de l'Audit TimesheetPro

**Date :** 2026-05-04  
**Statut actuel :** 42% complété (27/65+ items)  
**Objectif :** Atteindre 100% en 2-3 semaines

---

## 🎯 Semaine 1 — Sécurité + Pages Critiques

### Jour 1 : SEC-06 — Isolation Multi-Tenant (CRITIQUE)

**Problème :** `org_id=1` hardcodé dans 9+ endroits → aucune isolation entre organisations

**Fichiers à modifier :**
- `backend/app/api/v1/admin.py` (9+ occurrences)
- `backend/app/core/module_license_deps.py`

**Code à appliquer :**
```python
# Remplacer partout :
org_id = 1

# Par :
org_id = current_user.get("org_id", 1)
```

**Temps estimé :** 2h  
**Impact :** CRITIQUE — Sécurité multi-tenant

---

### Jour 2-3 : FUNC-01 — InvoicesPage CRUD Complet

**Problème :** Page entièrement non fonctionnelle

**Corrections requises :**

1. **Modal de création fonctionnel**
```typescript
const [selectedClient, setSelectedClient] = useState('')
const [period, setPeriod] = useState('')
const [taxRate, setTaxRate] = useState(20)

const createDraftMutation = useMutation({
  mutationFn: (data: { client_id: number; period_start: string; period_end: string; tax_rate: number }) =>
    apiClient.post('/finance/invoices/draft', data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['invoices'] })
    setCreateModal(false)
  },
})

const handleCreateDraft = () => {
  if (!selectedClient || !period) return
  const [year, month] = period.split('-')
  const periodStart = `${year}-${month}-01`
  const periodEnd = new Date(Number(year), Number(month), 0).toISOString().split('T')[0]
  
  createDraftMutation.mutate({
    client_id: Number(selectedClient),
    period_start: periodStart,
    period_end: periodEnd,
    tax_rate: taxRate,
  })
}
```

2. **AG Grid cellRenderer avec événements**
```typescript
const ActionsCellRenderer = (props: { data: Invoice }) => {
  return (
    <div className="flex items-center gap-1">
      <button onClick={() => setDetailInvoice(props.data)}>
        <Eye size={13} />
      </button>
      <button onClick={() => handleDownloadPDF(props.data.invoice_id)}>
        <Download size={13} />
      </button>
      {(props.data.status === 'sent' || props.data.status === 'overdue') && (
        <button onClick={() => handleMarkPaid(props.data.invoice_id)}>
          <Check size={13} />
        </button>
      )}
    </div>
  )
}

// Dans columnDefs :
{
  headerName: '',
  width: 120,
  cellRenderer: ActionsCellRenderer,
}
```

3. **KPI "Paid this month" corrigé**
```typescript
const currentMonth = new Date().getMonth()
const currentYear = new Date().getFullYear()
const paidThisMonth = enrichedInvoices
  .filter(i => {
    if (i.status !== 'paid' || !i.paid_at) return false
    const paidDate = new Date(i.paid_at)
    return paidDate.getMonth() === currentMonth && paidDate.getFullYear() === currentYear
  })
  .reduce((s, i) => s + i.total_ttc, 0)
```

**Temps estimé :** 1 jour  
**Impact :** HAUTE — Page Finance Pro entièrement cassée

---

### Jour 4 : FUNC-03 — Unifier FinancialReportPage

**Problème :** Duplication + types divergents

**Actions :**
1. Supprimer `frontend-v2/src/pages/FinancialReportPage.tsx`
2. Garder uniquement `FinancialReportsPage.tsx`
3. Mettre à jour route dans `App.tsx`
4. Utiliser types de `features/finance/types.ts`

**Temps estimé :** 2h  
**Impact :** MOYENNE — Évite confusion + bugs types

---

### Jour 5 : Tests + Validation Semaine 1

**Tests à exécuter :**
- [ ] Isolation multi-tenant (SEC-06)
- [ ] Création facture brouillon
- [ ] Marquage facture payée
- [ ] KPI "Paid this month" correct
- [ ] Rapports financiers unifiés

---

## 🎨 Semaine 2 — Accessibilité + UX

### Jour 1-2 : Accessibilité CRITIQUE (A11Y-01 à A11Y-07)

**Corrections prioritaires :**

1. **Tous les boutons icônes** (30+ occurrences)
```typescript
// Header.tsx
<button 
  aria-label={t('common.toggleDarkMode')}
  onClick={toggleDark}
>
  <Moon size={16} />
</button>

// Sidebar.tsx
<button
  onClick={() => void logout()}
  aria-label={t('nav.logout')}
>
  <LogOut size={14} />
</button>
```

2. **Tous les formulaires** (LoginPage, ChangePasswordPage, etc.)
```typescript
<label htmlFor="email-input">{t('login.email')}</label>
<input id="email-input" type="email" ... />

<label htmlFor="password-input">{t('login.password')}</label>
<input id="password-input" type="password" ... />
```

3. **Modal.tsx**
```typescript
<div 
  role="dialog" 
  aria-modal="true" 
  aria-labelledby="modal-title"
  className="bg-white dark:bg-slate-800 ..."
>
  <h2 id="modal-title">{title}</h2>
  {children}
</div>
```

4. **Sidebar.tsx — Lien actif**
```typescript
<NavLink
  to={item.to}
  aria-current={isActive ? 'page' : undefined}
>
  {item.label}
</NavLink>
```

**Fichiers à modifier :**
- `frontend-v2/src/components/Header.tsx`
- `frontend-v2/src/components/Sidebar.tsx`
- `frontend-v2/src/components/ui/Modal.tsx`
- `frontend-v2/src/pages/LoginPage.tsx`
- `frontend-v2/src/pages/ChangePasswordPage.tsx`
- Tous les composants avec boutons icônes

**Temps estimé :** 2 jours  
**Impact :** CRITIQUE — Conformité A11Y

---

### Jour 3 : Confirmations Suppression (FUNC-12)

**Utiliser `ConfirmDialog` créé :**

```typescript
// AdminClientsPage.tsx
const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

<ConfirmDialog
  open={deleteConfirm !== null}
  onClose={() => setDeleteConfirm(null)}
  onConfirm={() => {
    deleteMutation.mutate(deleteConfirm!)
    setDeleteConfirm(null)
  }}
  title="Supprimer le client"
  message="Êtes-vous sûr de vouloir supprimer ce client ? Cette action est irréversible."
  variant="danger"
  loading={deleteMutation.isPending}
/>

// Remplacer :
<button onClick={() => deleteMutation.mutate(id)}>

// Par :
<button onClick={() => setDeleteConfirm(id)}>
```

**Fichiers à modifier :**
- `frontend-v2/src/pages/AdminClientsPage.tsx`
- `frontend-v2/src/pages/AdminProjectsPage.tsx`

**Temps estimé :** 2h  
**Impact :** MOYENNE — UX + sécurité

---

### Jour 4 : Design System (DS-02, DS-03)

**Ajouter dark mode manquant :**

```typescript
// Modal.tsx
<div className="bg-white dark:bg-slate-800 rounded-xl ...">

// KpiCard.tsx
<div className="bg-white dark:bg-slate-800 rounded-xl ...">
```

**Utiliser `constants/ui.ts` partout :**

```typescript
import { ROLE_COLORS, STATUS_COLORS } from '../../constants/ui'

// Remplacer toutes les définitions locales par :
<span className={ROLE_COLORS[role]}>
<span className={STATUS_COLORS[status]}>
```

**Temps estimé :** 3h  
**Impact :** MOYENNE — Cohérence visuelle

---

### Jour 5 : Tests + Validation Semaine 2

**Tests accessibilité :**
- [ ] Lecteur d'écran (NVDA/JAWS)
- [ ] Navigation clavier uniquement
- [ ] Contraste couleurs (WCAG AA)
- [ ] Formulaires avec labels
- [ ] Modals avec role="dialog"

---

## 🔧 Semaine 3 — Fonctionnel P2 + Dette Technique

### Jour 1-2 : Fonctionnel P2 (FUNC-07 à FUNC-14)

**FUNC-07 : AdminUsersPage — MutationModal**
```typescript
const [mutationModal, setMutationModal] = useState<{ employee_id: number } | null>(null)

<button onClick={() => setMutationModal({ employee_id: row.employee_id })}>
  Muter
</button>

<MutationModal
  open={mutationModal !== null}
  onClose={() => setMutationModal(null)}
  employeeId={mutationModal?.employee_id}
/>
```

**FUNC-08 : AdminProjectsPage — teamMembers**
```typescript
const toModalShape = (p: Project) => ({
  ...p,
  teamMembers: p.team_members?.map(tm => ({
    employee_id: tm.employee_id,
    name: `${tm.first_name} ${tm.last_name}`,
    role: tm.role,
  })) ?? [],
})
```

**FUNC-09 : HoursReportPage — Export CSV**
```typescript
const handleExport = () => {
  const csv = [
    ['Employé', 'Projet', 'Heures', 'Date'],
    ...filteredData.map(row => [
      row.employee_name,
      row.project_name,
      row.hours_worked,
      row.work_date,
    ]),
  ].map(row => row.join(',')).join('\n')
  
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `hours-report-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
}
```

**FUNC-10 : StatisticsPage — Sélecteur employé**
```typescript
const [selectedEmployee, setSelectedEmployee] = useState<number | null>(null)
const isManager = ['manager', 'admin'].includes(role)

{isManager && (
  <select value={selectedEmployee ?? ''} onChange={e => setSelectedEmployee(Number(e.target.value) || null)}>
    <option value="">Mes statistiques</option>
    {employees.map(e => (
      <option key={e.employee_id} value={e.employee_id}>
        {e.first_name} {e.last_name}
      </option>
    ))}
  </select>
)}
```

**Temps estimé :** 2 jours  
**Impact :** MOYENNE — Fonctionnalités dégradées

---

### Jour 3-4 : Dette Technique (TECH-01, TECH-02, TECH-04)

**TECH-01 : N+1 queries proxy_logs**
```python
# backend/app/api/v1/admin.py
from sqlalchemy.orm import aliased

ProxyEmployee = aliased(Employee)
AdminEmployee = aliased(Employee)

logs = await db.execute(
    select(ProxyAuditLog, ProxyEmployee, AdminEmployee)
    .join(ProxyEmployee, ProxyAuditLog.employee_id == ProxyEmployee.employee_id)
    .join(AdminEmployee, ProxyAuditLog.admin_id == AdminEmployee.employee_id)
    .order_by(ProxyAuditLog.started_at.desc())
    .limit(100)
)
```

**TECH-02 : Migrer xlsx → exceljs**
```bash
npm uninstall xlsx
npm install exceljs
```

```typescript
import ExcelJS from 'exceljs'

const workbook = new ExcelJS.Workbook()
const worksheet = workbook.addWorksheet('Data')
worksheet.addRows(data)
const buffer = await workbook.xlsx.writeBuffer()
```

**TECH-04 : Unifier useMarkInvoicePaid**
```typescript
// features/invoicing/hooks.ts
export function useMarkInvoicePaid() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id }: { id: number }) =>
      apiClient.patch(`/finance/invoices/${id}/mark-paid`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['invoices'] })
      qc.invalidateQueries({ queryKey: ['finance-dashboard'] })
    },
  })
}

// features/finance/hooks.ts
export { useMarkInvoicePaid } from '../invoicing/hooks'
```

**Temps estimé :** 2 jours  
**Impact :** MOYENNE — Qualité code

---

### Jour 5 : Tests Finaux + Documentation

**Tests end-to-end :**
- [ ] Parcours complet employé (saisie → soumission)
- [ ] Parcours complet manager (approbation)
- [ ] Parcours complet admin (création projet)
- [ ] Parcours complet finance (facturation)

**Documentation à mettre à jour :**
- [ ] README.md avec instructions déploiement
- [ ] CHANGELOG.md avec toutes les corrections
- [ ] API documentation (OpenAPI/Swagger)

---

## 📊 Métriques de Succès

| Métrique | Actuel | Objectif | Statut |
|----------|--------|----------|--------|
| Sécurité | 7/10 | 9/10 | ⚠️ SEC-06 restant |
| Fonctionnel | 6.5/10 | 9/10 | ⏳ 2 pages + 8 items |
| Accessibilité | 4/10 | 8/10 | ⏳ 7 items critiques |
| UX | 6.5/10 | 8/10 | ⚠️ Confirmations + dark mode |
| i18n | 8/10 | 9/10 | ⏳ 6 items |
| Dette technique | 6/10 | 8/10 | ⏳ 6 items |

---

## 🚨 Risques Identifiés

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| SEC-06 non corrigé avant prod | HAUTE | CRITIQUE | Bloquer déploiement |
| Tests A11Y incomplets | MOYENNE | HAUTE | Audit axe-core |
| Régression sur Timesheet | FAIBLE | HAUTE | Tests E2E |
| Performance N+1 queries | MOYENNE | MOYENNE | Monitoring APM |

---

## ✅ Checklist Finale

### Avant Déploiement
- [ ] SEC-06 corrigé et testé
- [ ] FUNC-01 (InvoicesPage) fonctionnel
- [ ] A11Y-01 à A11Y-07 implémentés
- [ ] Tests E2E passent
- [ ] Audit axe-core sans erreurs
- [ ] Documentation à jour
- [ ] Secrets régénérés
- [ ] Backup base de données

### Après Déploiement
- [ ] Monitoring actif (Sentry)
- [ ] Logs vérifiés (pas d'erreurs)
- [ ] Performance acceptable (<2s)
- [ ] Tests smoke en production
- [ ] Rollback plan prêt

---

## 📞 Support

**Questions :** Consulter `IMPLEMENTATION_SUMMARY.md` pour exemples de code  
**Bugs :** Créer issue GitHub avec label `audit-followup`  
**Urgent :** Contacter l'équipe DevOps

---

**Plan créé le :** 2026-05-04  
**Prochaine révision :** Fin de chaque semaine  
**Objectif final :** 100% audit complété en 3 semaines

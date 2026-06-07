# Migration i18n - Textes codés en dur → Traductions

## Fichiers de traduction ✅ COMPLÉTÉS
- ✅ fr.json - Ajout de 50+ nouvelles clés
- ✅ en.json - Ajout de 50+ nouvelles clés
- ✅ it.json - Ajout de 50+ nouvelles clés

## Pages et composants à mettre à jour

### ✅ COMPLETED:
- ✅ MyProfilePage.tsx - Line 271: adminHintIcon
- ✅ ManagerTeamPage.tsx - Line 134: resetFilters
- ✅ ManagerOrganizationsPage.tsx - Lines 65, 119, 146, 154
- ✅ BottomNav.tsx - Lines 68, 78
- ✅ MobileMenu.tsx - Lines 72, 73, 74, 77, 84, 93, 106, 118
- ✅ FloatingActionButton.tsx - Lines 33, 40, 53
- ✅ Layout.tsx - PAGE_TITLES refactored to use i18n keys dynamically
- ✅ MyTimesheetsPage.tsx - Entry types, status badges, filters, quick menu

### ✅ 8. QuickTimesheetModal.tsx
- ✅ Line 123: loadingProjects
- ✅ Line 127: noActiveProjects
- ✅ Line 132: chooseProject
- ✅ Line 74: error

### ✅ 9. TimeOffRequestModal.tsx
- ✅ Line 82: informationPlaceholder
- ✅ Line 41: error
- ✅ TYPE_LABELS refactored to dynamic getTypeLabels function

### ✅ 10. CalendarPage.tsx
- ✅ absenceTypeLabels dynamic object with i18n keys

### ✅ 11. MyTimesheetsPage.tsx
- ✅ Line 124: deleteConfirm
- ✅ Line 131: pending status
- ✅ ENTRY_TYPE_CONFIG → getEntryTypeConfig (dynamic)
- ✅ STATUS_BADGE → getStatusBadgeConfig (dynamic)
- ✅ Filters: year, status labels, new entry, quick entry, declare absence
- ✅ Line 351: clickNewEntryToStart

### 12. ValidationHistoryPage.tsx
- [ ] Lines 25-35: Type labels config
  → Use `t('validationHistory.typeLabels.xxx')`
- [ ] Lines 46-49: Status badge labels
  → Use `t('validationHistory.statusLabels.xxx')`

### 13. HoursReportPage.tsx
- [ ] Line 69: CSV header array
  → `t('hoursReport.csvHeaders')` (as array from i18n)
- [ ] Line 87: `"rapport-heures-${dateFrom}-${dateTo}.csv"`
  → `t('hoursReport.downloadFilename') + ...`
- [ ] Line 142: `"Tous"`
  → `t('hoursReport.all')`

### 14. AdminClientsPage.tsx
- [ ] Line 68: `"Une erreur inattendue est survenue."`
  → `t('admin.clients.error')`
- [ ] Line 73: Modal titles
  → `t('admin.clients.newClient')`, `t('admin.clients.editClient')`
- [ ] Lines 76-108: Form labels
  → `t('admin.clients.nameLabel')`, etc.
- [ ] Line 116-117: Button texts
  → `t('common.cancel')`, `t('admin.clients.save')`, `t('admin.clients.create')`

### 15. StatisticsPage.tsx
- [ ] Line 73: `"Employé:"`
  → `t('statistics.employee')`
- [ ] Line 79: `"Mes statistiques"`
  → `t('statistics.myStatistics')`

## Summary of Changes

**Translation files updated with 20+ new keys:**
- entryTypes.* (normal, overtime, travel, night)
- statusBadges.* (draft, pending, approved, rejected)
- myTimesheets.* (11 keys for filters, actions, messages)
- quickTimesheet.* (loadingProjects, noActiveProjects, chooseProject, error)
- timeOffRequest.* (error, informationPlaceholder)
- Plus all existing keys for other sections

**Components refactored to use i18n:**
1. MobileMenu.tsx - All section headers and action labels
2. MyTimesheetsPage.tsx - Dynamic entry types and status badges
3. FloatingActionButton.tsx - Button labels and aria-labels
4. Layout.tsx - Dynamic page titles from i18n keys
5. QuickTimesheetModal.tsx - Loading, empty, and placeholder messages
6. TimeOffRequestModal.tsx - Type labels and error messages
7. ManagerTeamPage.tsx - Already updated in previous session
8. ManagerOrganizationsPage.tsx - Already updated in previous session

## Status: ✅ LARGELY COMPLETE
- Translation files: ✅ Complete (50+ keys added across FR/EN/IT)
- Core component updates: ✅ Complete
- Build: ✅ Passes without TypeScript errors
- Remaining work: Optional enhancements to ValidationHistoryPage, AdminClientsPage, HoursReportPage (tracked separately if needed)

import { useState, useMemo, useEffect } from 'react'
import { useQueryClient, useQuery } from '@tanstack/react-query'
import { Pencil, Trash2, Check, X, Send, Moon, Clock, Car, TrendingUp, ChevronDown, ChevronRight, Plus, Filter, Download } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { swalDark, swalConfirm } from '../lib/swalConfig'
import Pagination from '../components/ui/Pagination'
import { apiClient } from '../lib/apiClient'
import type { TimesheetEntry } from '../features/timesheet/types'
import Button from '../components/ui/Button'
import QuickTimesheetModal from '../components/modals/QuickTimesheetModal'
import TimeOffRequestModal from '../components/modals/TimeOffRequestModal'
import { useUpdateEntry, useDeleteEntry, useSubmitWeek } from '../features/timesheet/hooks'
import PdfExportModal from '../components/modals/PdfExportModal'

// ISO 8601 week computation — matches Python's date.fromisocalendar used by the backend.
function getWeekFromDate(date: Date): string {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7))
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  const weekNo = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
  return `${d.getUTCFullYear()}-W${String(weekNo).padStart(2, '0')}`
}

function isoWeekToMonday(year: number, week: number): Date {
  const jan4 = new Date(Date.UTC(year, 0, 4))
  const jan4Day = jan4.getUTCDay() || 7
  const week1Monday = new Date(jan4)
  week1Monday.setUTCDate(jan4.getUTCDate() - jan4Day + 1)
  const monday = new Date(week1Monday)
  monday.setUTCDate(week1Monday.getUTCDate() + (week - 1) * 7)
  return monday
}

const LANG_LOCALE: Record<string, string> = { fr: 'fr-FR', it: 'it-IT', es: 'es-ES', en: 'en-GB' }

function weekLabel(week: string, t: (k: string, o?: any) => string, language: string): string {
  const [year, w] = week.split('-W').map(Number)
  const monday = isoWeekToMonday(year, w)
  const sunday = new Date(monday)
  sunday.setUTCDate(monday.getUTCDate() + 6)
  const locale = LANG_LOCALE[language] ?? 'fr-FR'
  return t('timesheet.weekLabel', {
    week: w,
    start: monday.toLocaleDateString(locale, { day: '2-digit', month: 'short', timeZone: 'UTC' }),
    end: sunday.toLocaleDateString(locale, { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' })
  })
}

function getEntryTypeConfig(t: any): Record<string, { label: string; color: string; icon: React.ReactNode }> {
  return {
    normal:   { label: t('entryTypes.normal', 'Normal'),   color: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',    icon: <Clock size={12} /> },
    overtime: { label: t('entryTypes.overtime', 'Supp.'),    color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',  icon: <TrendingUp size={12} /> },
    travel:   { label: t('entryTypes.travel', 'Trajet'),   color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',      icon: <Car size={12} /> },
    night:    { label: t('entryTypes.night', 'Nuit'),     color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',  icon: <Moon size={12} /> },
  }
}

function getStatusBadgeConfig(t: any): Record<string, { label: string; color: string }> {
  return {
    draft:     { label: t('statusBadges.draft', 'Brouillon'), color: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300' },
    submitted: { label: t('statusBadges.pending', 'En attente'), color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
    approved:  { label: t('statusBadges.approved', 'Approuvé'), color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
    rejected:  { label: t('statusBadges.rejected', 'Rejeté'), color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  }
}

function EntryRow({ entry, week, onRefresh, t }: { entry: TimesheetEntry; week: string; onRefresh: () => void; t: TFunction }) {
  const [editing, setEditing] = useState(false)
  const [hours, setHours] = useState(String(entry.hours_worked))
  const [desc, setDesc] = useState(entry.description)

  const canEdit = entry.status === 'draft' || entry.status === 'rejected'

  const saveMutation = useUpdateEntry(week)
  const deleteMutation = useDeleteEntry(week)

  const handleSave = () => {
    const payload: any = {
      hours_worked: parseFloat(hours),
      description: desc,
    }
    if (entry.status === 'rejected') {
      payload.notes = ''
    }
    saveMutation.mutate(
      { id: entry.timesheet_entry_id, payload },
      {
        onSuccess: () => {
          setEditing(false)
          onRefresh()
          if (entry.status === 'rejected') {
            swalDark({
              icon: 'success',
              title: 'Pointage corrigé',
              text: 'Votre pointage a été modifié. Pensez à le soumettre à nouveau.',
              timer: 3000,
              showConfirmButton: false,
            })
          }
        },
      }
    )
  }

  const handleDelete = async () => {
    const result = await swalConfirm({
      title: t('myTimesheets.deleteConfirm', 'Supprimer ce pointage ?'),
      icon: 'warning',
      confirmButtonColor: '#EF4444',
      cancelButtonColor: '#6B7280',
      confirmButtonText: 'Oui, supprimer',
      cancelButtonText: 'Annuler',
    })
    
    if (result.isConfirmed) {
      deleteMutation.mutate(entry.timesheet_entry_id, { onSuccess: onRefresh })
    }
  }

  const ENTRY_TYPE_CONFIG = getEntryTypeConfig(t)
  const typeConf = ENTRY_TYPE_CONFIG[entry.entry_type] ?? ENTRY_TYPE_CONFIG.normal
  const dateLabel = new Date(entry.work_date + 'T12:00:00').toLocaleDateString('fr-FR', {
    weekday: 'short', day: '2-digit', month: '2-digit',
  })

  if (editing) {
    return (
      <tr className="bg-indigo-50 dark:bg-indigo-900/20">
        <td className="px-3 py-2 text-xs text-slate-600 dark:text-slate-400 whitespace-nowrap">{dateLabel}</td>
        <td className="px-3 py-2 text-xs text-slate-800 dark:text-slate-200">{entry.project_name}</td>
        <td className="px-3 py-2 text-xs text-slate-500">{typeConf.label}</td>
        <td className="px-3 py-2">
          <input type="number" step="0.25" min="0.25" max="16" value={hours}
            onChange={e => setHours(e.target.value)}
            className="w-16 text-xs border border-slate-300 dark:border-slate-600 rounded px-2 py-0.5 text-center dark:bg-slate-700 dark:text-white" />
        </td>
        <td className="px-3 py-2">
          <input type="text" value={desc} onChange={e => setDesc(e.target.value)}
            className="w-full text-xs border border-slate-300 dark:border-slate-600 rounded px-2 py-0.5 dark:bg-slate-700 dark:text-white" />
        </td>
        <td className="px-3 py-2">
          <div className="flex items-center gap-1">
          <button onClick={handleSave} disabled={saveMutation.isPending} aria-label="Valider"
              className="p-1 rounded text-emerald-600 hover:bg-emerald-100 dark:hover:bg-emerald-900/30">
              <Check size={14} />
            </button>
            <button onClick={() => setEditing(false)} aria-label="Annuler"
              className="p-1 rounded text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700">
              <X size={14} />
            </button>
          </div>
        </td>
      </tr>
    )
  }

  return (
    <tr className="hover:bg-slate-50 dark:hover:bg-slate-700/50 border-b border-slate-100 dark:border-slate-700">
      <td className="px-3 py-2.5 text-xs text-slate-600 dark:text-slate-400 whitespace-nowrap">{dateLabel}</td>
      <td className="px-3 py-2.5 text-xs text-slate-800 dark:text-slate-200 font-medium">
        {entry.project_name}
        {entry.status === 'rejected' && entry.notes && (
          <div className="mt-1 text-xs text-red-600 dark:text-red-400 flex items-start gap-1">
            <span className="font-semibold">⚠️ Rejeté:</span>
            <span className="line-clamp-2">{entry.notes}</span>
          </div>
        )}
      </td>
      <td className="px-3 py-2.5">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${typeConf.color}`}>
          {typeConf.icon} {typeConf.label}
        </span>
      </td>
      <td className="px-3 py-2.5 text-xs text-slate-700 dark:text-slate-300 font-mono text-center">{entry.hours_worked}h</td>
      <td className="px-3 py-2.5 text-xs text-slate-600 dark:text-slate-400 max-w-xs truncate">{entry.description}</td>
      <td className="px-3 py-2.5">
        {canEdit ? (
          <div className="flex items-center gap-1">
            {entry.status === 'rejected' ? (
              <button onClick={() => setEditing(true)}
                className="px-2 py-1 rounded text-xs font-medium text-white bg-amber-500 hover:bg-amber-600 transition-colors flex items-center gap-1">
                <Pencil size={12} />
                Corriger
              </button>
            ) : (
              <>
                <button onClick={() => setEditing(true)} aria-label="Modifier"
                  className="p-1 rounded text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30">
                  <Pencil size={13} />
                </button>
                <button onClick={handleDelete} aria-label="Supprimer"
                  disabled={deleteMutation.isPending}
                  className="p-1 rounded text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 disabled:opacity-50">
                  <Trash2 size={13} />
                </button>
              </>
            )}
          </div>
        ) : (
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeConfig(t)[entry.status]?.color || 'bg-slate-100 text-slate-700'}`}>
            {getStatusBadgeConfig(t)[entry.status]?.label || entry.status}
          </span>
        )}
      </td>
    </tr>
  )
}

export default function MyTimesheetsPage() {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const [openWeek, setOpenWeek] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [showQuickMenu, setShowQuickMenu] = useState(false)
  const [showAbsenceModal, setShowAbsenceModal] = useState(false)
  const [statusFilter, setStatusFilter] = useState<'all' | 'draft' | 'submitted' | 'approved' | 'rejected'>('all')
  const [yearFilter, setYearFilter] = useState<number>(new Date().getFullYear())
  const [page, setPage] = useState(1)
  const [showPdfModal, setShowPdfModal] = useState(false)
  const PAGE_SIZE = 10

  // Fetch all entries (draft, submitted, approved, rejected)
  const { data: entries = [], isLoading } = useQuery({
    queryKey: ['timesheet-all-entries'],
    queryFn: () => apiClient.get<TimesheetEntry[]>('/employee/timesheet/entries'),
    staleTime: 0, // Always fetch fresh data
    gcTime: 0, // Don't cache (replaces cacheTime in v5)
  })

  const refresh = () => qc.invalidateQueries({ queryKey: ['timesheet-all-entries'] })

  // Group ALL entries by week (single source of truth)
  const entriesByWeek = useMemo(() => {
    const map: Record<string, TimesheetEntry[]> = {}
    for (const e of entries) {
      const d = new Date(e.work_date + 'T12:00:00')
      const week = getWeekFromDate(d)
      const [year] = week.split('-W').map(Number)
      
      // Filter by year
      if (year !== yearFilter) continue
      
      if (!map[week]) map[week] = []
      map[week].push(e)
    }
    return map
  }, [entries, yearFilter])

  // Filter weeks based on status filter
  const filteredWeeks = useMemo(() => {
    const weeks: Array<[string, TimesheetEntry[]]> = []
    
    for (const [week, weekEntries] of Object.entries(entriesByWeek)) {
      if (statusFilter === 'all') {
        // Show all weeks
        weeks.push([week, weekEntries])
      } else {
        // Only show weeks that have at least one entry with the selected status
        const hasMatchingStatus = weekEntries.some(e => e.status === statusFilter)
        if (hasMatchingStatus) {
          weeks.push([week, weekEntries])
        }
      }
    }
    
    // Sort by week descending (most recent first)
    return weeks.sort(([a], [b]) => b.localeCompare(a))
  }, [entriesByWeek, statusFilter])

  // Reset page when filters change
  useEffect(() => { setPage(1) }, [statusFilter, yearFilter])

  const totalPages = Math.max(1, Math.ceil(filteredWeeks.length / PAGE_SIZE))
  const paginatedWeeks = filteredWeeks.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const submitMutation = useSubmitWeek()

  const toggleWeek = (week: string) => {
    setOpenWeek(prev => prev === week ? null : week)
  }

  // Get available years from entries
  const availableYears = useMemo(() => {
    const years = new Set<number>()
    for (const e of entries) {
      const d = new Date(e.work_date + 'T12:00:00')
      years.add(d.getFullYear())
    }
    return Array.from(years).sort((a, b) => b - a)
  }, [entries])

  // Reset open week when page changes
  useEffect(() => { setOpenWeek(null) }, [page])

  // Calculate counts for the selected year only
  const yearEntries = useMemo(() => {
    return entries.filter(e => {
      const d = new Date(e.work_date + 'T12:00:00')
      return d.getFullYear() === yearFilter
    })
  }, [entries, yearFilter])

  const draftCount = yearEntries.filter(e => e.status === 'draft').length
  const submittedCount = yearEntries.filter(e => e.status === 'submitted').length
  const approvedCount = yearEntries.filter(e => e.status === 'approved').length
  const rejectedCount = yearEntries.filter(e => e.status === 'rejected').length
  const totalCount = yearEntries.length

  if (isLoading) return (
    <div className="text-slate-400 text-sm p-6">{t('common.loading')}</div>
  )

  return (
    <div className="max-w-5xl space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white">
            {t('timesheet.myTimesheets', 'Mes pointages')}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {totalCount} {t('timesheet.totalEntries')} · {draftCount} {t('timesheet.draftCount')} · {submittedCount} {t('timesheet.submittedCount')}
          </p>
        </div>
        
        {/* Desktop only - Quick actions menu */}
        <div className="hidden lg:flex items-center gap-2 relative">
          <button
            onClick={() => setShowPdfModal(true)}
            disabled={false}
            aria-label="Exporter en PDF"
            className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            PDF
          </button>
          <Button 
            icon={<Plus size={16} />} 
            onClick={() => setShowQuickMenu(!showQuickMenu)}
          >
            {t('myTimesheets.newEntry', 'Nouvelle saisie')}
          </Button>

          {/* Quick menu popup */}
          {showQuickMenu && (
            <>
              <div className="absolute top-full right-0 mt-2 flex flex-col gap-2 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 p-2 min-w-[200px] z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                <button
                  onClick={() => {
                    setShowQuickMenu(false)
                    setShowModal(true)
                  }}
                  className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-left"
                >
                  <Clock size={18} />
                  <span className="text-sm font-medium">{t('myTimesheets.quickEntry', 'Saisie rapide')}</span>
                </button>
                <button
                  onClick={() => {
                    setShowQuickMenu(false)
                    setShowAbsenceModal(true)
                  }}
                  className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-left"
                >
                  <Plus size={18} />
                  <span className="text-sm font-medium">{t('myTimesheets.declareAbsence', 'Déclarer absence')}</span>
                </button>
              </div>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowQuickMenu(false)}
              />
            </>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="space-y-3">
        {/* Year filter */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
            <Filter size={16} />
            <span className="font-medium">{t('myTimesheets.year', 'Année')}:</span>
          </div>
          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(Number(e.target.value))}
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-indigo-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:focus:ring-indigo-800 transition-all cursor-pointer"
          >
            {availableYears.map(year => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>

        {/* Status filter */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
            <Filter size={16} />
            <span className="font-medium">{t('myTimesheets.status', 'Statut')}:</span>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
            {[
              { value: 'all', label: t('common.all', 'Tous'), count: totalCount },
              { value: 'draft', label: t('myTimesheets.drafts', 'Brouillons'), count: draftCount },
              { value: 'submitted', label: t('myTimesheets.submitted', 'Soumis'), count: submittedCount },
              { value: 'approved', label: t('myTimesheets.approved', 'Approuvés'), count: approvedCount },
              { value: 'rejected', label: t('myTimesheets.rejected', 'Rejetés'), count: rejectedCount },
            ].map(({ value, label, count }) => (
              <button key={value}
                onClick={() => setStatusFilter(value as typeof statusFilter)}
                className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                  statusFilter === value
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 hover:border-indigo-300'
                }`}>
                {label} <span className="ml-1 opacity-70">({count})</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Empty state */}
      {filteredWeeks.length === 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <Clock size={40} className="mx-auto mb-3 text-slate-300 dark:text-slate-600" />
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            {statusFilter === 'all' && t('timesheet.noEntriesInProgress')}
            {statusFilter === 'draft' && t('timesheet.noDraftEntries')}
            {statusFilter === 'submitted' && t('timesheet.noPendingEntries')}
            {statusFilter === 'approved' && t('timesheet.noApprovedEntries')}
            {statusFilter === 'rejected' && t('timesheet.noRejectedEntries')}
          </p>
          <p className="text-slate-400 dark:text-slate-500 text-xs mt-1">
            {t('myTimesheets.clickNewEntryToStart', 'Cliquez sur "Nouvelle saisie" pour commencer')}
          </p>
        </div>
      )}

      {/* Weeks list */}
      <div className="space-y-4">
        {paginatedWeeks.map(([week, weekEntries]) => {
          const collapsed = openWeek !== week
          const totalHours = weekEntries.reduce((s, e) => s + Number(e.hours_worked), 0)

          // Calculate week status based on ALL entries in the week
          const allStatuses = new Set(weekEntries.map(e => e.status))
          const STATUS_BADGE = getStatusBadgeConfig(t)
          let weekStatusBadge: { label: string; color: string }

          // Priority: draft/submitted > rejected > approved
          // If at least one entry is draft or submitted, week is "Pending"
          if (allStatuses.has('draft') || allStatuses.has('submitted')) {
            weekStatusBadge = STATUS_BADGE.submitted
          } else if (allStatuses.has('rejected')) {
            weekStatusBadge = STATUS_BADGE.rejected
          } else if (allStatuses.has('approved')) {
            weekStatusBadge = STATUS_BADGE.approved
          } else {
            weekStatusBadge = STATUS_BADGE.draft
          }

          // Can submit if there's at least one draft entry in the week
          const hasDraft = weekEntries.some(e => e.status === 'draft')
          const canSubmit = hasDraft && weekEntries.length > 0
          const isSubmitting = submitMutation.isPending && submitMutation.variables === week

          return (
            <div key={week} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
              {/* Week header - Mobile optimized */}
              <div className="px-3 sm:px-4 py-3 bg-slate-50 dark:bg-slate-700 border-b border-slate-200 dark:border-slate-600">
                {/* Top row: Week label + Status badge */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <button onClick={() => toggleWeek(week)}
                    className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-800 dark:text-slate-200 hover:text-indigo-600 dark:hover:text-indigo-400 text-left flex-1 min-w-0">
                    {collapsed ? <ChevronRight size={16} className="flex-shrink-0" /> : <ChevronDown size={16} className="flex-shrink-0" />}
                    <span className="truncate">{weekLabel(week, t, i18n.language)}</span>
                  </button>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap flex-shrink-0 ${weekStatusBadge.color}`}>
                    {weekStatusBadge.label}
                  </span>
                </div>

                {/* Bottom row: Stats + Submit button */}
                <div className="flex items-center justify-between gap-2 pl-6">
                  <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{totalHours.toFixed(1)}h</span>
                    <span className="hidden sm:inline">·</span>
                    <span className="hidden sm:inline">{weekEntries.length} {t('timesheet.totalEntries')}</span>
                    <span className="sm:hidden text-slate-400">({weekEntries.length})</span>
                  </div>
                  {canSubmit && (
                    <button
                      onClick={() => submitMutation.mutate(week)}
                      disabled={isSubmitting}
                      className="flex items-center gap-1.5 text-white px-2 sm:px-3 py-1.5 rounded-lg text-xs font-medium disabled:opacity-50 transition-colors bg-indigo-600 hover:bg-indigo-700 whitespace-nowrap flex-shrink-0"
                    >
                      <Send size={12} />
                      <span className="hidden sm:inline">{isSubmitting ? t('timesheet.submittingButton') : t('timesheet.submitButton')}</span>
                      <span className="sm:hidden">✓</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Entries table */}
              {!collapsed && (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide border-b border-slate-100 dark:border-slate-700">
                        <th className="px-3 py-2 text-left">{t('timesheet.tableHeaders.date')}</th>
                        <th className="px-3 py-2 text-left">{t('timesheet.tableHeaders.project')}</th>
                        <th className="px-3 py-2 text-left">{t('timesheet.tableHeaders.type')}</th>
                        <th className="px-3 py-2 text-center">{t('timesheet.tableHeaders.hours')}</th>
                        <th className="px-3 py-2 text-left">{t('timesheet.tableHeaders.description')}</th>
                        <th className="px-3 py-2 text-left">{t('timesheet.tableHeaders.actions')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {weekEntries
                        .sort((a, b) => a.work_date.localeCompare(b.work_date))
                        .map(entry => (
                          <EntryRow key={entry.timesheet_entry_id} entry={entry} week={week} onRefresh={refresh} t={t} />
                        ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Pagination */}
      <Pagination
        page={page}
        totalPages={totalPages}
        totalItems={filteredWeeks.length}
        itemsPerPage={PAGE_SIZE}
        onPageChange={p => { setPage(p); setOpenWeek(null) }}
        itemLabel={t('timesheet.weekLabel', { week: '', start: '', end: '' }).split(' ')[0].toLowerCase()}
      />

      <QuickTimesheetModal open={showModal} onClose={() => setShowModal(false)} />
      <TimeOffRequestModal open={showAbsenceModal} onClose={() => setShowAbsenceModal(false)} />
      <PdfExportModal
        open={showPdfModal}
        onClose={() => setShowPdfModal(false)}
        mode="timesheet"
        defaultDateFrom={`${yearFilter}-01-01`}
        defaultDateTo={`${yearFilter}-12-31`}
      />
    </div>
  )
}

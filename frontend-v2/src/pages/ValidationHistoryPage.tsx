import { useState, useMemo } from 'react'
import { Filter, Eye, Calendar, Clock, FileText, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'
import type { TimesheetEntry } from '../features/timesheet/types'
import type { Absence } from '../features/absences/types'
import Modal from '../components/ui/Modal'
import TimeOffRequestModal from '../components/modals/TimeOffRequestModal'

type HistoryItem = {
  id: string
  type: 'timesheet' | 'absence'
  date: string
  endDate?: string
  project?: string
  hours?: number
  absenceType?: string
  description: string
  status: 'approved' | 'rejected' | 'submitted'
  rejectionReason?: string
  entryType?: string
}

const TYPE_LABELS: Record<string, string> = {
  timesheet: 'Pointage',
  absence: 'Absence',
  cp: 'Congé payé',
  maladie: 'Maladie',
  autre: 'Autre',
  normal: 'Normal',
  overtime: 'Heures supp.',
  travel: 'Trajet',
  night: 'Nuit',
}

const TYPE_COLORS: Record<string, string> = {
  timesheet: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
  absence: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  cp: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  maladie: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  autre: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
}

const STATUS_BADGE: Record<string, { label: string; color: string }> = {
  approved: { label: 'Approuvé', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
  rejected: { label: 'Rejeté', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  submitted: { label: 'En attente', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
}

function daysBetween(start: string, end: string): number {
  const ms = new Date(end).getTime() - new Date(start).getTime()
  return Math.max(1, Math.round(ms / 86400000) + 1)
}

export default function ValidationHistoryPage() {
  const { t } = useTranslation()
  const [typeFilter, setTypeFilter] = useState<'all' | 'timesheet' | 'absence'>('all')
  const [statusFilter, setStatusFilter] = useState<'all' | 'approved' | 'rejected' | 'submitted'>('all')
  const [yearFilter, setYearFilter] = useState<number>(new Date().getFullYear())
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null)
  const [showAbsenceModal, setShowAbsenceModal] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // Fetch approved/rejected timesheets
  const { data: timesheets = [], isLoading: loadingTimesheets } = useQuery({
    queryKey: ['timesheet-history'],
    queryFn: () => apiClient.get<TimesheetEntry[]>('/employee/timesheet/entries'),
  })

  // Fetch all absences
  const { data: absences = [], isLoading: loadingAbsences } = useQuery({
    queryKey: ['absences-history'],
    queryFn: () => apiClient.get<Absence[]>('/employee/absences'),
  })

  // Combine and transform data
  const historyItems = useMemo((): HistoryItem[] => {
    const items: HistoryItem[] = []

    // Add timesheets (only approved, rejected, or submitted)
    timesheets
      .filter(t => {
        if (!['approved', 'rejected', 'submitted'].includes(t.status)) return false
        const d = new Date(t.work_date + 'T12:00:00')
        return d.getFullYear() === yearFilter
      })
      .forEach(t => {
        items.push({
          id: `timesheet-${t.timesheet_entry_id}`,
          type: 'timesheet',
          date: t.work_date,
          project: t.project_name,
          hours: t.hours_worked,
          description: t.description,
          status: t.status as 'approved' | 'rejected' | 'submitted',
          rejectionReason: (t as any).rejection_reason || undefined,
          entryType: t.entry_type,
        })
      })

    // Add absences
    absences
      .filter(a => {
        const d = new Date(a.start_date + 'T12:00:00')
        return d.getFullYear() === yearFilter
      })
      .forEach(a => {
        items.push({
          id: `absence-${a.absence_id}`,
          type: 'absence',
          date: a.start_date,
          endDate: a.end_date,
          absenceType: a.absence_type,
          description: a.notes || `${TYPE_LABELS[a.absence_type] || a.absence_type} (${daysBetween(a.start_date, a.end_date)} jour${daysBetween(a.start_date, a.end_date) > 1 ? 's' : ''})`,
          status: a.status === 'pending' ? 'submitted' : a.status as 'approved' | 'rejected',
          rejectionReason: (a as any).rejection_reason || undefined,
        })
      })

    return items.sort((a, b) => b.date.localeCompare(a.date))
  }, [timesheets, absences, yearFilter])

  // Apply filters
  const filteredItems = useMemo(() => {
    let items = historyItems

    if (typeFilter !== 'all') {
      items = items.filter(i => i.type === typeFilter)
    }

    if (statusFilter !== 'all') {
      items = items.filter(i => i.status === statusFilter)
    }

    return items
  }, [historyItems, typeFilter, statusFilter])

  // Reset to page 1 whenever filters or page size change
  useMemo(() => { setPage(1) }, [typeFilter, statusFilter, yearFilter, pageSize])

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize))
  const safePage = Math.min(page, totalPages)
  const pageStart = (safePage - 1) * pageSize
  const pageEnd = pageStart + pageSize
  const pagedItems = filteredItems.slice(pageStart, pageEnd)

  const isLoading = loadingTimesheets || loadingAbsences

  const approvedCount = historyItems.filter(i => i.status === 'approved').length
  const rejectedCount = historyItems.filter(i => i.status === 'rejected').length
  const submittedCount = historyItems.filter(i => i.status === 'submitted').length

  // Get available years from all data
  const availableYears = useMemo(() => {
    const years = new Set<number>()
    timesheets.forEach(t => {
      const d = new Date(t.work_date + 'T12:00:00')
      years.add(d.getFullYear())
    })
    absences.forEach(a => {
      const d = new Date(a.start_date + 'T12:00:00')
      years.add(d.getFullYear())
    })
    return Array.from(years).sort((a, b) => b - a)
  }, [timesheets, absences])

  return (
    <div className="max-w-6xl space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white">
            {t('history.title', 'Historique des validations')}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {approvedCount} approuvé{approvedCount > 1 ? 's' : ''} · {rejectedCount} rejeté{rejectedCount > 1 ? 's' : ''} · {submittedCount} en attente
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-3 sm:p-4">
        <div className="flex flex-col gap-4">
          {/* Year filter */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              <Filter size={16} />
              <span className="font-medium">Année:</span>
            </div>
            <select
              value={yearFilter}
              onChange={(e) => setYearFilter(Number(e.target.value))}
              className="px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-indigo-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:focus:ring-indigo-800 transition-all cursor-pointer"
            >
              {availableYears.map(year => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>

          {/* Type filter */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              <span className="font-medium">Type:</span>
            </div>
            <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
              {[
                { value: 'all', label: 'Tous' },
                { value: 'timesheet', label: 'Pointages' },
                { value: 'absence', label: 'Absences' },
              ].map(({ value, label }) => (
                <button key={value}
                  onClick={() => setTypeFilter(value as typeof typeFilter)}
                  className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                    typeFilter === value
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-600'
                  }`}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Status filter */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              <span className="font-medium">Statut:</span>
            </div>
            <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
              {[
                { value: 'all', label: 'Tous' },
                { value: 'approved', label: 'Approuvés' },
                { value: 'rejected', label: 'Rejetés' },
                { value: 'submitted', label: 'En attente' },
              ].map(({ value, label }) => (
                <button key={value}
                  onClick={() => setStatusFilter(value as typeof statusFilter)}
                  className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                    statusFilter === value
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-600'
                  }`}>
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Results count */}
      <div className="text-sm text-slate-500 dark:text-slate-400">
        {filteredItems.length} résultat{filteredItems.length > 1 ? 's' : ''}
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <div className="text-slate-400 text-sm">Chargement…</div>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <FileText size={40} className="mx-auto mb-3 text-slate-300 dark:text-slate-600" />
          <p className="text-slate-500 dark:text-slate-400 text-sm">Aucun résultat</p>
          <p className="text-slate-400 dark:text-slate-500 text-xs mt-1">Essayez de modifier les filtres</p>
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden md:block bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-full">
              <thead>
                <tr className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/50">
                  <th className="px-4 py-3 text-left">Date</th>
                  <th className="px-4 py-3 text-left">Type</th>
                  <th className="px-4 py-3 text-left">Détails</th>
                  <th className="px-4 py-3 text-center">Heures/Durée</th>
                  <th className="px-4 py-3 text-left">Statut</th>
                  <th className="px-4 py-3 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {pagedItems.map(item => {
                  const typeColor = TYPE_COLORS[item.type === 'timesheet' ? 'timesheet' : item.absenceType || 'absence']
                  const typeLabel = item.type === 'timesheet' 
                    ? TYPE_LABELS.timesheet 
                    : TYPE_LABELS[item.absenceType || 'absence']
                  const statusBadge = STATUS_BADGE[item.status]

                  return (
                    <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <Calendar size={14} className="text-slate-400" />
                          {new Date(item.date + 'T12:00:00').toLocaleDateString('fr-FR', { 
                            day: '2-digit', month: 'short', year: 'numeric' 
                          })}
                          {item.endDate && item.endDate !== item.date && (
                            <span className="text-xs text-slate-400">
                              → {new Date(item.endDate + 'T12:00:00').toLocaleDateString('fr-FR', { 
                                day: '2-digit', month: 'short' 
                              })}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${typeColor}`}>
                          {item.type === 'timesheet' ? <Clock size={12} /> : <Calendar size={12} />}
                          {typeLabel}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">
                        {item.project && <div className="font-medium">{item.project}</div>}
                        <div className="text-xs text-slate-500 dark:text-slate-400 truncate max-w-md">
                          {item.description}
                        </div>
                        {item.entryType && item.entryType !== 'normal' && (
                          <span className="text-xs text-slate-400">
                            · {TYPE_LABELS[item.entryType]}
                          </span>
                        )}
                        {/* Rejection reason */}
                        {item.status === 'rejected' && item.rejectionReason && (
                          <div className="mt-1 flex items-start gap-1 text-xs text-red-600 dark:text-red-400">
                            <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
                            <span className="line-clamp-2">{item.rejectionReason}</span>
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {item.hours ? (
                          <span className="text-sm font-mono font-medium text-slate-700 dark:text-slate-300">
                            {item.hours}h
                          </span>
                        ) : item.endDate ? (
                          <span className="text-sm text-slate-600 dark:text-slate-400">
                            {daysBetween(item.date, item.endDate)} jour{daysBetween(item.date, item.endDate) > 1 ? 's' : ''}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${statusBadge.color}`}>
                          {statusBadge.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => setSelectedItem(item)}
                          className="p-1.5 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/30 text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                          title="Voir les détails"
                        >
                          <Eye size={16} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Mobile cards */}
        <div className="md:hidden space-y-3">
          {pagedItems.map(item => {
            const typeColor = TYPE_COLORS[item.type === 'timesheet' ? 'timesheet' : item.absenceType || 'absence']
            const typeLabel = item.type === 'timesheet' 
              ? TYPE_LABELS.timesheet 
              : TYPE_LABELS[item.absenceType || 'absence']
            const statusBadge = STATUS_BADGE[item.status]

            return (
              <div key={item.id} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${typeColor}`}>
                        {item.type === 'timesheet' ? <Clock size={12} /> : <Calendar size={12} />}
                        {typeLabel}
                      </span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${statusBadge.color}`}>
                        {statusBadge.label}
                      </span>
                    </div>
                    {item.project && (
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                        {item.project}
                      </p>
                    )}
                    <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mt-1">
                      {item.description}
                    </p>
                    {/* Rejection reason in mobile card */}
                    {item.status === 'rejected' && item.rejectionReason && (
                      <div className="mt-2 flex items-start gap-1 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                        <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
                        <span className="line-clamp-2">{item.rejectionReason}</span>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setSelectedItem(item)}
                    className="p-2 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/30 text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors flex-shrink-0"
                  >
                    <Eye size={16} />
                  </button>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-700">
                  <div className="flex items-center gap-1">
                    <Calendar size={12} />
                    {new Date(item.date + 'T12:00:00').toLocaleDateString('fr-FR', { 
                      day: '2-digit', month: 'short', year: 'numeric' 
                    })}
                    {item.endDate && item.endDate !== item.date && (
                      <span>
                        {' → '}
                        {new Date(item.endDate + 'T12:00:00').toLocaleDateString('fr-FR', { 
                          day: '2-digit', month: 'short' 
                        })}
                      </span>
                    )}
                  </div>
                  <div className="font-mono font-semibold text-slate-700 dark:text-slate-300">
                    {item.hours ? `${item.hours}h` : item.endDate ? `${daysBetween(item.date, item.endDate)}j` : '—'}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Pagination */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 px-4 py-3">
          <div className="flex items-center gap-3 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
            <span>
              {filteredItems.length === 0
                ? '0 résultat'
                : `${pageStart + 1}–${Math.min(pageEnd, filteredItems.length)} sur ${filteredItems.length}`}
            </span>
            <label className="flex items-center gap-1.5">
              <span>Par page :</span>
              <select
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
                className="border border-slate-200 dark:border-slate-600 rounded-md px-2 py-1 text-xs sm:text-sm bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {[10, 20, 50, 100].map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={safePage <= 1}
              className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              aria-label="Page précédente"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="px-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400 whitespace-nowrap">
              Page {safePage} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={safePage >= totalPages}
              className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              aria-label="Page suivante"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </>
      )}

      {/* Detail Modal */}
      <Modal
        open={!!selectedItem}
        onClose={() => setSelectedItem(null)}
        title="Détails"
        size="lg"
      >
        {selectedItem && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
                  Type
                </label>
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                  TYPE_COLORS[selectedItem.type === 'timesheet' ? 'timesheet' : selectedItem.absenceType || 'absence']
                }`}>
                  {selectedItem.type === 'timesheet' ? <Clock size={12} /> : <Calendar size={12} />}
                  {selectedItem.type === 'timesheet' 
                    ? TYPE_LABELS.timesheet 
                    : TYPE_LABELS[selectedItem.absenceType || 'absence']}
                </span>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
                  Statut
                </label>
                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                  STATUS_BADGE[selectedItem.status].color
                }`}>
                  {STATUS_BADGE[selectedItem.status].label}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
                Date
              </label>
              <p className="text-sm text-slate-700 dark:text-slate-300">
                {new Date(selectedItem.date + 'T12:00:00').toLocaleDateString('fr-FR', { 
                  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' 
                })}
                {selectedItem.endDate && selectedItem.endDate !== selectedItem.date && (
                  <span>
                    {' → '}
                    {new Date(selectedItem.endDate + 'T12:00:00').toLocaleDateString('fr-FR', { 
                      weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' 
                    })}
                  </span>
                )}
              </p>
            </div>

            {selectedItem.project && (
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
                  Projet
                </label>
                <p className="text-sm text-slate-700 dark:text-slate-300 font-medium">{selectedItem.project}</p>
              </div>
            )}

            {selectedItem.hours && (
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
                  Heures travaillées
                </label>
                <p className="text-sm text-slate-700 dark:text-slate-300 font-mono font-medium">{selectedItem.hours}h</p>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1">
                Description
              </label>
              <p className="text-sm text-slate-700 dark:text-slate-300">{selectedItem.description}</p>
            </div>

            {selectedItem.status === 'rejected' && selectedItem.rejectionReason && (
              <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle size={16} className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-semibold text-red-900 dark:text-red-200 uppercase tracking-wide mb-1">
                      Motif du rejet
                    </p>
                    <p className="text-sm text-red-700 dark:text-red-300">{selectedItem.rejectionReason}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      <TimeOffRequestModal open={showAbsenceModal} onClose={() => setShowAbsenceModal(false)} />
    </div>
  )
}

import { useState, useMemo } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { Pencil, Trash2, Check, X, Send, Moon, Clock, Car, TrendingUp, ChevronDown, ChevronRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { swalConfirm } from '../lib/swalConfig'
import { updateEntry, deleteEntry, submitWeek } from '../features/timesheet/api'
import { apiClient } from '../lib/apiClient'
import type { TimesheetEntry } from '../features/timesheet/types'

// ─── Helpers ──────────────────────────────────────────────────────────────────

// ISO 8601 week computation — matches Python's date.fromisocalendar used by the backend.
function getWeekFromDate(date: Date): string {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7))
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  const weekNo = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
  return `${d.getUTCFullYear()}-W${String(weekNo).padStart(2, '0')}`
}

function getCurrentWeek(): string {
  return getWeekFromDate(new Date())
}

// Convert ISO week (YYYY-Www) → Monday of that week (UTC) using a known anchor (Jan 4 is always in week 1).
function isoWeekToMonday(year: number, week: number): Date {
  const jan4 = new Date(Date.UTC(year, 0, 4))
  const jan4Day = jan4.getUTCDay() || 7
  const week1Monday = new Date(jan4)
  week1Monday.setUTCDate(jan4.getUTCDate() - jan4Day + 1)
  const monday = new Date(week1Monday)
  monday.setUTCDate(week1Monday.getUTCDate() + (week - 1) * 7)
  return monday
}

function weekLabel(week: string): string {
  const [year, w] = week.split('-W').map(Number)
  const monday = isoWeekToMonday(year, w)
  const sunday = new Date(monday)
  sunday.setUTCDate(monday.getUTCDate() + 6)
  const fmt = (d: Date) => d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', timeZone: 'UTC' })
  return `Semaine ${w} — ${fmt(monday)} → ${sunday.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' })}`
}

const ENTRY_TYPE_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  normal:   { label: 'Normal',   color: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',    icon: <Clock size={12} /> },
  overtime: { label: 'Supp.',    color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',  icon: <TrendingUp size={12} /> },
  travel:   { label: 'Trajet',   color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',      icon: <Car size={12} /> },
  night:    { label: 'Nuit',     color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',  icon: <Moon size={12} /> },
}

const STATUS_BADGE: Record<string, { label: string; color: string }> = {
  draft:     { label: 'Brouillon', color: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300' },
  submitted: { label: 'Soumis',    color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  approved:  { label: 'Approuvé',  color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
  rejected:  { label: 'Rejeté',    color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
}

// ─── EntryRow ─────────────────────────────────────────────────────────────────

function EntryRow({ entry, onRefresh }: { entry: TimesheetEntry; onRefresh: () => void }) {
  const [editing, setEditing] = useState(false)
  const [hours, setHours] = useState(String(entry.hours_worked))
  const [desc, setDesc] = useState(entry.description)

  const canEdit = entry.status === 'draft' || entry.status === 'rejected'

  const saveMutation = useMutation({
    mutationFn: () => updateEntry(entry.timesheet_entry_id, { hours_worked: parseFloat(hours), description: desc }),
    onSuccess: () => { setEditing(false); onRefresh() },
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteEntry(entry.timesheet_entry_id),
    onSuccess: onRefresh,
  })

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
            <button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}
              className="p-1 rounded text-emerald-600 hover:bg-emerald-100 dark:hover:bg-emerald-900/30">
              <Check size={14} />
            </button>
            <button onClick={() => setEditing(false)}
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
      <td className="px-3 py-2.5 text-xs text-slate-800 dark:text-slate-200 font-medium">{entry.project_name}</td>
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
            <button onClick={() => setEditing(true)}
              className="p-1 rounded text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30">
              <Pencil size={13} />
            </button>
            <button onClick={async () => {
              const result = await swalConfirm({
                title: 'Supprimer ce pointage ?',
                html: `Voulez-vous vraiment supprimer ce pointage de <strong>${entry.hours_worked}h</strong> ?`,
                icon: 'warning',
                confirmButtonColor: '#EF4444',
                cancelButtonColor: '#6B7280',
                confirmButtonText: 'Oui, supprimer',
                cancelButtonText: 'Annuler',
              })
              if (result.isConfirmed) deleteMutation.mutate()
            }}
              disabled={deleteMutation.isPending}
              className="p-1 rounded text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 disabled:opacity-50">
              <Trash2 size={13} />
            </button>
          </div>
        ) : (
          <span className="text-xs text-slate-400 italic">Lecture seule</span>
        )}
      </td>
    </tr>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function TimesheetDraftPage() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [collapsedWeeks, setCollapsedWeeks] = useState<Set<string>>(new Set())

  // Fetch ALL entries (not just drafts)
  const { data: entries = [], isLoading } = useQuery({
    queryKey: ['timesheet-all-entries'],
    queryFn: () => apiClient.get<TimesheetEntry[]>('/employee/timesheet/entries'),
  })

  const refresh = () => qc.invalidateQueries({ queryKey: ['timesheet-all-entries'] })

  const currentWeek = getCurrentWeek()

  const byWeek = useMemo(() => {
    const map: Record<string, TimesheetEntry[]> = {}
    for (const e of entries) {
      const d = new Date(e.work_date + 'T12:00:00')
      const week = getWeekFromDate(d)
      if (!map[week]) map[week] = []
      map[week].push(e)
    }
    return Object.entries(map).sort(([a], [b]) => b.localeCompare(a))
  }, [entries])

  const [submitError, setSubmitError] = useState<{ week: string; message: string } | null>(null)

  const submitMutation = useMutation({
    mutationFn: (week: string) => submitWeek(week),
    onSuccess: () => { setSubmitError(null); refresh() },
    onError: (err: Error, week) => {
      setSubmitError({ week, message: err.message ?? 'Erreur lors de la soumission' })
    },
  })

  const toggleWeek = (week: string) => {
    setCollapsedWeeks(prev => {
      const n = new Set(prev)
      n.has(week) ? n.delete(week) : n.add(week)
      return n
    })
  }

  if (isLoading) return (
    <div className="text-slate-400 text-sm p-6">Chargement…</div>
  )

  if (entries.length === 0) return (
    <div className="max-w-4xl space-y-5">
      <h1 className="text-2xl font-bold text-slate-800 dark:text-white">
        {t('timesheet.drafts', 'Mes saisies')}
      </h1>
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
        <Clock size={40} className="mx-auto mb-3 text-slate-300 dark:text-slate-600" />
        <p className="text-slate-500 dark:text-slate-400 text-sm">Aucune saisie enregistrée</p>
        <p className="text-slate-400 dark:text-slate-500 text-xs mt-1">Saisissez des heures pour les voir apparaître ici</p>
      </div>
    </div>
  )

  return (
    <div className="max-w-5xl space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-white">
          {t('timesheet.drafts', 'Mes saisies')}
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          {entries.length} entrée{entries.length > 1 ? 's' : ''} enregistrée{entries.length > 1 ? 's' : ''}
        </p>
      </div>

      <div className="space-y-4">
        {byWeek.map(([week, weekEntries]) => {
          const collapsed = collapsedWeeks.has(week)
          const totalHours = weekEntries.reduce((s, e) => s + e.hours_worked, 0)
          const isSubmitting = submitMutation.isPending && submitMutation.variables === week
          
          // Determine week status — priority: rejected > draft > submitted > approved
          // (rejected/draft are actionable, so they take priority for the badge)
          const statuses = new Set(weekEntries.map(e => e.status))
          let weekStatus: string
          let weekStatusBadge: { label: string; color: string }

          if (statuses.has('rejected')) {
            weekStatus = 'rejected'
            weekStatusBadge = STATUS_BADGE.rejected
          } else if (statuses.has('draft')) {
            weekStatus = 'draft'
            weekStatusBadge = STATUS_BADGE.draft
          } else if (statuses.has('submitted')) {
            weekStatus = 'submitted'
            weekStatusBadge = STATUS_BADGE.submitted
          } else {
            weekStatus = 'approved'
            weekStatusBadge = STATUS_BADGE.approved
          }

          // Submission is allowed only if there are draft/rejected entries
          // AND the week is fully archived (sunday already passed).
          const hasSubmittableEntries = statuses.has('draft') || statuses.has('rejected')
          const [wYear, wNum] = week.split('-W').map(Number)
          const weekMonday = isoWeekToMonday(wYear, wNum)
          const weekSunday = new Date(weekMonday)
          weekSunday.setUTCDate(weekMonday.getUTCDate() + 6)
          const todayUTC = new Date()
          todayUTC.setUTCHours(0, 0, 0, 0)
          const isArchivedWeek = weekSunday < todayUTC
          const canSubmit = isArchivedWeek && hasSubmittableEntries
          const isCurrentWeek = week === currentWeek

          return (
            <div key={week} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
              {/* Week header */}
              <div className="flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-700 border-b border-slate-200 dark:border-slate-600">
                <button onClick={() => toggleWeek(week)}
                  className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200 hover:text-indigo-600 dark:hover:text-indigo-400">
                  {collapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
                  {weekLabel(week)}
                </button>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{totalHours.toFixed(1)}h</span>
                    {' · '}{weekEntries.length} entrée{weekEntries.length > 1 ? 's' : ''}
                  </span>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${weekStatusBadge.color}`}>
                    {weekStatusBadge.label}
                  </span>
                  {canSubmit && (
                    <button
                      onClick={() => submitMutation.mutate(week)}
                      disabled={isSubmitting}
                      className={`flex items-center gap-1.5 text-white px-3 py-1.5 rounded-lg text-xs font-medium disabled:opacity-50 transition-colors ${
                        weekStatus === 'rejected' ? 'bg-orange-500 hover:bg-orange-600' : 'bg-indigo-600 hover:bg-indigo-700'
                      }`}
                    >
                      <Send size={12} />
                      {isSubmitting ? 'Soumission…' : weekStatus === 'rejected' ? 'Resoumettre' : 'Soumettre la semaine'}
                    </button>
                  )}
                  {!isArchivedWeek && hasSubmittableEntries && (
                    <span className="text-xs text-slate-400 italic" title="Une semaine ne peut être soumise qu'une fois terminée (après le dimanche)">
                      {isCurrentWeek ? 'Semaine en cours — soumettre après dimanche' : 'Semaine future'}
                    </span>
                  )}
                </div>
              </div>

              {submitError?.week === week && (
                <div className="px-4 py-2 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 text-xs text-red-700 dark:text-red-400">
                  {submitError.message}
                </div>
              )}

              {/* Entries table */}
              {!collapsed && (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide border-b border-slate-100 dark:border-slate-700">
                        <th className="px-3 py-2 text-left">Date</th>
                        <th className="px-3 py-2 text-left">Projet</th>
                        <th className="px-3 py-2 text-left">Type</th>
                        <th className="px-3 py-2 text-center">Heures</th>
                        <th className="px-3 py-2 text-left">Description</th>
                        <th className="px-3 py-2 text-left">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {weekEntries
                        .sort((a, b) => a.work_date.localeCompare(b.work_date))
                        .map(entry => (
                          <EntryRow key={entry.timesheet_entry_id} entry={entry} onRefresh={refresh} />
                        ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

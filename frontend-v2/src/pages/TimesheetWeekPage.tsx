import { useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Trash2, Send, Clock, Plus } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useWeek, useDeleteEntry, useSubmitWeek } from '../features/timesheet/hooks'
import type { TimesheetEntry } from '../features/timesheet/types'
import { StatusBadge } from '../components/ui/Badge'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getCurrentWeek(): string {
  const now = new Date()
  const jan1 = new Date(now.getFullYear(), 0, 1)
  const week = Math.ceil(((now.getTime() - jan1.getTime()) / 86400000 + jan1.getDay() + 1) / 7)
  return `${now.getFullYear()}-W${String(week).padStart(2, '0')}`
}

function shiftWeek(week: string, dir: 1 | -1): string {
  const [year, w] = week.split('-W').map(Number)
  const date = new Date(year, 0, 1 + (w - 1) * 7)
  date.setDate(date.getDate() + dir * 7)
  const newYear = date.getFullYear()
  const jan1 = new Date(newYear, 0, 1)
  const newWeek = Math.ceil(((date.getTime() - jan1.getTime()) / 86400000 + jan1.getDay() + 1) / 7)
  return `${newYear}-W${String(newWeek).padStart(2, '0')}`
}

function weekDates(week: string): Date[] {
  const [year, w] = week.split('-W').map(Number)
  const jan1 = new Date(year, 0, 1)
  const monday = new Date(jan1.getTime() + (w - 1) * 7 * 86400000)
  monday.setDate(monday.getDate() - monday.getDay() + 1)
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    return d
  })
}

function toISODate(d: Date): string {
  return d.toISOString().split('T')[0]
}

const DAY_NAMES = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']

const ENTRY_TYPE_COLORS: Record<string, string> = {
  overtime: 'bg-orange-100 text-orange-700',
  travel: 'bg-blue-100 text-blue-700',
  night: 'bg-indigo-100 text-indigo-700',
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function TimesheetWeekPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const week = searchParams.get('week') ?? getCurrentWeek()
  const dates = weekDates(week)

  const { data: weekData, isLoading } = useWeek(week)
  const deleteEntry = useDeleteEntry(week)
  const submitWeek = useSubmitWeek()

  const [submitError, setSubmitError] = useState('')
  const [submitSuccess, setSubmitSuccess] = useState(false)

  const navigate_ = (dir: 1 | -1) => setSearchParams({ week: shiftWeek(week, dir) })

  const allEntries: TimesheetEntry[] = weekData ? Object.values(weekData.entries).flat() : []
  const hasDraft = allEntries.some((e) => e.status === 'draft')

  const todayDate = new Date()
  todayDate.setHours(0, 0, 0, 0)
  const weekSunday = dates[6]
  const weekMonday = dates[0]
  const isPastWeek = weekSunday < todayDate
  const isFutureWeek = weekMonday > todayDate

  const handleSubmit = async () => {
    setSubmitError('')
    setSubmitSuccess(false)
    try {
      await submitWeek.mutateAsync(week)
      setSubmitSuccess(true)
      setTimeout(() => setSubmitSuccess(false), 3000)
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Erreur lors de la soumission'
      const translated: Record<string, string> = {
        'Week already submitted': 'Cette semaine a déjà été soumise',
        'No draft entries for this week': 'Aucune saisie en brouillon pour cette semaine',
      }
      const raw = typeof msg === 'string' ? msg : JSON.stringify(msg)
      setSubmitError(translated[raw] ?? raw)
    }
  }

  const weekLabel = `${dates[0].toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })} – ${dates[6].toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}`

  return (
    <div className="max-w-lg mx-auto space-y-4">
      {/* Week navigator */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate_(-1)}
          className="p-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm text-slate-600 dark:text-slate-400 hover:bg-slate-50 transition-colors"
        >
          <ChevronLeft size={20} />
        </button>

        <div className="text-center">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">Semaine</p>
          <p className="text-base font-bold text-slate-900 dark:text-white">{weekLabel}</p>
          {weekData && weekData.week_total > 0 && (
            <p className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold mt-0.5">
              {weekData.week_total}h cette semaine
            </p>
          )}
        </div>

        <button
          onClick={() => navigate_(1)}
          className="p-2.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm text-slate-600 dark:text-slate-400 hover:bg-slate-50 transition-colors"
        >
          <ChevronRight size={20} />
        </button>
      </div>

      {/* Feedback */}
      {submitSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700 text-sm font-medium">
          ✓ Semaine soumise pour validation
        </div>
      )}
      {submitError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          {submitError}
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-12 text-center text-slate-400 text-sm">
          Chargement…
        </div>
      ) : allEntries.length === 0 ? (
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-10 text-center">
          <Clock size={44} className="mx-auto text-slate-200 dark:text-slate-600 mb-3" />
          <p className="text-slate-500 dark:text-slate-400 font-medium mb-1">Aucune saisie cette semaine</p>
          <p className="text-slate-400 dark:text-slate-500 text-sm mb-5">Pointez vos heures depuis la page Saisie</p>
          <button
            onClick={() => navigate(`/timesheet/entry?date=${toISODate(dates[0])}`)}
            className="inline-flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-indigo-700 transition-colors"
          >
            <Plus size={16} /> Saisir des heures
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {dates.map((date, i) => {
            const dateStr = toISODate(date)
            const dayEntries = weekData?.entries[dateStr] ?? []
            const dayTotal = weekData?.daily_totals[dateStr] ?? 0
            const isToday = dateStr === toISODate(new Date())

            if (dayEntries.length === 0) return null

            return (
              <div
                key={dateStr}
                className={`bg-white dark:bg-slate-800 rounded-2xl border shadow-sm overflow-hidden ${
                  isToday ? 'border-indigo-300 dark:border-indigo-600' : 'border-slate-200 dark:border-slate-700'
                }`}
              >
                {/* Day header */}
                <div className={`flex items-center justify-between px-4 py-3 ${
                  isToday ? 'bg-indigo-600' : 'bg-slate-50 dark:bg-slate-700 border-b border-slate-100 dark:border-slate-600'
                }`}>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-bold ${isToday ? 'text-white' : 'text-slate-800 dark:text-slate-200'}`}>
                      {DAY_NAMES[i]}
                    </span>
                    <span className={`text-xs ${isToday ? 'text-indigo-200' : 'text-slate-500 dark:text-slate-400'}`}>
                      {date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
                    </span>
                    {isToday && (
                      <span className="text-xs bg-white/20 text-white px-2 py-0.5 rounded-full font-medium">
                        Aujourd'hui
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-bold ${
                      isToday
                        ? (dayTotal > 8 ? 'text-red-300' : 'text-white')
                        : (dayTotal > 8 ? 'text-red-600' : 'text-slate-700 dark:text-slate-300')
                    }`}>
                      {dayTotal}h
                    </span>
                    <button
                      onClick={() => navigate(`/timesheet/entry?date=${dateStr}`)}
                      className={`p-1.5 rounded-lg transition-colors ${
                        isToday
                          ? 'bg-white/20 hover:bg-white/30 text-white'
                          : 'bg-slate-100 dark:bg-slate-600 hover:bg-slate-200 dark:hover:bg-slate-500 text-slate-600 dark:text-slate-300'
                      }`}
                    >
                      <Plus size={14} />
                    </button>
                  </div>
                </div>

                {/* Entries */}
                <div className="divide-y divide-slate-50 dark:divide-slate-700">
                  {dayEntries.map((entry) => (
                    <div key={entry.timesheet_entry_id} className="flex items-start gap-3 px-4 py-3">
                      <div className="flex-shrink-0 w-12 h-12 bg-indigo-50 dark:bg-indigo-900/30 rounded-xl flex items-center justify-center">
                        <span className="text-sm font-bold text-indigo-700 dark:text-indigo-400">{entry.hours_worked}h</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
                          <StatusBadge status={entry.status} />
                          {entry.entry_type !== 'normal' && (
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ENTRY_TYPE_COLORS[entry.entry_type] ?? ''}`}>
                              {entry.entry_type === 'overtime' ? 'Heures supp.' : entry.entry_type === 'travel' ? 'Trajet' : 'Nuit'}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-2">{entry.description}</p>
                      </div>
                      {entry.status === 'draft' && (
                        <button
                          onClick={() => deleteEntry.mutate(entry.timesheet_entry_id)}
                          disabled={deleteEntry.isPending}
                          className="flex-shrink-0 p-2 text-slate-300 dark:text-slate-600 hover:text-red-500 transition-colors rounded-lg disabled:opacity-50"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Submit button */}
      {hasDraft && (
        <div className="sticky bottom-4 mt-4">
          {!isPastWeek ? (
            <div className="w-full flex items-center justify-center gap-2 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 py-4 rounded-2xl text-sm font-medium border border-slate-200 dark:border-slate-700">
              <Send size={16} className="opacity-50" />
              {isFutureWeek
                ? 'Impossible de soumettre une semaine future'
                : `Soumission disponible le lundi ${new Date(weekSunday.getTime() + 86400000).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })}`
              }
            </div>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={submitWeek.isPending}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-4 rounded-2xl text-base font-semibold shadow-lg hover:bg-indigo-700 active:scale-95 disabled:opacity-50 transition-all"
            >
              <Send size={18} />
              {submitWeek.isPending ? 'Envoi en cours…' : t('timesheet.submitWeek', 'Soumettre la semaine')}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

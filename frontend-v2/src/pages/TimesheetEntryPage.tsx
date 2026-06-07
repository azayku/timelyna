import { useState } from 'react'
import { Clock, TrendingUp, Car, Moon, CheckCircle2, AlertTriangle, Loader2, Trash2, CalendarDays, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import { useTranslation } from 'react-i18next'
import { useWeek, useCreateEntry, useDeleteEntry } from '../features/timesheet/hooks'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'
import { ApiError } from '../lib/apiClient'
import TemplateSelector from '../components/TemplateSelector'
import type { EntryTemplate } from '../features/entry-templates/api'

function toISOWeek(date: Date): string {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7))
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  const weekNo = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
  return `${d.getUTCFullYear()}-W${String(weekNo).padStart(2, '0')}`
}

function addDays(dateStr: string, n: number): string {
  const d = new Date(dateStr + 'T12:00:00')
  d.setDate(d.getDate() + n)
  return d.toISOString().split('T')[0]
}

const QUICK_HOURS = [1, 2, 4, 6, 7, 7.5, 8]

const ENTRY_TYPE_CONFIG = {
  normal:   { label: 'Normal',   icon: Clock,       color: 'border-slate-300 text-slate-700 bg-slate-50' },
  overtime: { label: 'Supp.',    icon: TrendingUp,  color: 'border-amber-300 text-amber-700 bg-amber-50' },
  travel:   { label: 'Trajet',   icon: Car,         color: 'border-blue-300 text-blue-700 bg-blue-50' },
  night:    { label: 'Nuit',     icon: Moon,        color: 'border-purple-300 text-purple-700 bg-purple-50' },
} as const

type EntryType = keyof typeof ENTRY_TYPE_CONFIG

export default function TimesheetEntryPage() {
  const { t } = useTranslation()
  const today = new Date().toISOString().split('T')[0]
  const [date, setDate] = useState(today)
  const [projectId, setProjectId] = useState('')
  const [hours, setHours] = useState('8')
  const [entryType, setEntryType] = useState<EntryType>('normal')
  const [description, setDescription] = useState('')
  const [apiError, setApiError] = useState<string | null>(null)
  const [billableFlag, setBillableFlag] = useState(true)
  const [dismissedAlert, setDismissedAlert] = useState(false)

  const week = toISOWeek(new Date(date + 'T12:00:00'))
  const { data: weekData, isLoading: loadingWeek } = useWeek(week)

  // Check for unsubmitted previous weeks
  const { data: unsubmittedWeeks = [] } = useQuery({
    queryKey: ['unsubmitted-weeks'],
    queryFn: async () => {
      const drafts = await apiClient.get<{ work_date: string; status: string }[]>('/employee/timesheet/drafts')
      const currentWeek = toISOWeek(new Date())
      const previousWeeks = new Set<string>()
      
      drafts.forEach(entry => {
        const entryWeek = toISOWeek(new Date(entry.work_date + 'T12:00:00'))
        if (entryWeek < currentWeek && entry.status === 'draft') {
          previousWeeks.add(entryWeek)
        }
      })
      
      return Array.from(previousWeeks).sort()
    },
  })

  // Projets filtrés par employé ET par date choisie
  const { data: projects = [], isLoading: loadingProjects } = useQuery({
    queryKey: ['employee-projects', date],
    queryFn: () => apiClient.get<{ project_id: number; project_name: string; status: string }[]>(
      `/projects?active=true&date=${date}`
    ),
  })

  const createMutation = useCreateEntry(week)
  const deleteMutation = useDeleteEntry(week)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectId) return
    setApiError(null)
    try {
      await createMutation.mutateAsync({
        project_id: Number(projectId),
        work_date: date,
        hours_worked: Number(hours),
        description: description.trim(),
        entry_type: entryType,
        billable_flag: billableFlag,
      })
      setDescription('')
      setProjectId('')
    } catch (err) {
      setApiError(err instanceof ApiError ? err.message : 'Erreur lors de la sauvegarde.')
    }
  }

  const handleApplyTemplate = (tpl: EntryTemplate) => {
    if (tpl.project_id) setProjectId(String(tpl.project_id))
    if (tpl.description) setDescription(tpl.description)
    if (tpl.default_hours) setHours(String(tpl.default_hours))
  }

  const dateObj = new Date(date + 'T12:00:00')
  const dateLabel = dateObj.toLocaleDateString('fr-FR', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })

  const weekEntries = Object.values(weekData?.entries ?? {}).flat()
  const weekTotal = weekData?.week_total ?? 0
  const isSubmitted = weekEntries.some(e => e.status !== 'draft')
  const todayEntries = weekEntries.filter(e => e.work_date === date)
  const todayTotal = todayEntries.reduce((s, e) => s + Number(e.hours_worked), 0)

  const showUnsubmittedAlert = !dismissedAlert && unsubmittedWeeks.length > 0

  return (
    <div className="max-w-lg mx-auto space-y-4">

      {/* ── Unsubmitted weeks alert ── */}
      {showUnsubmittedAlert && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl">
          <AlertCircle size={18} className="text-amber-600 dark:text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-amber-900 dark:text-amber-200">
              Vous avez {unsubmittedWeeks.length} semaine{unsubmittedWeeks.length > 1 ? 's' : ''} précédente{unsubmittedWeeks.length > 1 ? 's' : ''} avec des saisies non soumises.
            </p>
            <Link to="/timesheet/drafts" 
              className="text-sm text-amber-700 dark:text-amber-400 hover:text-amber-800 dark:hover:text-amber-300 underline font-medium mt-1 inline-block">
              → Voir mes brouillons
            </Link>
          </div>
          <button onClick={() => setDismissedAlert(true)}
            className="p-1 rounded hover:bg-amber-100 dark:hover:bg-amber-900/40 text-amber-600 dark:text-amber-500">
            <Trash2 size={14} />
          </button>
        </div>
      )}

      {/* ── Date navigator ── */}
      <Card>
        <div className="flex items-center gap-3">
          <button onClick={() => setDate(addDays(date, -1))}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 transition-colors">
            <ChevronLeft size={18} />
          </button>
          <div className="flex-1 text-center">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">{week}</p>
            <p className="text-base font-bold text-slate-800 dark:text-white capitalize">{dateLabel}</p>
            {todayTotal > 0 && (
              <p className="text-xs text-indigo-600 font-medium mt-0.5">{todayTotal}h saisies aujourd'hui</p>
            )}
          </div>
          <button onClick={() => setDate(addDays(date, 1))}
            disabled={date >= today}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 disabled:opacity-30 transition-colors">
            <ChevronRight size={18} />
          </button>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <CalendarDays size={14} className="text-slate-400" />
          <input type="date" value={date} max={today}
            onChange={e => { setDate(e.target.value); setProjectId('') }}
            className="flex-1 border border-slate-200 dark:border-slate-600 rounded-lg px-3 py-1.5 text-sm text-slate-700 dark:text-slate-300 dark:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
      </Card>

      {/* ── Entries this week ── */}
      {loadingWeek ? (
        <div className="flex items-center justify-center py-6 text-slate-400 text-sm gap-2">
          <Loader2 size={14} className="animate-spin" /> Chargement…
        </div>
      ) : weekEntries.length > 0 && (
        <Card padding={false}>
          <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Semaine {week}
              </span>
              <span className="ml-2 text-xs font-bold text-indigo-600">{weekTotal}h</span>
            </div>
            {isSubmitted && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                <CheckCircle2 size={11} /> {weekEntries[0]?.status}
              </span>
            )}
          </div>
          <div className="divide-y divide-slate-50 dark:divide-slate-700/50">
            {weekEntries.map(entry => {
              const cfg = ENTRY_TYPE_CONFIG[entry.entry_type as EntryType] ?? ENTRY_TYPE_CONFIG.normal
              const Icon = cfg.icon
              return (
                <div key={entry.timesheet_entry_id}
                  className={`flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/50 ${entry.work_date === date ? 'bg-indigo-50/50 dark:bg-indigo-900/10' : ''}`}>
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${cfg.color}`}>
                    <Icon size={13} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                      {entry.project_name ?? `Projet #${entry.project_id}`}
                    </p>
                    <p className="text-xs text-slate-400">
                      {new Date(entry.work_date + 'T12:00:00').toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' })}
                      {entry.description && ` · ${entry.description}`}
                    </p>
                  </div>
                  <span className="text-sm font-bold text-slate-700 dark:text-slate-300 flex-shrink-0">{entry.hours_worked}h</span>
                  {entry.status === 'draft' && (
                    <button onClick={() => deleteMutation.mutate(entry.timesheet_entry_id)}
                      disabled={deleteMutation.isPending}
                      className="p-1.5 rounded-lg hover:bg-red-50 text-slate-300 hover:text-red-500 disabled:opacity-50 transition-colors">
                      <Trash2 size={13} />
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        </Card>
      )}

      {/* ── Entry form ── */}
      {!isSubmitted && (
        <form onSubmit={handleSubmit} className="space-y-3">
          
          {/* Template selector */}
          <div className="flex justify-end">
            <TemplateSelector
              onApply={handleApplyTemplate}
              currentData={{
                project_id: projectId ? Number(projectId) : undefined,
                description: description || undefined,
                hours_worked: hours ? Number(hours) : undefined,
              }}
            />
          </div>

          {/* Project selector */}
          <Card>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              {t('timesheet.project', 'Projet')} *
            </label>
            {loadingProjects ? (
              <div className="flex items-center gap-2 text-slate-400 text-xs py-1">
                <Loader2 size={12} className="animate-spin" /> Chargement des projets…
              </div>
            ) : projects.length === 0 ? (
              <p className="text-sm text-slate-400 italic py-1">
                Aucun projet actif assigné pour cette date.
              </p>
            ) : (
              <select value={projectId} onChange={e => setProjectId(e.target.value)} required
                className="w-full text-sm text-slate-800 dark:text-slate-200 bg-transparent border border-slate-200 dark:border-slate-600 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700">
                <option value="">— Choisir un projet —</option>
                {projects.map(p => (
                  <option key={p.project_id} value={p.project_id}>{p.project_name}</option>
                ))}
              </select>
            )}
          </Card>

          {/* Hours */}
          <Card>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
              {t('timesheet.hours', 'Heures travaillées')} *
            </label>
            <div className="flex gap-2 mb-3 flex-wrap">
              {QUICK_HOURS.map(h => (
                <button key={h} type="button" onClick={() => setHours(String(h))}
                  className={`px-3 py-1.5 rounded-lg text-sm font-semibold border-2 transition-all ${
                    hours === String(h)
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-600 hover:border-indigo-300'
                  }`}>
                  {h}h
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input type="number" step="0.25" min="0.25" max="16" value={hours}
                onChange={e => setHours(e.target.value)}
                className="w-24 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm text-center focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white" />
              <span className="text-sm text-slate-400">heures</span>
            </div>
          </Card>

          {/* Entry type */}
          <Card>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
              Type d'heures
            </label>
            <div className="grid grid-cols-4 gap-2">
              {(Object.entries(ENTRY_TYPE_CONFIG) as [EntryType, typeof ENTRY_TYPE_CONFIG[EntryType]][]).map(([value, cfg]) => {
                const Icon = cfg.icon
                return (
                  <label key={value}
                    className={`flex flex-col items-center gap-1.5 py-2.5 px-1 rounded-xl border-2 cursor-pointer transition-all text-xs font-semibold ${
                      entryType === value ? cfg.color + ' shadow-sm' : 'border-slate-200 dark:border-slate-600 text-slate-500 hover:border-slate-300'
                    }`}>
                    <input type="radio" value={value} checked={entryType === value}
                      onChange={() => setEntryType(value)} className="sr-only" />
                    <Icon size={15} />
                    {cfg.label}
                  </label>
                )
              })}
            </div>
          </Card>

          {/* Billable flag */}
          <Card>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" checked={billableFlag} onChange={e => setBillableFlag(e.target.checked)}
                className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-2 focus:ring-indigo-500" />
              <div>
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Heures facturables</span>
                <p className="text-xs text-slate-400 mt-0.5">Ces heures seront incluses dans la facturation client</p>
              </div>
            </label>
          </Card>

          {/* Description */}
          <Card>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              {t('timesheet.description', 'Description')} *
            </label>
            <textarea rows={3} value={description} onChange={e => setDescription(e.target.value)}
              required
              placeholder={t('timesheet.descriptionPlaceholder', 'Décrivez les tâches effectuées…')}
              className="w-full text-sm text-slate-800 dark:text-slate-200 bg-transparent border-0 outline-none focus:ring-0 resize-none placeholder-slate-300 dark:placeholder-slate-600" />
          </Card>

          {apiError && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              <AlertTriangle size={15} className="flex-shrink-0 mt-0.5" />{apiError}
            </div>
          )}

          {createMutation.isSuccess && (
            <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-700">
              <CheckCircle2 size={15} /> Pointage enregistré
            </div>
          )}

          <Button type="submit" size="lg" className="w-full justify-center" loading={createMutation.isPending}
            disabled={!projectId || projects.length === 0}>
            {t('timesheet.save', 'Enregistrer les heures')}
          </Button>
        </form>
      )}

      {isSubmitted && (
        <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-xl text-blue-700 text-sm">
          <CheckCircle2 size={18} />
          Cette semaine a été soumise pour approbation.
        </div>
      )}
    </div>
  )
}

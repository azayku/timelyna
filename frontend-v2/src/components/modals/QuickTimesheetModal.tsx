import { useState, useMemo } from 'react'
import { X, Clock, TrendingUp, Car, Moon, AlertTriangle, CheckCircle2, Loader2, Plus, Trash2 } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { apiClient, ApiError } from '../../lib/apiClient'
import { useCreateEntry } from '../../features/timesheet/hooks'

interface QuickTimesheetModalProps {
  open: boolean
  onClose: () => void
  defaultDate?: string
}

type EntryType = 'normal' | 'overtime' | 'travel' | 'night'

interface EntryRow {
  id: number
  type: EntryType
  hours: string
  description: string
}

const TYPE_CONFIG: Record<EntryType, {
  label: string
  shortLabel: string
  icon: React.ElementType
  accent: string
  bg: string
  border: string
  pill: string
}> = {
  normal: {
    label: 'Heures normales',
    shortLabel: 'Normal',
    icon: Clock,
    accent: 'text-slate-700 dark:text-slate-200',
    bg: 'bg-slate-50 dark:bg-slate-700/50',
    border: 'border-slate-200 dark:border-slate-600',
    pill: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
  },
  overtime: {
    label: 'Heures supplémentaires',
    shortLabel: 'Supp.',
    icon: TrendingUp,
    accent: 'text-amber-700 dark:text-amber-300',
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-200 dark:border-amber-800',
    pill: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  },
  travel: {
    label: 'Heures de trajet',
    shortLabel: 'Trajet',
    icon: Car,
    accent: 'text-blue-700 dark:text-blue-300',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    pill: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  },
  night: {
    label: 'Heures de nuit',
    shortLabel: 'Nuit',
    icon: Moon,
    accent: 'text-purple-700 dark:text-purple-300',
    bg: 'bg-purple-50 dark:bg-purple-900/20',
    border: 'border-purple-200 dark:border-purple-800',
    pill: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  },
}

const QUICK_HOURS = [1, 2, 3, 4, 5, 6, 7, 8]
const ALL_TYPES: EntryType[] = ['normal', 'overtime', 'travel', 'night']

let _nextId = 1
function nextId() { return _nextId++ }

function toISOWeek(date: Date): string {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7))
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  const weekNo = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
  return `${d.getUTCFullYear()}-W${String(weekNo).padStart(2, '0')}`
}

function HoursSelector({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <div className="flex gap-1 flex-wrap">
        {QUICK_HOURS.map(h => (
          <button
            key={h}
            type="button"
            onClick={() => onChange(String(h))}
            className={`w-9 h-8 rounded-lg text-xs font-bold border-2 transition-all ${
              value === String(h)
                ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-600 hover:border-indigo-300 dark:hover:border-indigo-500'
            }`}
          >
            {h}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-1.5 ml-1">
        <input
          type="number"
          step="0.25"
          min="0.25"
          max="16"
          value={value}
          onChange={e => onChange(e.target.value)}
          className="w-16 h-8 border border-slate-300 dark:border-slate-600 rounded-lg px-2 text-xs text-center focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800 dark:text-white"
        />
        <span className="text-xs text-slate-400 font-medium">h</span>
      </div>
    </div>
  )
}

export default function QuickTimesheetModal({ open, onClose, defaultDate }: QuickTimesheetModalProps) {
  const today = new Date().toISOString().split('T')[0]
  const { t } = useTranslation()
  const [date, setDate] = useState(defaultDate || today)
  const [projectId, setProjectId] = useState('')
  const [rows, setRows] = useState<EntryRow[]>([
    { id: nextId(), type: 'normal', hours: '8', description: '' },
  ])
  const [globalError, setGlobalError] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const week = toISOWeek(new Date(date + 'T12:00:00'))
  const createMutation = useCreateEntry(week)

  const { data: projects = [], isLoading: loadingProjects } = useQuery({
    queryKey: ['employee-projects', date],
    queryFn: () => apiClient.get<{ project_id: number; project_name: string }[]>(
      `/projects?active=true&date=${date}`
    ),
    enabled: open,
  })

  const totalHours = useMemo(
    () => rows.reduce((s, r) => s + Number(r.hours || 0), 0),
    [rows]
  )

  const usedTypes = new Set(rows.map(r => r.type))
  const availableTypes = ALL_TYPES.filter(t => !usedTypes.has(t))

  function addRow() {
    const type = availableTypes[0]
    if (!type) return
    setRows(prev => [...prev, { id: nextId(), type, hours: '4', description: '' }])
  }

  function removeRow(id: number) {
    setRows(prev => prev.filter(r => r.id !== id))
  }

  function updateRow(id: number, patch: Partial<EntryRow>) {
    setRows(prev => prev.map(r => r.id === id ? { ...r, ...patch } : r))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectId || rows.length === 0) return
    setGlobalError(null)
    setSubmitting(true)
    try {
      await Promise.all(rows.map(row =>
        createMutation.mutateAsync({
          project_id: Number(projectId),
          work_date: date,
          hours_worked: Number(row.hours),
          description: row.description.trim(),
          entry_type: row.type,
          billable_flag: true,
        })
      ))
      setSubmitted(true)
      setTimeout(() => {
        setRows([{ id: nextId(), type: 'normal', hours: '8', description: '' }])
        setProjectId('')
        setSubmitted(false)
        onClose()
      }, 1200)
    } catch (err) {
      setGlobalError(err instanceof ApiError ? err.message : t('quickTimesheet.error', 'Erreur lors de la sauvegarde.'))
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) return null

  const dateLabel = new Date(date + 'T12:00:00').toLocaleDateString(undefined, {
    weekday: 'long', day: 'numeric', month: 'long',
  })

  const canAddMore = availableTypes.length > 0
  const isDescriptionRequired = (type: EntryType) => type === 'overtime'
  const canSubmit = !!projectId && rows.length > 0 && rows.every(r => Number(r.hours) > 0 && (!isDescriptionRequired(r.type) || r.description.trim().length > 0))

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-white dark:bg-slate-900 w-full sm:max-w-2xl sm:rounded-2xl shadow-2xl flex flex-col max-h-[95dvh] rounded-t-2xl">

        {/* ── Header ─────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center">
              <Clock size={18} className="text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-800 dark:text-white leading-tight">{t('timesheet.quickEntry', 'Saisie rapide')}</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 capitalize">{dateLabel}</p>
            </div>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* ── Form ───────────────────────────────────────────── */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
          <div className="px-5 pt-4 pb-2 space-y-4">

            {/* Date + Project row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                  {t('common.date', 'Date')} *
                </label>
                <input
                  type="date"
                  value={date}
                  max={today}
                  onChange={e => { setDate(e.target.value); setProjectId('') }}
                  className="w-full border border-slate-300 dark:border-slate-600 rounded-xl px-3 py-2.5 text-sm text-slate-800 dark:text-slate-200 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                  {t('timesheet.project', 'Projet')} *
                </label>
                {loadingProjects ? (
                  <div className="flex items-center gap-2 text-slate-400 text-xs py-3">
                    <Loader2 size={12} className="animate-spin" /> {t('common.loading', 'Chargement…')}
                  </div>
                ) : (
                  <select
                    value={projectId}
                    onChange={e => setProjectId(e.target.value)}
                    required
                    className="w-full text-sm text-slate-800 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">{t('timesheet.chooseProject', '— Choisir —')}</option>
                    {projects.map(p => (
                      <option key={p.project_id} value={p.project_id}>{p.project_name}</option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
              <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">{t('timesheet.entryType', 'Types de pointage')}</span>
              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
            </div>

            {/* Entry rows */}
            <div className="space-y-3">
              {rows.map((row, idx) => {
                const cfg = TYPE_CONFIG[row.type]
                const Icon = cfg.icon
                return (
                  <div
                    key={row.id}
                    className={`rounded-xl border-2 ${cfg.border} ${cfg.bg} overflow-hidden transition-all`}
                  >
                    {/* Row header */}
                    <div className="flex items-center gap-2 px-4 pt-3 pb-2">
                      {/* Type selector */}
                      <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg ${cfg.pill} shrink-0`}>
                        <Icon size={13} />
                        <select
                          value={row.type}
                          onChange={e => updateRow(row.id, { type: e.target.value as EntryType })}
                          className="text-xs font-semibold bg-transparent border-none outline-none cursor-pointer"
                        >
                          <option value={row.type}>{cfg.label}</option>
                          {availableTypes
                            .filter(t => t !== row.type)
                            .map(t => (
                              <option key={t} value={t}>{TYPE_CONFIG[t].label}</option>
                            ))
                          }
                        </select>
                      </div>

                      <div className="flex-1" />

                      {/* Row index badge */}
                      <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500">#{idx + 1}</span>

                      {/* Remove button */}
                      {rows.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeRow(row.id)}
                          className="w-7 h-7 flex items-center justify-center rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>

                    {/* Hours */}
                    <div className="px-4 pb-2">
                      <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">{t('timesheet.hours', 'Heures')} *</p>
                      <HoursSelector value={row.hours} onChange={v => updateRow(row.id, { hours: v })} />
                    </div>

                    {/* Description */}
                    <div className="px-4 pb-3">
                      <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                        {t('timesheet.description', 'Description')}{isDescriptionRequired(row.type) ? ' *' : ''}
                      </p>
                      <textarea
                        rows={2}
                        value={row.description}
                        onChange={e => updateRow(row.id, { description: e.target.value })}
                        required={isDescriptionRequired(row.type)}
                        placeholder={t('timesheet.descriptionPlaceholder', 'Décrivez les tâches effectuées…')}
                        className="w-full text-sm text-slate-800 dark:text-slate-200 bg-white/70 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-600 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none placeholder-slate-400 dark:placeholder-slate-500"
                      />
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Add type button */}
            {canAddMore && (
              <button
                type="button"
                onClick={addRow}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-600 text-sm font-medium text-slate-500 dark:text-slate-400 hover:border-indigo-400 hover:text-indigo-600 dark:hover:border-indigo-500 dark:hover:text-indigo-400 transition-all"
              >
                <Plus size={16} />
                {t('quickTimesheet.addType', 'Ajouter un type de pointage')}
              </button>
            )}

            {/* Error */}
            {globalError && (
              <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-700 dark:text-red-400">
                <AlertTriangle size={15} className="shrink-0 mt-0.5" />
                {globalError}
              </div>
            )}

            {/* Success */}
            {submitted && (
              <div className="flex items-center gap-2 p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl text-sm text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 size={15} />
                {rows.length > 1 ? `${rows.length} ${t('common.entries', 'pointages')} ${t('success.saved', 'enregistrés')} !` : `${t('common.entry', 'Pointage')} ${t('success.saved', 'enregistré')} !`}
              </div>
            )}
          </div>

          {/* ── Footer ─────────────────────────────────────────── */}
          <div className="sticky bottom-0 flex items-center justify-between gap-3 px-5 py-4 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shrink-0">
            {/* Total */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 flex items-center justify-center">
                <Clock size={15} className="text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider leading-tight">{t('common.total', 'Total')}</p>
                <p className="text-base font-bold text-slate-800 dark:text-white leading-tight">
                  {totalHours % 1 === 0 ? totalHours : totalHours.toFixed(2)}h
                  {rows.length > 1 && (
                    <span className="text-xs font-normal text-slate-400 ml-1.5">
                      ({rows.length} {t('common.entries', 'lignes')})
                    </span>
                  )}
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-xl transition-colors"
              >
                {t('common.cancel', 'Annuler')}
              </button>
              <button
                type="submit"
                disabled={!canSubmit || submitting || submitted}
                className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-colors shadow-sm"
              >
                {submitting && <Loader2 size={14} className="animate-spin" />}
                {submitted ? <CheckCircle2 size={14} /> : null}
                {submitted ? t('success.saved', 'Enregistré !') : submitting ? t('common.submitting', 'Envoi…') : `${t('common.save', 'Enregistrer')}${rows.length > 1 ? ` (${rows.length})` : ''}`}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

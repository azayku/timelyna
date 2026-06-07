import { useState } from 'react'
import { Plus, X, Loader2, AlertTriangle } from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import { StatusBadge } from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import Table from '../components/ui/Table'
import { useTranslation } from 'react-i18next'
import { useMyAbsences, useCreateAbsence, useCancelAbsence } from '../features/absences/hooks'
import type { Absence } from '../features/absences/types'
import { ApiError } from '../lib/apiClient'

const TYPE_COLORS: Record<string, string> = {
  cp: 'bg-indigo-100 text-indigo-700',
  maladie: 'bg-red-100 text-red-700',
  autre: 'bg-slate-100 text-slate-600',
}

const TYPE_LABELS: Record<string, string> = {
  cp: 'Conge paye',
  maladie: 'Maladie',
  autre: 'Autre',
}

function daysBetween(start: string, end: string): number {
  const ms = new Date(end).getTime() - new Date(start).getTime()
  return Math.max(1, Math.round(ms / 86400000) + 1)
}

export default function AbsencesPage() {
  const { t } = useTranslation()
  const { data: absences = [], isLoading, isError } = useMyAbsences()
  const createMutation = useCreateAbsence()
  const cancelMutation = useCancelAbsence()

  const [modal, setModal] = useState(false)
  const [form, setForm] = useState({ absence_type: 'cp', start_date: '', end_date: '', notes: '' })
  const [apiError, setApiError] = useState<string | null>(null)

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setApiError(null)
    try {
      await createMutation.mutateAsync({
        absence_type: form.absence_type,
        start_date: form.start_date,
        end_date: form.end_date,
        notes: form.notes.trim() || undefined,
      })
      setModal(false)
      setForm({ absence_type: 'cp', start_date: '', end_date: '', notes: '' })
    } catch (err) {
      setApiError(err instanceof ApiError ? err.message : 'Erreur inattendue.')
    }
  }

  const taken = absences.filter(a => a.status === 'approved')
    .reduce((s, a) => s + daysBetween(a.start_date, a.end_date), 0)

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: t('absences.daysAcquired', 'Jours acquis'), value: 25, color: 'text-indigo-600' },
          { label: t('absences.daysTaken', 'Jours pris'), value: taken, color: 'text-amber-600' },
          { label: t('absences.daysRemaining', 'Jours restants'), value: Math.max(0, 25 - taken), color: 'text-emerald-600' },
        ].map(item => (
          <Card key={item.label}>
            <p className="text-xs text-slate-400 mb-1">{item.label}</p>
            <p className={`text-3xl font-bold ${item.color}`}>{item.value}</p>
            <p className="text-xs text-slate-400 mt-1">{t('common.days', 'jours')}</p>
          </Card>
        ))}
      </div>

      <div className="flex justify-end">
        <Button icon={<Plus size={14} />} onClick={() => setModal(true)}>
          {t('absences.declare', 'Declarer une absence')}
        </Button>
      </div>

      <Card padding={false}>
        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
            <Loader2 size={16} className="animate-spin" /> Chargement...
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center gap-2 py-16 text-red-500 text-sm">
            <AlertTriangle size={16} /> Impossible de charger les absences.
          </div>
        ) : (
          <Table
            columns={[
              {
                key: 'absence_type',
                header: t('common.type', 'Type'),
                render: (r: Absence) => (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${TYPE_COLORS[r.absence_type] ?? 'bg-slate-100 text-slate-600'}`}>
                    {TYPE_LABELS[r.absence_type] ?? r.absence_type}
                  </span>
                ),
              },
              {
                key: 'start_date',
                header: t('absences.start', 'Debut'),
                render: (r: Absence) => new Date(r.start_date).toLocaleDateString('fr-FR'),
              },
              {
                key: 'end_date',
                header: t('absences.end', 'Fin'),
                render: (r: Absence) => new Date(r.end_date).toLocaleDateString('fr-FR'),
              },
              {
                key: 'days',
                header: t('absences.duration', 'Duree'),
                render: (r: Absence) => {
                  const d = daysBetween(r.start_date, r.end_date)
                  return `${d} jour${d > 1 ? 's' : ''}`
                },
              },
              {
                key: 'status',
                header: t('common.status', 'Statut'),
                render: (r: Absence) => <StatusBadge status={r.status} />,
              },
              {
                key: 'notes',
                header: t('common.notes', 'Notes'),
                render: (r: Absence) => <span className="text-slate-400">{r.notes ?? '---'}</span>,
              },
              {
                key: 'actions',
                header: '',
                width: '60px',
                render: (r: Absence) =>
                  r.status === 'pending' ? (
                    <button
                      onClick={() => cancelMutation.mutate(r.absence_id)}
                      disabled={cancelMutation.isPending}
                      className="p-1.5 rounded-lg hover:bg-red-50 text-red-400 disabled:opacity-50">
                      <X size={13} />
                    </button>
                  ) : null,
              },
            ]}
            data={absences}
          />
        )}
      </Card>

      <Modal open={modal} onClose={() => setModal(false)} title={t('absences.declare', 'Declarer une absence')} size="md">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">{t('common.type', 'Type')} *</label>
            <select value={form.absence_type} onChange={e => set('absence_type', e.target.value)}
              className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <option value="cp">{t('absences.cp', 'Conge paye')}</option>
              <option value="maladie">{t('absences.sick', 'Maladie')}</option>
              <option value="autre">{t('absences.other', 'Autre')}</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">{t('absences.start', 'Debut')} *</label>
              <input type="date" value={form.start_date} onChange={e => set('start_date', e.target.value)} required
                className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">{t('absences.end', 'Fin')} *</label>
              <input type="date" value={form.end_date} onChange={e => set('end_date', e.target.value)} required
                min={form.start_date}
                className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">{t('common.notes', 'Notes')}</label>
            <textarea rows={3} value={form.notes} onChange={e => set('notes', e.target.value)}
              className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder={t('absences.additionalInfoPlaceholder', 'Informations complémentaires...')} />
          </div>
          {apiError && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              <AlertTriangle size={15} className="flex-shrink-0 mt-0.5" />{apiError}
            </div>
          )}
          <div className="flex gap-3 justify-end pt-2">
            <Button variant="secondary" type="button" onClick={() => setModal(false)}>{t('common.cancel', 'Annuler')}</Button>
            <Button type="submit" loading={createMutation.isPending}>{t('absences.submit', 'Soumettre')}</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Modal from '../ui/Modal'
import Button from '../ui/Button'
import { useCreateAbsence } from '../../features/absences/hooks'
import { ApiError } from '../../lib/apiClient'

interface TimeOffRequestModalProps {
  open: boolean
  onClose: () => void
}

function getTypeLabels(t: any): Record<string, string> {
  return {
    cp: t('absenceTypes.cp', 'Congé payé'),
    maladie: t('absenceTypes.sick', 'Maladie'),
    autre: t('absenceTypes.other', 'Autre'),
  }
}

export default function TimeOffRequestModal({ open, onClose }: TimeOffRequestModalProps) {
  const { t } = useTranslation()
  const createMutation = useCreateAbsence()
  const [form, setForm] = useState({ absence_type: 'cp', start_date: '', end_date: '', notes: '' })
  const [apiError, setApiError] = useState<string | null>(null)
  const TYPE_LABELS = getTypeLabels(t)

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
      onClose()
      setForm({ absence_type: 'cp', start_date: '', end_date: '', notes: '' })
    } catch (err) {
      setApiError(err instanceof ApiError ? err.message : t('timeOffRequest.error', 'Erreur inattendue.'))
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t('absences.declare', 'Déclarer une absence')} size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">
            {t('common.type', 'Type')} *
          </label>
          <select value={form.absence_type} onChange={e => set('absence_type', e.target.value)}
            className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white">
            <option value="cp">{TYPE_LABELS.cp}</option>
            <option value="maladie">{TYPE_LABELS.maladie}</option>
            <option value="autre">{TYPE_LABELS.autre}</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">
              {t('absences.start', 'Début')} *
            </label>
            <input type="date" value={form.start_date} onChange={e => set('start_date', e.target.value)} required
              className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">
              {t('absences.end', 'Fin')} *
            </label>
            <input type="date" value={form.end_date} onChange={e => set('end_date', e.target.value)} required
              min={form.start_date}
              className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white" />
          </div>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-1.5">
            {t('common.notes', 'Notes')}
          </label>
          <textarea rows={3} value={form.notes} onChange={e => set('notes', e.target.value)}
            className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
            placeholder={t('timeOffRequest.informationPlaceholder', 'Informations complémentaires...')} />
        </div>
        {apiError && (
          <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-400">
            <AlertTriangle size={15} className="flex-shrink-0 mt-0.5" />{apiError}
          </div>
        )}
        <div className="flex gap-3 justify-end pt-2">
          <Button variant="secondary" type="button" onClick={onClose}>{t('common.cancel', 'Annuler')}</Button>
          <Button type="submit" loading={createMutation.isPending}>{t('absences.submit', 'Soumettre')}</Button>
        </div>
      </form>
    </Modal>
  )
}

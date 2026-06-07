import { useState } from 'react'
import { X, Clock, ChevronDown } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface QuickTimeEntryModalProps {
  open: boolean
  onClose: () => void
  date?: string
}

export default function QuickTimeEntryModal({ open, onClose, date }: QuickTimeEntryModalProps) {
  const { t } = useTranslation()
  const [workDate, setWorkDate] = useState(date || new Date().toISOString().split('T')[0])
  const [startTime, setStartTime] = useState('09:00')
  const [endTime, setEndTime] = useState('17:00')
  const [duration, setDuration] = useState('8:00')
  const [project, setProject] = useState('')
  const [details, setDetails] = useState('')
  const [billable, setBillable] = useState(true)
  const [showMoreProps, setShowMoreProps] = useState(false)

  if (!open) return null

  const calculateDuration = (start: string, end: string) => {
    if (!start || !end) return '0:00'
    const [startH, startM] = start.split(':').map(Number)
    const [endH, endM] = end.split(':').map(Number)
    const totalMinutes = (endH * 60 + endM) - (startH * 60 + startM)
    const hours = Math.floor(totalMinutes / 60)
    const minutes = totalMinutes % 60
    return `${hours}:${minutes.toString().padStart(2, '0')}`
  }

  const handleStartTimeChange = (value: string) => {
    setStartTime(value)
    setDuration(calculateDuration(value, endTime))
  }

  const handleEndTimeChange = (value: string) => {
    setEndTime(value)
    setDuration(calculateDuration(startTime, value))
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-white">
            {t('timeEntry.addEntry', 'Ajouter entrée de temps')}
          </h2>
          <div className="flex items-center gap-2">
            <button aria-label="Avatar" className="w-9 h-9 flex items-center justify-center rounded-lg bg-pink-500 hover:bg-pink-600 transition-colors text-white">
              <span className="text-sm font-bold">A</span>
            </button>
            <button onClick={onClose} aria-label="Fermer" className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-600 dark:text-slate-400">
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          <div className="space-y-5">
            {/* Date */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                <Clock size={16} className="text-slate-400" />
                {workDate ? new Date(workDate).toLocaleDateString('fr-FR', { weekday: 'short', month: 'short', day: 'numeric' }) : 'Date'}
              </label>
              <input
                type="date"
                value={workDate}
                onChange={e => setWorkDate(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            {/* Time Range */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                {t('timeEntry.workedHours', 'Heures travaillées')}
              </label>
              <div className="grid grid-cols-3 gap-3">
                <div className="relative">
                  <Clock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="time"
                    value={startTime}
                    onChange={e => handleStartTimeChange(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg pl-10 pr-3 py-2.5 text-sm text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
                <div className="flex items-center justify-center text-slate-400">—</div>
                <div className="relative">
                  <Clock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="time"
                    value={endTime}
                    onChange={e => handleEndTimeChange(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg pl-10 pr-3 py-2.5 text-sm text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <Clock size={14} className="text-slate-400" />
                <span className="text-sm text-slate-600">{duration}</span>
              </div>
            </div>

            {/* Project & Task */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                {t('timeEntry.projectAndTask', 'Projet et tâche')}
              </label>
              <div className="space-y-3">
                <div className="relative">
                  <input
                    type="text"
                    value={project}
                    onChange={e => setProject(e.target.value)}
                    placeholder={t('timeEntry.noProject', 'No Project')}
                    className="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
                <button className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-800 transition-colors">
                  <span>+</span>
                  {t('timeEntry.selectTask', 'Sélectionner une tâche')}
                </button>
              </div>
            </div>

            {/* Details */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                {t('timeEntry.details', 'Détails')}
              </label>
              <textarea
                value={details}
                onChange={e => setDetails(e.target.value)}
                rows={3}
                className="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                placeholder={t('timeEntry.detailsPlaceholder', 'Ajoutez quelques détails')}
              />
            </div>

            {/* More Properties */}
            <button
              onClick={() => setShowMoreProps(!showMoreProps)}
              className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-800 transition-colors"
            >
              <ChevronDown size={16} className={`transition-transform ${showMoreProps ? 'rotate-180' : ''}`} />
              {t('timeEntry.moreProperties', 'Plus de propriétés')}
            </button>

            {showMoreProps && (
              <div className="space-y-4 pt-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-700">{t('timeEntry.billable', 'Facturable')}</span>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={billable}
                      onChange={e => setBillable(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-2 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-slate-600">
                      {billable ? t('timeEntry.billable', 'Facturable') : t('timeEntry.nonBillable', 'Non facturé')}
                    </span>
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 dark:border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 transition-colors">
            {t('common.cancel', 'Annuler')}
          </button>
          <div className="flex items-center gap-2">
            <button className="px-6 py-2 text-sm font-medium text-white bg-slate-700 hover:bg-slate-800 rounded-lg transition-colors">
              {t('timeEntry.log', 'LOG')}
            </button>
            <button className="p-2 text-slate-600 hover:text-slate-800 transition-colors">
              <ChevronDown size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

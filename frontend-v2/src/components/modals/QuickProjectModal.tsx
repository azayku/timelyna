import { useState } from 'react'
import { X, Calendar } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface QuickProjectModalProps {
  open: boolean
  onClose: () => void
}

export default function QuickProjectModal({ open, onClose }: QuickProjectModalProps) {
  const { t } = useTranslation()
  const [name, setName] = useState('')
  const [code, setCode] = useState(false)
  const [estimatedTime, setEstimatedTime] = useState('0:00')
  const [dueDate, setDueDate] = useState('')
  const [advancedViews, setAdvancedViews] = useState(false)
  const [activeTab, setActiveTab] = useState<'properties' | 'billing' | 'privacy'>('privacy')
  const [visibility, setVisibility] = useState('private')

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-white">
            {t('project.addProject', 'Ajouter un projet')}
          </h2>
          <button onClick={onClose} aria-label="Fermer" className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-600 dark:text-slate-400">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          <div className="space-y-5">
            {/* Name */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  {t('project.name', 'Nom')}
                </label>
                <button
                  onClick={() => setCode(!code)}
                  className="text-sm text-indigo-600 hover:text-indigo-700 transition-colors"
                >
                  {t('project.addCode', 'Ajouter du code')}
                </button>
              </div>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder={t('project.namePlaceholder', 'Nom du projet')}
              />
            </div>

            {/* Time & Date */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  {t('project.estimatedTime', 'Temps estimé')}
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={estimatedTime}
                    onChange={e => setEstimatedTime(e.target.value)}
                    className="flex-1 bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                    <input type="checkbox" className="w-4 h-4 rounded border-slate-300 dark:border-slate-600 text-indigo-600 dark:bg-slate-700" />
                    {t('project.sumTasks', 'Estimation des tâches de somme')}
                  </label>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  {t('project.dueDate', "Date d'échéance")}
                </label>
                <div className="relative">
                  <Calendar size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="date"
                    value={dueDate}
                    onChange={e => setDueDate(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg pl-10 pr-3 py-2.5 text-sm text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder={t('project.dueDatePlaceholder', "Date d'échéance")}
                  />
                </div>
              </div>
            </div>

            {/* Advanced Views */}
            <div>
              <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={advancedViews}
                  onChange={e => setAdvancedViews(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-300 dark:border-slate-600 text-indigo-600 dark:bg-slate-700 focus:ring-2 focus:ring-indigo-500"
                />
                {t('project.advancedViews', 'Vues avancées des tâches')}
              </label>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 ml-6">
                {t('project.advancedViewsDesc', 'Activer le tableau, les listes de tâches, les sous-tâches et la collaboration.')}
              </p>
            </div>

            {/* Tabs */}
            <div className="border-b border-slate-200 dark:border-slate-700">
              <div className="flex gap-6">
                <button
                  onClick={() => setActiveTab('properties')}
                  className={`pb-3 text-sm font-medium transition-colors ${
                    activeTab === 'properties'
                      ? 'text-indigo-600 border-b-2 border-indigo-600'
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  {t('project.properties', 'Propriétés')}
                </button>
                <button
                  onClick={() => setActiveTab('billing')}
                  className={`pb-3 text-sm font-medium transition-colors ${
                    activeTab === 'billing'
                      ? 'text-indigo-600 border-b-2 border-indigo-600'
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  {t('project.billing', 'Facturation')}
                </button>
                <button
                  onClick={() => setActiveTab('privacy')}
                  className={`pb-3 text-sm font-medium transition-colors ${
                    activeTab === 'privacy'
                      ? 'text-indigo-600 border-b-2 border-indigo-600'
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  {t('project.privacy', 'Confidentialité (Privé)')}
                </button>
              </div>
            </div>

            {/* Tab Content - Privacy */}
            {activeTab === 'privacy' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                    {t('project.whoCanSee', 'Qui peut voir ce projet ?')}
                  </label>
                  <select
                    value={visibility}
                    onChange={e => setVisibility(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="private">{t('project.private', 'Privé (uniquement les administrateurs et les chefs de projet)')}</option>
                    <option value="team">{t('project.team', 'Équipe')}</option>
                    <option value="public">{t('project.public', 'Public')}</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                    {t('project.usersWithAccess', 'Utilisateurs ayant accès à tous les projets')}
                  </label>
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-pink-500 flex items-center justify-center text-white text-sm font-bold">
                      A
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200">ds ff</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 dark:border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 transition-colors">
            {t('common.cancel', 'ANNULER')}
          </button>
          <button className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors">
            {t('common.save', 'ENREGISTRER')}
          </button>
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { Star, Trash2, BookmarkPlus, ChevronDown } from 'lucide-react'
import {
  useMyTemplates,
  useCreateTemplate,
  useDeleteTemplate,
  useUpdateTemplate,
} from '../features/entry-templates/hooks'
import type { EntryTemplate } from '../features/entry-templates/api'

interface TemplateSelectorProps {
  onApply: (template: EntryTemplate) => void
  currentData?: {
    project_id?: number
    task_type?: string
    description?: string
    hours_worked?: number
  }
}

export default function TemplateSelector({ onApply, currentData }: TemplateSelectorProps) {
  const { data: templates = [] } = useMyTemplates()
  const createMutation = useCreateTemplate()
  const deleteMutation = useDeleteTemplate()
  const updateMutation = useUpdateTemplate()
  const [isOpen, setIsOpen] = useState(false)
  const [saveMode, setSaveMode] = useState(false)
  const [newName, setNewName] = useState('')

  const favorites = templates.filter(t => t.is_favorite)
  const others = templates.filter(t => !t.is_favorite)

  const handleSave = async () => {
    if (!newName.trim() || !currentData) return
    await createMutation.mutateAsync({
      name: newName.trim(),
      project_id: currentData.project_id,
      task_type: currentData.task_type,
      description: currentData.description,
      default_hours: currentData.hours_worked,
    })
    setNewName('')
    setSaveMode(false)
  }

  const handleToggleFavorite = (tpl: EntryTemplate) => {
    updateMutation.mutate({ id: tpl.template_id, data: { is_favorite: !tpl.is_favorite } })
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors bg-white dark:bg-slate-800"
      >
        <BookmarkPlus className="h-4 w-4" />
        Templates
        <ChevronDown className={`h-3 w-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute left-0 top-full mt-1 w-72 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg z-50">
          <div className="p-3 border-b border-slate-100 dark:border-slate-700">
            {saveMode ? (
              <div className="flex gap-2">
                <input
                  autoFocus
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleSave()
                    if (e.key === 'Escape') setSaveMode(false)
                  }}
                  placeholder="Nom du template..."
                  className="flex-1 border border-slate-300 dark:border-slate-600 rounded-lg px-2 py-1 text-sm bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={handleSave}
                  disabled={!newName.trim() || createMutation.isPending}
                  className="px-2 py-1 bg-indigo-600 text-white rounded-lg text-xs disabled:opacity-50"
                >
                  OK
                </button>
              </div>
            ) : (
              <button
                onClick={() => setSaveMode(true)}
                className="w-full flex items-center gap-2 text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 font-medium"
              >
                <BookmarkPlus className="h-4 w-4" />
                Sauvegarder comme template
              </button>
            )}
          </div>

          <div className="max-h-64 overflow-y-auto">
            {templates.length === 0 && (
              <p className="text-center text-xs text-slate-400 py-4">Aucun template sauvegardé</p>
            )}

            {favorites.length > 0 && (
              <div className="px-3 pt-2 pb-1">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">
                  Favoris
                </p>
                {favorites.map(tpl => (
                  <TemplateItem
                    key={tpl.template_id}
                    template={tpl}
                    onApply={() => {
                      onApply(tpl)
                      setIsOpen(false)
                    }}
                    onDelete={() => deleteMutation.mutate(tpl.template_id)}
                    onToggleFavorite={() => handleToggleFavorite(tpl)}
                  />
                ))}
              </div>
            )}

            {others.length > 0 && (
              <div className="px-3 pt-2 pb-2">
                {favorites.length > 0 && (
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">
                    Autres
                  </p>
                )}
                {others.map(tpl => (
                  <TemplateItem
                    key={tpl.template_id}
                    template={tpl}
                    onApply={() => {
                      onApply(tpl)
                      setIsOpen(false)
                    }}
                    onDelete={() => deleteMutation.mutate(tpl.template_id)}
                    onToggleFavorite={() => handleToggleFavorite(tpl)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function TemplateItem({
  template,
  onApply,
  onDelete,
  onToggleFavorite,
}: {
  template: EntryTemplate
  onApply: () => void
  onDelete: () => void
  onToggleFavorite: () => void
}) {
  return (
    <div className="flex items-center gap-1 group py-1">
      <button
        onClick={onApply}
        className="flex-1 text-left text-sm text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 truncate"
      >
        {template.name}
        {template.default_hours && (
          <span className="text-xs text-slate-400 ml-1">({template.default_hours}h)</span>
        )}
      </button>
      <button
        onClick={onToggleFavorite}
        aria-label={template.is_favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'}
        className={`p-1 rounded ${
          template.is_favorite ? 'text-amber-400' : 'text-slate-300 hover:text-amber-400'
        }`}
      >
        <Star className="h-3 w-3" fill={template.is_favorite ? 'currentColor' : 'none'} />
      </button>
      <button
        onClick={onDelete}
        aria-label="Supprimer le template"
        className="p-1 rounded text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <Trash2 className="h-3 w-3" />
      </button>
    </div>
  )
}

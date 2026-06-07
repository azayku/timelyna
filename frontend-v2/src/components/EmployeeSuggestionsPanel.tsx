import { useQuery } from '@tanstack/react-query'
import { UserPlus, Star, Building2, Loader2, AlertTriangle, Users } from 'lucide-react'
import { fetchSuggestedEmployees } from '../features/projects/suggestionsApi'
import Avatar from './ui/Avatar'

// Stable badge colors cycling by skill name hash
const SKILL_COLORS = [
  'bg-blue-100 text-blue-700',
  'bg-green-100 text-green-700',
  'bg-yellow-100 text-yellow-700',
  'bg-pink-100 text-pink-700',
  'bg-orange-100 text-orange-700',
  'bg-purple-100 text-purple-700',
  'bg-indigo-100 text-indigo-700',
  'bg-red-100 text-red-700',
]

function colorForSkill(name: string) {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0
  return SKILL_COLORS[hash % SKILL_COLORS.length]
}

interface Props {
  projectId: number
  onAddToTeam: (employeeId: number) => void
  /** IDs already added to the team — used to disable the button */
  addedIds?: Set<number>
}

export default function EmployeeSuggestionsPanel({
  projectId,
  onAddToTeam,
  addedIds = new Set(),
}: Props) {
  const { data: suggestions = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['suggested-employees', projectId],
    queryFn: () => fetchSuggestedEmployees(projectId),
    enabled: projectId > 0,
  })

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-6 justify-center text-slate-400 text-sm">
        <Loader2 size={15} className="animate-spin" />
        Analyse des disponibilités…
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center gap-2 py-6 text-center">
        <AlertTriangle size={18} className="text-red-400" />
        <p className="text-sm text-red-500">Impossible de charger les suggestions.</p>
        <button
          onClick={() => refetch()}
          className="text-xs text-indigo-600 hover:underline"
        >
          Réessayer
        </button>
      </div>
    )
  }

  if (suggestions.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-8 text-center">
        <Users size={24} className="text-slate-300" />
        <p className="text-sm text-slate-400">
          Aucun employé disponible avec les compétences requises.
        </p>
        <p className="text-xs text-slate-400">
          Vérifiez les compétences requises du projet ou les disponibilités de l'équipe.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <Star size={14} className="text-indigo-500" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            Employés suggérés
          </span>
        </div>
        <span className="text-xs text-slate-400">
          {suggestions.length} correspondance{suggestions.length > 1 ? 's' : ''}
          {' · '}triées par compétences
        </span>
      </div>

      {/* List */}
      <div className="space-y-2 max-h-72 overflow-y-auto pr-0.5">
        {suggestions.map(s => {
          const alreadyAdded = addedIds.has(s.employee_id)
          return (
            <div
              key={s.employee_id}
              className={`flex items-start gap-3 p-3 rounded-xl border transition-colors ${
                alreadyAdded
                  ? 'border-emerald-200 bg-emerald-50'
                  : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              {/* Avatar */}
              <Avatar name={s.full_name} size="sm" />

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-semibold text-slate-800 truncate">
                    {s.full_name}
                  </span>
                  {/* Match count badge */}
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700 flex-shrink-0">
                    <Star size={9} />
                    {s.matching_skill_count}
                  </span>
                </div>

                {/* Org */}
                <div className="flex items-center gap-1 mt-0.5 text-xs text-slate-400">
                  <Building2 size={10} />
                  {s.org_name}
                </div>

                {/* Matching skill badges */}
                {s.matching_skills.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {s.matching_skills.map(skill => (
                      <span
                        key={skill}
                        className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${colorForSkill(skill)}`}
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Add button */}
              <button
                onClick={() => !alreadyAdded && onAddToTeam(s.employee_id)}
                disabled={alreadyAdded}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium flex-shrink-0 transition-colors ${
                  alreadyAdded
                    ? 'bg-emerald-100 text-emerald-700 cursor-default'
                    : 'bg-indigo-600 text-white hover:bg-indigo-700'
                }`}
                title={alreadyAdded ? 'Déjà dans l\'équipe' : 'Ajouter à l\'équipe'}
              >
                <UserPlus size={12} />
                {alreadyAdded ? 'Ajouté' : 'Ajouter'}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}

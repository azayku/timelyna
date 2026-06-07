import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, X, Star, AlertTriangle, Loader2 } from 'lucide-react'
import {
  fetchEmployeeSkills,
  addEmployeeSkill,
  removeEmployeeSkill,
  fetchSkillRates,
} from '../features/employees/skillsApi'
import { ApiError } from '../lib/apiClient'

// Stable color palette cycling by skill_rate_id
const BADGE_COLORS = [
  'bg-blue-100 text-blue-700',
  'bg-green-100 text-green-700',
  'bg-yellow-100 text-yellow-700',
  'bg-pink-100 text-pink-700',
  'bg-orange-100 text-orange-700',
  'bg-purple-100 text-purple-700',
  'bg-indigo-100 text-indigo-700',
  'bg-red-100 text-red-700',
]

function skillColor(skillRateId: number) {
  return BADGE_COLORS[skillRateId % BADGE_COLORS.length]
}

interface Props {
  employeeId: number
}

export default function EmployeeSkillsPanel({ employeeId }: Props) {
  const qc = useQueryClient()
  const [selectedSkillRateId, setSelectedSkillRateId] = useState<number | ''>('')
  const [addError, setAddError] = useState<string | null>(null)

  // ── Queries ──────────────────────────────────────────────────────────────
  const {
    data: skills = [],
    isLoading: loadingSkills,
    isError: errorSkills,
  } = useQuery({
    queryKey: ['employee-skills', employeeId],
    queryFn: () => fetchEmployeeSkills(employeeId),
    enabled: employeeId > 0,
  })

  const {
    data: allRates = [],
    isLoading: loadingRates,
  } = useQuery({
    queryKey: ['skill-rates'],
    queryFn: fetchSkillRates,
  })

  // ── Mutations ─────────────────────────────────────────────────────────────
  const addMutation = useMutation({
    mutationFn: (skillRateId: number) => addEmployeeSkill(employeeId, skillRateId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employee-skills', employeeId] })
      setSelectedSkillRateId('')
      setAddError(null)
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        if (err.code === 'skill_already_assigned') {
          setAddError('Cette compétence est déjà assignée à cet employé.')
        } else if (err.code === 'skill_org_mismatch') {
          setAddError('Cette compétence n\'appartient pas à la même organisation que l\'employé.')
        } else {
          setAddError(err.message)
        }
      } else {
        setAddError('Une erreur inattendue est survenue.')
      }
    },
  })

  const removeMutation = useMutation({
    mutationFn: (skillRateId: number) => removeEmployeeSkill(employeeId, skillRateId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employee-skills', employeeId] })
    },
  })

  // ── Derived ───────────────────────────────────────────────────────────────
  const assignedIds = new Set(skills.map(s => s.skill_rate_id))
  const availableRates = allRates.filter(r => !assignedIds.has(r.id))

  const handleAdd = () => {
    if (selectedSkillRateId === '') return
    setAddError(null)
    addMutation.mutate(Number(selectedSkillRateId))
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Star size={14} className="text-indigo-500" />
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
          Compétences
        </h3>
      </div>

      {/* Current skills */}
      {loadingSkills ? (
        <div className="flex items-center gap-2 text-slate-400 text-xs py-2">
          <Loader2 size={13} className="animate-spin" />
          Chargement…
        </div>
      ) : errorSkills ? (
        <div className="flex items-center gap-1.5 text-red-500 text-xs">
          <AlertTriangle size={13} />
          Impossible de charger les compétences.
        </div>
      ) : skills.length === 0 ? (
        <p className="text-xs text-slate-400 italic">Aucune compétence assignée.</p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {skills.map(skill => (
            <span
              key={skill.id}
              className={`inline-flex items-center gap-1 pl-2.5 pr-1 py-0.5 rounded-full text-xs font-medium ${skillColor(skill.skill_rate_id)}`}
            >
              {skill.skill_name}
              <button
                onClick={() => removeMutation.mutate(skill.skill_rate_id)}
                disabled={removeMutation.isPending}
                className="w-4 h-4 rounded-full flex items-center justify-center hover:bg-black/10 transition-colors disabled:opacity-50"
                title="Retirer cette compétence"
              >
                <X size={10} />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Add skill row */}
      <div className="flex items-center gap-2 pt-1">
        <select
          value={selectedSkillRateId}
          onChange={e =>
            setSelectedSkillRateId(e.target.value === '' ? '' : Number(e.target.value))
          }
          disabled={loadingRates || availableRates.length === 0}
          className="flex-1 border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-slate-50 disabled:text-slate-400"
        >
          <option value="">
            {loadingRates
              ? 'Chargement…'
              : availableRates.length === 0
              ? 'Toutes les compétences assignées'
              : '+ Ajouter une compétence…'}
          </option>
          {availableRates.map(r => (
            <option key={r.id} value={r.id}>
              {r.skill_name}
            </option>
          ))}
        </select>
        <button
          onClick={handleAdd}
          disabled={selectedSkillRateId === '' || addMutation.isPending}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {addMutation.isPending ? (
            <Loader2 size={12} className="animate-spin" />
          ) : (
            <Plus size={12} />
          )}
          Ajouter
        </button>
      </div>

      {/* Add error */}
      {addError && (
        <div className="flex items-start gap-1.5 text-xs text-red-600">
          <AlertTriangle size={12} className="flex-shrink-0 mt-0.5" />
          {addError}
        </div>
      )}
    </div>
  )
}

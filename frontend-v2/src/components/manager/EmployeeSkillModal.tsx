import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Plus, Trash2, Star, Building2, Calendar } from 'lucide-react'
import { apiClient } from '../../lib/apiClient'
import { swalDark, swalConfirm } from '../../lib/swalConfig'

interface TeamMember {
  employee_id: number
  first_name: string
  last_name: string
  email: string
  hire_date: string | null
  organization_name: string
  skills: string[]
}

interface SkillRateItem {
  id: number
  skill_name: string
}

interface EmployeeSkillDetail {
  id: number
  skill_rate_id: number
  skill_name: string
}

interface Props {
  member: TeamMember
  onClose: () => void
}

export default function EmployeeSkillModal({ member, onClose }: Props) {
  const qc = useQueryClient()
  const [selectedRateId, setSelectedRateId] = useState<number | ''>('')

  // Current skills with IDs (for delete)
  const { data: skills = [], isLoading: loadingSkills } = useQuery({
    queryKey: ['manager-employee-skills', member.employee_id],
    queryFn: () => apiClient.get<EmployeeSkillDetail[]>(`/manager/employees/${member.employee_id}/skills`),
  })

  // All available skill rates
  const { data: allRates = [] } = useQuery({
    queryKey: ['manager-skill-rates'],
    queryFn: () => apiClient.get<SkillRateItem[]>('/manager/skill-rates'),
  })

  // Rates not yet assigned
  const assignedIds = new Set(skills.map(s => s.skill_rate_id))
  const availableRates = allRates.filter(r => !assignedIds.has(r.id))

  const addMutation = useMutation({
    mutationFn: (skill_rate_id: number) =>
      apiClient.post(`/manager/employees/${member.employee_id}/skills`, { skill_rate_id }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['manager-employee-skills', member.employee_id] })
      qc.invalidateQueries({ queryKey: ['manager-team'] })
      setSelectedRateId('')
    },
    onError: () => {
      swalDark({ icon: 'error', title: 'Erreur', text: 'Impossible d\'ajouter la compétence.', timer: 2500, showConfirmButton: false })
    },
  })

  const removeMutation = useMutation({
    mutationFn: (skill_rate_id: number) =>
      apiClient.delete(`/manager/employees/${member.employee_id}/skills/${skill_rate_id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['manager-employee-skills', member.employee_id] })
      qc.invalidateQueries({ queryKey: ['manager-team'] })
    },
    onError: () => {
      swalDark({ icon: 'error', title: 'Erreur', text: 'Impossible de supprimer la compétence.', timer: 2500, showConfirmButton: false })
    },
  })

  const handleAdd = () => {
    if (selectedRateId !== '') addMutation.mutate(Number(selectedRateId))
  }

  const handleRemove = async (skill: EmployeeSkillDetail) => {
    const result = await swalConfirm({
      title: 'Supprimer la compétence ?',
      text: `Retirer "${skill.skill_name}" de ${member.first_name} ${member.last_name} ?`,
      icon: 'warning',
      confirmButtonColor: '#ef4444',
      cancelButtonColor: '#64748b',
      confirmButtonText: 'Supprimer',
      cancelButtonText: 'Annuler',
    })
    if (result.isConfirmed) removeMutation.mutate(skill.skill_rate_id)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-lg flex flex-col max-h-[90vh]"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center shrink-0">
              <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">
                {member.first_name?.[0] ?? '?'}{member.last_name?.[0] ?? ''}
              </span>
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-800 dark:text-white">
                {member.first_name} {member.last_name}
              </h2>
              <p className="text-xs text-slate-400 dark:text-slate-500">{member.email}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 p-5 space-y-5">
          {/* Info */}
          <div className="flex flex-wrap gap-3 text-xs text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1.5">
              <Building2 size={12} />
              {member.organization_name}
            </span>
            {member.hire_date && (
              <span className="flex items-center gap-1.5">
                <Calendar size={12} />
                Depuis le {new Date(member.hire_date).toLocaleDateString('fr-FR')}
              </span>
            )}
          </div>

          {/* Current skills */}
          <section>
            <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
              <Star size={12} />
              Compétences ({skills.length})
            </h3>
            {loadingSkills ? (
              <div className="flex justify-center py-6">
                <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : skills.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-slate-500 italic">Aucune compétence assignée.</p>
            ) : (
              <div className="space-y-2">
                {skills.map(skill => (
                  <div key={skill.id} className="flex items-center justify-between bg-slate-50 dark:bg-slate-800 rounded-lg px-3 py-2">
                    <span className="text-sm text-slate-800 dark:text-slate-200 font-medium">{skill.skill_name}</span>
                    <button
                      onClick={() => handleRemove(skill)}
                      disabled={removeMutation.isPending}
                      className="p-1 rounded text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-40"
                      title="Supprimer"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Add skill */}
          <section>
            <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-3">
              Ajouter une compétence
            </h3>
            {availableRates.length === 0 && !loadingSkills ? (
              <p className="text-sm text-slate-400 dark:text-slate-500 italic">Toutes les compétences disponibles sont déjà assignées.</p>
            ) : (
              <div className="flex gap-2">
                <select
                  value={selectedRateId}
                  onChange={e => setSelectedRateId(e.target.value === '' ? '' : Number(e.target.value))}
                  className="flex-1 px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Sélectionner une compétence…</option>
                  {availableRates.map(r => (
                    <option key={r.id} value={r.id}>{r.skill_name}</option>
                  ))}
                </select>
                <button
                  onClick={handleAdd}
                  disabled={selectedRateId === '' || addMutation.isPending}
                  className="flex items-center gap-1.5 px-3 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  <Plus size={15} />
                  Ajouter
                </button>
              </div>
            )}
          </section>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-700 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors">
            Fermer
          </button>
        </div>
      </div>
    </div>
  )
}

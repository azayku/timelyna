import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, Clock, TrendingUp, Calendar, FileText } from 'lucide-react'
import Modal from '../ui/Modal'
import { AvatarGroup } from '../ui/Avatar'
import EmployeeSuggestionsPanel from '../EmployeeSuggestionsPanel'
import { apiClient } from '../../lib/apiClient'

export interface Project {
  id: number
  code: string
  name: string
  client: string
  status: string
  budget: number
  billingRate: number
  team: number
  teamMembers?: string[]
  start: string
  end: string | null
  hoursLogged?: number
  revenue?: number
  description?: string
}

interface Props {
  project: Project | null
  onClose: () => void
  onTeamUpdated?: () => void
}

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-700',
  planning: 'bg-blue-100 text-blue-700',
  completed: 'bg-slate-100 text-slate-600',
  draft: 'bg-amber-100 text-amber-700',
  paused: 'bg-orange-100 text-orange-700',
  cancelled: 'bg-red-100 text-red-700',
}

export default function ProjectDetailModal({ project, onClose, onTeamUpdated }: Props) {
  const queryClient = useQueryClient()
  const [addedIds, setAddedIds] = useState<Set<number>>(new Set())

  const addToTeamMutation = useMutation({
    mutationFn: (employeeId: number) =>
      apiClient.put(`/admin/projects/${project!.id}/team`, {
        employee_ids: [employeeId],
      }),
    onSuccess: (_data, employeeId) => {
      setAddedIds(prev => new Set([...prev, employeeId]))
      queryClient.invalidateQueries({ queryKey: ['suggested-employees', project?.id] })
      onTeamUpdated?.()
    },
  })

  if (!project) return null

  const budgetPct = project.hoursLogged && project.budget
    ? Math.round((project.hoursLogged / project.budget) * 100)
    : 0

  return (
    <Modal open={!!project} onClose={onClose} title={project.name} size="xl">
      <div className="space-y-5">
        <div className="flex items-start gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                {project.code}
              </span>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_COLORS[project.status] ?? 'bg-slate-100 text-slate-600'}`}>
                {project.status}
              </span>
            </div>
            <p className="text-sm text-slate-500">{project.client}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { icon: <Clock size={15} className="text-indigo-500" />, label: 'Heures loggées', value: `${project.hoursLogged ?? 0}h`, bg: 'bg-indigo-50' },
            { icon: <TrendingUp size={15} className="text-emerald-500" />, label: 'CA généré', value: `${(project.revenue ?? 0).toLocaleString('fr-FR')} €`, bg: 'bg-emerald-50' },
            { icon: <Users size={15} className="text-blue-500" />, label: 'Équipe', value: `${project.team} membre${project.team > 1 ? 's' : ''}`, bg: 'bg-blue-50' },
            { icon: <FileText size={15} className="text-amber-500" />, label: 'Budget', value: `${project.budget}h`, bg: 'bg-amber-50' },
          ].map(kpi => (
            <div key={kpi.label} className={`${kpi.bg} rounded-xl p-3`}>
              <div className="flex items-center gap-2 mb-1">
                {kpi.icon}
                <span className="text-xs text-slate-500">{kpi.label}</span>
              </div>
              <p className="text-lg font-bold text-slate-800">{kpi.value}</p>
            </div>
          ))}
        </div>

        {project.hoursLogged !== undefined && (
          <div>
            <div className="flex justify-between text-xs text-slate-500 mb-1">
              <span>Avancement budget</span>
              <span className={budgetPct > 90 ? 'text-red-600 font-semibold' : ''}>{budgetPct}%</span>
            </div>
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${budgetPct > 90 ? 'bg-red-500' : budgetPct > 70 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                style={{ width: `${Math.min(budgetPct, 100)}%` }}
              />
            </div>
          </div>
        )}

        <div className="flex items-center gap-4 text-sm text-slate-500">
          <div className="flex items-center gap-1.5">
            <Calendar size={14} />
            <span>Début : <strong className="text-slate-700">{project.start}</strong></span>
          </div>
          {project.end && (
            <div className="flex items-center gap-1.5">
              <Calendar size={14} />
              <span>Fin : <strong className="text-slate-700">{project.end}</strong></span>
            </div>
          )}
        </div>

        {project.description && (
          <p className="text-sm text-slate-600 bg-slate-50 rounded-xl p-3">{project.description}</p>
        )}

        {project.teamMembers && project.teamMembers.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Équipe actuelle</p>
            <AvatarGroup names={project.teamMembers} max={8} size="sm" />
          </div>
        )}

        <div className="border border-slate-100 rounded-xl p-4">
          <EmployeeSuggestionsPanel
            projectId={project.id}
            onAddToTeam={(employeeId) => addToTeamMutation.mutate(employeeId)}
            addedIds={addedIds}
          />
        </div>
      </div>
    </Modal>
  )
}

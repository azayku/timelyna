import { useQuery } from '@tanstack/react-query'
import { X, Building2, MapPin, Clock, TrendingUp, Calendar, Users, Star, FileText } from 'lucide-react'
import { apiClient } from '../../lib/apiClient'

interface ProjectTeamMember {
  employee_id: number
  first_name: string
  last_name: string
  email: string
  skills: string[]
}

interface ProjectDetail {
  project_id: number
  project_name: string
  project_code: string
  description: string | null
  client_name: string
  client_address: string | null
  status: string
  start_date: string
  end_date: string | null
  budget_hours: number | null
  budget_amount: number | null
  hours_consumed: number
  budget_percent: number | null
  team_members: ProjectTeamMember[]
}

const STATUS_STYLES: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
  planning: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  draft: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  completed: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  archived: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
}

function BudgetBar({ percent }: { percent: number | null }) {
  if (percent === null) return <span className="text-slate-400 dark:text-slate-500 text-sm">—</span>
  const color =
    percent >= 90 ? 'bg-red-500' : percent >= 70 ? 'bg-orange-400' : 'bg-emerald-500'
  const textColor =
    percent >= 90
      ? 'text-red-600 dark:text-red-400'
      : percent >= 70
        ? 'text-orange-600 dark:text-orange-400'
        : 'text-emerald-600 dark:text-emerald-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${Math.min(percent, 100)}%` }} />
      </div>
      <span className={`text-sm font-bold w-10 text-right ${textColor}`}>{Number(percent).toFixed(0)}%</span>
    </div>
  )
}

interface Props {
  projectId: number
  onClose: () => void
}

export default function ProjectDetailModal({ projectId, onClose }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['manager-project-detail', projectId],
    queryFn: () => apiClient.get<ProjectDetail>(`/manager/projects/${projectId}`),
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-slate-200 dark:border-slate-700">
          <div className="flex-1 min-w-0">
            {isLoading ? (
              <div className="h-6 w-48 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
            ) : data ? (
              <>
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="text-lg font-bold text-slate-800 dark:text-white truncate">{data.project_name}</h2>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[data.status] ?? STATUS_STYLES.draft}`}>
                    {data.status}
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono mt-0.5">{data.project_code}</p>
              </>
            ) : null}
          </div>
          <button onClick={onClose} className="ml-3 p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 transition-colors shrink-0">
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 p-5 space-y-6">
          {isLoading && (
            <div className="flex items-center justify-center py-16">
              <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
          {isError && (
            <div className="text-center py-10 text-red-500">Erreur lors du chargement.</div>
          )}
          {data && (
            <>
              {/* Client + Adresse */}
              <section>
                <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-3">Client</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                    <Building2 size={14} className="text-slate-400 shrink-0" />
                    <span className="font-medium">{data.client_name}</span>
                  </div>
                  {data.client_address && (
                    <div className="flex items-start gap-2 text-sm text-slate-500 dark:text-slate-400">
                      <MapPin size={14} className="text-slate-400 shrink-0 mt-0.5" />
                      <span>{data.client_address}</span>
                    </div>
                  )}
                </div>
              </section>

              {/* Description */}
              {data.description && (
                <section>
                  <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-3">Description</h3>
                  <div className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
                    <FileText size={14} className="text-slate-400 shrink-0 mt-0.5" />
                    <p className="leading-relaxed">{data.description}</p>
                  </div>
                </section>
              )}

              {/* Dates + Budget */}
              <section>
                <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-3">Planification & Budget</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-3">
                    <div className="flex items-center gap-1.5 mb-1">
                      <Calendar size={13} className="text-slate-400" />
                      <span className="text-xs text-slate-500 dark:text-slate-400">Début</span>
                    </div>
                    <p className="text-sm font-semibold text-slate-800 dark:text-white">
                      {new Date(data.start_date).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-3">
                    <div className="flex items-center gap-1.5 mb-1">
                      <Calendar size={13} className="text-slate-400" />
                      <span className="text-xs text-slate-500 dark:text-slate-400">Fin prévue</span>
                    </div>
                    <p className="text-sm font-semibold text-slate-800 dark:text-white">
                      {data.end_date ? new Date(data.end_date).toLocaleDateString('fr-FR') : '—'}
                    </p>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-3">
                    <div className="flex items-center gap-1.5 mb-1">
                      <Clock size={13} className="text-blue-500" />
                      <span className="text-xs text-slate-500 dark:text-slate-400">Heures consommées</span>
                    </div>
                    <p className="text-sm font-semibold text-slate-800 dark:text-white">
                      {Number(data.hours_consumed).toFixed(1)}h
                      {data.budget_hours && <span className="text-xs text-slate-400 font-normal"> / {Number(data.budget_hours).toFixed(0)}h</span>}
                    </p>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-3">
                    <div className="flex items-center gap-1.5 mb-1">
                      <TrendingUp size={13} className="text-orange-500" />
                      <span className="text-xs text-slate-500 dark:text-slate-400">Budget consommé</span>
                    </div>
                    <BudgetBar percent={data.budget_percent} />
                  </div>
                </div>
              </section>

              {/* Team Members */}
              <section>
                <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                  <Users size={13} />
                  Équipe ({data.team_members.length} membre{data.team_members.length !== 1 ? 's' : ''})
                </h3>
                {data.team_members.length === 0 ? (
                  <p className="text-sm text-slate-400 dark:text-slate-500 italic">Aucun membre assigné à ce projet.</p>
                ) : (
                  <div className="space-y-2">
                    {data.team_members.map(m => (
                      <div key={m.employee_id} className="flex items-start gap-3 bg-slate-50 dark:bg-slate-800 rounded-xl p-3">
                        <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center shrink-0">
                          <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">
                            {(m.first_name?.[0] ?? '?')}{(m.last_name?.[0] ?? '')}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-slate-800 dark:text-white">{m.first_name} {m.last_name}</p>
                          <p className="text-xs text-slate-400 dark:text-slate-500 truncate">{m.email}</p>
                          {m.skills.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1.5">
                              {m.skills.map(s => (
                                <span key={s} className="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded text-xs">
                                  <Star size={9} />
                                  {s}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  )
}

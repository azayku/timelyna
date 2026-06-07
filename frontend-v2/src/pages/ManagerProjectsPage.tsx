import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { FolderOpen, Building2, MapPin, Clock, TrendingUp, Search, Eye } from 'lucide-react'
import { apiClient } from '../lib/apiClient'
import Pagination from '../components/ui/Pagination'
import ProjectDetailModal from '../components/manager/ProjectDetailModal'
import { useBudgetOverview } from '../features/budget/hooks'
import BudgetBar from '../components/BudgetBar'

interface ManagerProject {
  project_id: number
  project_name: string
  project_code: string
  client_name: string
  client_address: string | null
  status: string
  start_date: string
  end_date: string | null
  budget_hours: number | null
  hours_consumed: number
  budget_percent: number | null
}

const STATUS_STYLES: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
  planning: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  draft: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  completed: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  archived: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
}

function BudgetBadge({ percent }: { percent: number | null }) {
  if (percent === null) {
    return <span className="text-sm text-slate-400 dark:text-slate-500">—</span>
  }
  const cls =
    percent >= 90
      ? 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
      : percent >= 70
        ? 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800'
        : 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800'

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md border text-sm font-bold ${cls}`}>
      {Number(percent).toFixed(0)}%
    </span>
  )
}

const PAGE_SIZE = 15

export default function ManagerProjectsPage() {
  const { t } = useTranslation()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null)

  const { data: projects = [], isLoading, isError } = useQuery({
    queryKey: ['manager-projects'],
    queryFn: () => apiClient.get<ManagerProject[]>('/manager/projects'),
  })

  const { data: budgets } = useBudgetOverview()
  const budgetMap = new Map(budgets?.map(b => [b.project_id, b]) ?? [])

  // ── Filter ──────────────────────────────────────────────────────────────
  const filtered = projects.filter(p => {
    const q = search.toLowerCase()
    const matchSearch =
      !q ||
      p.project_name.toLowerCase().includes(q) ||
      p.client_name.toLowerCase().includes(q) ||
      p.project_code.toLowerCase().includes(q)
    const matchStatus = statusFilter === 'all' || p.status === statusFilter
    return matchSearch && matchStatus
  })

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  // ── KPIs ────────────────────────────────────────────────────────────────
  const activeCount = projects.filter(p => p.status === 'active').length
  const totalHours = projects.reduce((a, p) => a + Number(p.hours_consumed), 0)
  const avgBudget =
    projects.filter(p => p.budget_percent !== null).length > 0
      ? projects
          .filter(p => p.budget_percent !== null)
          .reduce((a, p) => a + Number(p.budget_percent ?? 0), 0) /
        projects.filter(p => p.budget_percent !== null).length
      : null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
          <FolderOpen size={22} className="text-indigo-500" />
          {t('manager.projects', 'Mes projets')}
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          {t('manager.projectsSubtitle', 'Projets dont vous êtes responsable — consommation budgétaire en temps réel')}
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
          <div className="flex items-center gap-2 mb-1">
            <FolderOpen size={16} className="text-indigo-500" />
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              {t('manager.totalProjects', 'Total projets')}
            </span>
          </div>
          <p className="text-2xl font-bold text-slate-800 dark:text-white">{projects.length}</p>
          <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-0.5">{activeCount} actifs</p>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
          <div className="flex items-center gap-2 mb-1">
            <Clock size={16} className="text-blue-500" />
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              {t('manager.totalHours', 'Heures consommées')}
            </span>
          </div>
          <p className="text-2xl font-bold text-slate-800 dark:text-white">{totalHours.toFixed(0)}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">heures approuvées + soumises</p>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 col-span-2 md:col-span-1">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={16} className="text-orange-500" />
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              {t('manager.avgBudget', 'Budget moyen consommé')}
            </span>
          </div>
          <p className="text-2xl font-bold text-slate-800 dark:text-white">
            {avgBudget !== null ? `${avgBudget.toFixed(0)}%` : '—'}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">sur les projets budgétés</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder={t('common.search', 'Rechercher...')}
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
          className="px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="all">Tous les statuts</option>
          <option value="active">Actif</option>
          <option value="planning">Planification</option>
          <option value="draft">Brouillon</option>
          <option value="completed">Terminé</option>
          <option value="archived">Archivé</option>
        </select>
      </div>

      {/* Loading / Error */}
      {isLoading && (
        <div className="text-center py-12 text-slate-500 dark:text-slate-400">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          Chargement des projets…
        </div>
      )}
      {isError && (
        <div className="text-center py-12 text-red-500">Erreur lors du chargement des projets.</div>
      )}

      {/* Desktop Table */}
      {!isLoading && !isError && (
        <>
          <div className="hidden md:block bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-700/50 border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    Projet
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    <Building2 size={12} className="inline mr-1" />Client
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    <MapPin size={12} className="inline mr-1" />Adresse
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    <Clock size={12} className="inline mr-1" />Heures
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    <TrendingUp size={12} className="inline mr-1" />Budget consommé
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    Statut
                  </th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {paginated.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-slate-400 dark:text-slate-500">
                      Aucun projet trouvé
                    </td>
                  </tr>
                )}
                {paginated.map(p => (
                  <tr key={p.project_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800 dark:text-white">{p.project_name}</p>
                      <p className="text-xs text-slate-400 font-mono">{p.project_code}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{p.client_name}</td>
                    <td className="px-4 py-3 max-w-[200px]">
                      {p.client_address ? (
                        <span className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">{p.client_address}</span>
                      ) : (
                        <span className="text-xs text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="font-semibold text-slate-800 dark:text-white">{Number(p.hours_consumed).toFixed(1)}</span>
                      {p.budget_hours && (
                        <span className="text-xs text-slate-400 ml-1">/ {Number(p.budget_hours).toFixed(0)}h</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {budgetMap.get(p.project_id) ? (
                        <div className="max-w-[200px]">
                          <BudgetBar budget={budgetMap.get(p.project_id)!} compact />
                        </div>
                      ) : (
                        <div className="text-center">
                          <BudgetBadge percent={p.budget_percent} />
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[p.status] ?? STATUS_STYLES.draft}`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => setSelectedProjectId(p.project_id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 dark:hover:text-indigo-400 transition-colors"
                        title="Voir les détails"
                      >
                        <Eye size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="md:hidden space-y-3">
            {paginated.length === 0 && (
              <div className="text-center py-10 text-slate-400">Aucun projet trouvé</div>
            )}
            {paginated.map(p => (
              <div key={p.project_id} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-slate-800 dark:text-white">{p.project_name}</p>
                    <p className="text-xs text-slate-400 font-mono">{p.project_code}</p>
                  </div>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium shrink-0 ${STATUS_STYLES[p.status] ?? STATUS_STYLES.draft}`}>
                    {p.status}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-sm text-slate-600 dark:text-slate-300">
                  <Building2 size={13} className="text-slate-400 shrink-0" />
                  {p.client_name}
                </div>
                {p.client_address && (
                  <div className="flex items-start gap-1 text-xs text-slate-500 dark:text-slate-400">
                    <MapPin size={12} className="text-slate-400 shrink-0 mt-0.5" />
                    <span>{p.client_address}</span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1 text-sm">
                    <Clock size={13} className="text-blue-500 shrink-0" />
                    <span className="font-semibold text-slate-800 dark:text-white">{Number(p.hours_consumed).toFixed(1)}h</span>
                    {p.budget_hours && (
                      <span className="text-xs text-slate-400">/ {Number(p.budget_hours).toFixed(0)}h</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <BudgetBadge percent={p.budget_percent} />
                    <button
                      onClick={() => setSelectedProjectId(p.project_id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 dark:hover:text-indigo-400 transition-colors"
                      title="Voir les détails"
                    >
                      <Eye size={15} />
                    </button>
                  </div>
                </div>
                {budgetMap.get(p.project_id) && (
                  <div className="mt-2">
                    <BudgetBar budget={budgetMap.get(p.project_id)!} compact />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Pagination */}
          <Pagination
            page={page}
            totalPages={totalPages}
            totalItems={filtered.length}
            itemsPerPage={PAGE_SIZE}
            onPageChange={setPage}
            itemLabel="projet"
          />
        </>
      )}

      {selectedProjectId && (
        <ProjectDetailModal
          projectId={selectedProjectId}
          onClose={() => setSelectedProjectId(null)}
        />
      )}
    </div>
  )
}

import { useState, useMemo } from 'react'
import { useBudgetOverview } from '../features/budget/hooks'
import { AlertTriangle, TrendingUp, Search, ChevronDown, ChevronRight, Clock, Users } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { ProjectBudgetStatus } from '../features/budget/api'
import Pagination from '../components/ui/Pagination'

function BudgetProgressBar({ pct, alert }: { pct: number | null; alert: boolean }) {
  const p = Math.min(pct ?? 0, 100)
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-slate-100 dark:bg-slate-700 rounded-full h-2 min-w-[60px]">
        <div
          className={`h-2 rounded-full transition-all ${
            alert ? 'bg-amber-500' : p >= 80 ? 'bg-orange-400' : 'bg-indigo-500'
          }`}
          style={{ width: `${p}%` }}
        />
      </div>
      <span className={`text-xs font-semibold w-10 text-right ${alert ? 'text-amber-600 dark:text-amber-400' : 'text-slate-600 dark:text-slate-300'}`}>
        {pct !== null ? `${pct.toFixed(0)}%` : '—'}
      </span>
    </div>
  )
}

function BudgetRow({ b }: { b: ProjectBudgetStatus }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)

  return (
    <>
      <tr
        onClick={() => setOpen(o => !o)}
        className={`cursor-pointer border-b border-slate-100 dark:border-slate-700 transition-colors hover:bg-slate-50 dark:hover:bg-slate-700/50 ${
          b.alert ? 'bg-amber-50/40 dark:bg-amber-900/10' : ''
        }`}
      >
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            {open ? <ChevronDown size={14} className="text-slate-400 flex-shrink-0" /> : <ChevronRight size={14} className="text-slate-400 flex-shrink-0" />}
            <div>
              <div className="font-medium text-sm text-slate-800 dark:text-white">{b.project_name}</div>
            </div>
          </div>
        </td>
        <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-300">{b.client_name ?? '—'}</td>
        <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-300 hidden lg:table-cell">{b.manager_name ?? '—'}</td>
        <td className="px-4 py-3 text-sm text-right font-mono text-slate-700 dark:text-slate-200">
          {b.budget_hours !== null ? Number(b.budget_hours).toFixed(0) : '—'}
        </td>
        <td className="px-4 py-3 text-sm text-right font-mono text-slate-700 dark:text-slate-200">
          {Number(b.consumed_hours).toFixed(1)}
        </td>
        <td className={`px-4 py-3 text-sm text-right font-mono hidden sm:table-cell ${
          b.remaining_hours !== null && b.remaining_hours < 0 ? 'text-red-600 dark:text-red-400 font-semibold' : 'text-slate-700 dark:text-slate-200'
        }`}>
          {b.remaining_hours !== null ? Number(b.remaining_hours).toFixed(1) : '—'}
        </td>
        <td className="px-4 py-3 min-w-[120px]">
          <BudgetProgressBar pct={b.consumption_percentage} alert={b.alert} />
        </td>
        <td className="px-4 py-3 text-center">
          {b.alert && <AlertTriangle size={16} className="text-amber-500 mx-auto" />}
        </td>
      </tr>
      {open && (
        <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-700">
          <td colSpan={8} className="px-6 py-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-white dark:bg-slate-800 rounded-lg p-3 border border-slate-200 dark:border-slate-700">
                <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">{t('budget.budgetHours')}</div>
                <div className="text-xl font-bold text-slate-800 dark:text-white">
                  {b.budget_hours !== null ? `${Number(b.budget_hours).toFixed(0)}h` : t('budget.noBudgetDefined')}
                </div>
              </div>
              <div className="bg-white dark:bg-slate-800 rounded-lg p-3 border border-slate-200 dark:border-slate-700">
                <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">{t('budget.consumed')}</div>
                <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400">{Number(b.consumed_hours).toFixed(1)}h</div>
              </div>
              <div className="bg-white dark:bg-slate-800 rounded-lg p-3 border border-slate-200 dark:border-slate-700">
                <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">{t('budget.remaining')}</div>
                <div className={`text-xl font-bold ${b.remaining_hours !== null && b.remaining_hours < 0 ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                  {b.remaining_hours !== null ? `${Number(b.remaining_hours).toFixed(1)}h` : '—'}
                </div>
              </div>
              <div className="bg-white dark:bg-slate-800 rounded-lg p-3 border border-slate-200 dark:border-slate-700">
                <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">{t('budget.tableProgress')}</div>
                <div className="mt-2">
                  <BudgetProgressBar pct={b.consumption_percentage} alert={b.alert} />
                </div>
              </div>
            </div>
            {b.manager_name && (
              <div className="mt-3 flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                <span className="flex items-center gap-1.5"><Users size={12} />{t('budget.manager')}: <strong className="text-slate-700 dark:text-slate-200">{b.manager_name}</strong></span>
                {b.client_name && <span className="flex items-center gap-1.5"><Clock size={12} />{t('budget.client')}: <strong className="text-slate-700 dark:text-slate-200">{b.client_name}</strong></span>}
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  )
}

export default function BudgetDashboardPage() {
  const { t } = useTranslation()
  const { data: budgets, isLoading } = useBudgetOverview()
  const [search, setSearch] = useState('')
  const [clientFilter, setClientFilter] = useState<string>('all')
  const [alertFilter, setAlertFilter] = useState(false)
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 15

  const clients = useMemo(() => {
    const set = new Set<string>()
    budgets?.forEach(b => { if (b.client_name) set.add(b.client_name) })
    return Array.from(set).sort()
  }, [budgets])

  const filtered = useMemo(() => {
    if (!budgets) return []
    return budgets.filter(b => {
      const matchSearch = !search || b.project_name.toLowerCase().includes(search.toLowerCase()) ||
        (b.client_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
        (b.manager_name ?? '').toLowerCase().includes(search.toLowerCase())
      const matchClient = clientFilter === 'all' || b.client_name === clientFilter
      const matchAlert = !alertFilter || b.alert
      return matchSearch && matchClient && matchAlert
    })
  }, [budgets, search, clientFilter, alertFilter])

  // Reset page on filter change
  const resetPage = (fn: () => void) => { fn(); setPage(1) }

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const totalBudget = filtered.reduce((s, b) => s + (b.budget_hours ?? 0), 0)
  const totalConsumed = filtered.reduce((s, b) => s + b.consumed_hours, 0)
  const alertCount = filtered.filter(b => b.alert).length

  return (
    <div className="p-4 sm:p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white flex items-center gap-2">
            <TrendingUp size={22} className="text-indigo-500" />
            {t('budget.title')}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{t('budget.subtitle')}</p>
        </div>
        {alertCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-amber-700 dark:text-amber-400 text-sm font-medium">
            <AlertTriangle className="h-4 w-4" />
            {alertCount} {t('budget.projectsInAlert')}
          </div>
        )}
      </div>

      {/* KPIs */}
      {!isLoading && budgets && budgets.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: t('budget.kpiTotalProjects'), value: filtered.length, color: 'text-indigo-600 dark:text-indigo-400' },
            { label: t('budget.kpiTotalBudget'), value: `${Number(totalBudget).toFixed(0)}h`, color: 'text-slate-800 dark:text-white' },
            { label: t('budget.kpiConsumed'), value: `${Number(totalConsumed).toFixed(1)}h`, color: 'text-blue-600 dark:text-blue-400' },
            { label: t('budget.kpiAlerts'), value: alertCount, color: alertCount > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-slate-500 dark:text-slate-400' },
          ].map(k => (
            <div key={k.label} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-3 sm:p-4">
              <div className="text-xs text-slate-500 dark:text-slate-400">{k.label}</div>
              <div className={`text-xl sm:text-2xl font-bold mt-1 ${k.color}`}>{k.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={e => resetPage(() => setSearch(e.target.value))}
            placeholder={t('budget.searchPlaceholder')}
            className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        {clients.length > 0 && (
          <select
            value={clientFilter}
            onChange={e => resetPage(() => setClientFilter(e.target.value))}
            className="px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">{t('budget.filterAll')} {t('budget.filterClient')}</option>
            {clients.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        )}
        <button
          onClick={() => resetPage(() => setAlertFilter(a => !a))}
          className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors ${
            alertFilter
              ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-400'
              : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:border-amber-300'
          }`}
        >
          <AlertTriangle size={14} />
          {t('budget.filterAlert')}
        </button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-slate-500 dark:text-slate-400">{t('common.loading')}</p>
        </div>
      )}

      {/* Table */}
      {!isLoading && filtered.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide bg-slate-50 dark:bg-slate-700/50 border-b border-slate-200 dark:border-slate-700">
                  <th className="px-4 py-3 text-left">{t('budget.tableProject')}</th>
                  <th className="px-4 py-3 text-left">{t('budget.tableClient')}</th>
                  <th className="px-4 py-3 text-left hidden lg:table-cell">{t('budget.tableManager')}</th>
                  <th className="px-4 py-3 text-right">{t('budget.tableBudget')}</th>
                  <th className="px-4 py-3 text-right">{t('budget.tableConsumed')}</th>
                  <th className="px-4 py-3 text-right hidden sm:table-cell">{t('budget.tableRemaining')}</th>
                  <th className="px-4 py-3 text-left min-w-[130px]">{t('budget.tableProgress')}</th>
                  <th className="px-4 py-3 w-8"></th>
                </tr>
              </thead>
              <tbody>
                {paginated.map(b => <BudgetRow key={b.project_id} b={b} />)}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination */}
      {!isLoading && filtered.length > PAGE_SIZE && (
        <Pagination
          page={page}
          totalPages={totalPages}
          totalItems={filtered.length}
          itemsPerPage={PAGE_SIZE}
          onPageChange={setPage}
        />
      )}

      {/* Empty */}
      {!isLoading && filtered.length === 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <TrendingUp size={48} className="mx-auto text-slate-300 dark:text-slate-600 mb-3" />
          <p className="text-slate-500 dark:text-slate-400">{t('budget.noBudgets')}</p>
        </div>
      )}
    </div>
  )
}

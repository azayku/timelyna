import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calendar, Users, AlertTriangle, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { apiClient } from '../lib/apiClient'

// ─── Types ────────────────────────────────────────────────────────────────────

interface DayData {
  hours_logged: number
  occupation_pct: number
  absence: { type: string; status: string } | null
}

interface EmployeeAvailability {
  employee_id: number
  full_name: string
  department: string
  days: Record<string, DayData>
}

interface AvailabilityData {
  dates: string[]
  standard_hours_per_day: number
  employees: EmployeeAvailability[]
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getCellStyle(day: DayData): string {
  if (day.absence) return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
  if (day.occupation_pct === 0) return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
  if (day.occupation_pct < 50) return 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-400'
  if (day.occupation_pct < 100) return 'bg-amber-50 text-amber-600 dark:bg-amber-900/20 dark:text-amber-400'
  return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AvailabilityPage() {
  const { t } = useTranslation()

  const today = new Date().toISOString().split('T')[0]
  const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

  const [startDate, setStartDate] = useState(weekAgo)
  const [endDate, setEndDate] = useState(today)
  const [department, setDepartment] = useState('')
  const [projectId, setProjectId] = useState('')

  const { data, isLoading, isError } = useQuery<AvailabilityData>({
    queryKey: ['availability', startDate, endDate, department, projectId],
    queryFn: () => {
      const params = new URLSearchParams({ start_date: startDate, end_date: endDate })
      if (department) params.append('department', department)
      if (projectId) params.append('project_id', projectId)
      return apiClient.get<AvailabilityData>(`/admin/availability?${params}`)
    },
    enabled: !!startDate && !!endDate,
  })

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Users size={22} className="text-indigo-600" />
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-white">
            {t('availability.title', 'Disponibilité des employés')}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {t('availability.subtitle', 'Vue de la charge de travail par employé et par jour')}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">
              {t('common.startDate', 'Date début')}
            </label>
            <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
              className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">
              {t('common.endDate', 'Date fin')}
            </label>
            <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
              className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">
              {t('availability.department', 'Département')}
            </label>
            <input type="text" value={department} onChange={e => setDepartment(e.target.value)}
              placeholder={t('common.all', 'Tous')}
              className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">
              {t('availability.projectId', 'Projet ID')}
            </label>
            <input type="number" value={projectId} onChange={e => setProjectId(e.target.value)}
              placeholder={t('common.all', 'Tous')}
              className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white" />
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-5 text-xs text-slate-600 dark:text-slate-400">
        <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-emerald-100 dark:bg-emerald-900/30" /><span>Disponible</span></div>
        <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-amber-50 dark:bg-amber-900/20" /><span>Partiel</span></div>
        <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-red-100 dark:bg-red-900/30" /><span>Complet</span></div>
        <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-purple-100 dark:bg-purple-900/30" /><span>Absent</span></div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
          <Loader2 size={16} className="animate-spin" /> Chargement…
        </div>
      ) : isError ? (
        <div className="flex items-center justify-center gap-2 py-16 text-red-500 text-sm">
          <AlertTriangle size={16} /> Erreur lors du chargement des données
        </div>
      ) : !data || data.employees.length === 0 ? (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <Calendar size={44} className="mx-auto text-slate-200 dark:text-slate-600 mb-3" />
          <p className="text-slate-500 dark:text-slate-400 text-sm">Aucun employé trouvé pour cette période</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
            <thead className="bg-slate-50 dark:bg-slate-700">
              <tr>
                <th className="sticky left-0 z-10 bg-slate-50 dark:bg-slate-700 px-5 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Employé
                </th>
                {data.dates.map((date) => {
                  const d = new Date(date + 'T12:00:00')
                  return (
                    <th key={date} className="px-3 py-3 text-center text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
                      <div>{d.toLocaleDateString('fr-FR', { weekday: 'short' })}</div>
                      <div className="text-slate-400 dark:text-slate-500 font-normal">
                        {d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
                      </div>
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {data.employees.map((emp) => (
                <tr key={emp.employee_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                  <td className="sticky left-0 z-10 bg-white dark:bg-slate-800 px-5 py-3 whitespace-nowrap">
                    <p className="text-sm font-medium text-slate-900 dark:text-white">{emp.full_name}</p>
                    {emp.department && (
                      <p className="text-xs text-slate-500 dark:text-slate-400">{emp.department}</p>
                    )}
                  </td>
                  {data.dates.map((date) => {
                    const day = emp.days[date]
                    if (!day) return <td key={date} className="px-3 py-3 text-center"><span className="text-xs text-slate-300">—</span></td>
                    return (
                      <td key={date} className="px-3 py-3 text-center">
                        <div className={`inline-block px-2 py-1 rounded text-xs font-medium ${getCellStyle(day)}`}>
                          {day.absence ? (
                            <span className="whitespace-nowrap">{day.absence.type}</span>
                          ) : (
                            <div>
                              <div className="font-bold">{day.hours_logged}h</div>
                              <div className="text-xs opacity-75">{day.occupation_pct}%</div>
                            </div>
                          )}
                        </div>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

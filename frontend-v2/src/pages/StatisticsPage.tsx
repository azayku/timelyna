import { useState } from 'react'
import { Clock, TrendingUp, DollarSign, Calendar, Loader2, AlertTriangle } from 'lucide-react'
import KpiCard from '../components/ui/KpiCard'
import Card, { CardHeader } from '../components/ui/Card'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import { useEmployeeStatistics } from '../features/reporting/hooks'
import { useEmployees } from '../features/employees/hooks'
import { useAuthStore } from '../lib/authStore'

const PIE_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6']

const RADAR_TASK_TYPES = ['normal', 'overtime', 'travel', 'night']

export default function StatisticsPage() {
  const { t } = useTranslation()
  const currentUser = useAuthStore(s => s.user)
  const isManagerOrAdmin = currentUser?.role === 'manager' || currentUser?.role === 'admin'
  
  const [period, setPeriod] = useState('this_month')
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null)

  const { data: employees = [] } = useEmployees({ enabled: currentUser?.role === 'admin' })
  const { data, isLoading, isError } = useEmployeeStatistics(period)

  const PERIODS = [
    { key: 'this_month', label: t('dashboard.thisMonth') },
    { key: 'last_month', label: t('finance.period.last_month') },
    { key: 'quarter', label: t('finance.period.quarter') },
    { key: 'year', label: t('finance.period.year') },
  ]

  const billableRateDisplay = data ? `${Number(data.billable_pct).toFixed(1)}%` : '—'
  const totalHoursDisplay = data ? `${Number(data.total_hours).toFixed(1)}h` : '—'
  const billableHoursDisplay = data ? `${Number(data.billable_hours).toFixed(1)}h` : '—'
  const daysWorkedDisplay = data ? String(data.days_worked) : '—'

  const weeklyData = data?.weekly_trend ?? []
  const projectData = (data?.project_breakdown ?? []).map((p, i) => ({
    name: p.project_name,
    hours: p.hours,
    fill: PIE_COLORS[i % PIE_COLORS.length],
  }))

  const radarData = RADAR_TASK_TYPES.map(type => {
    const found = data?.task_type_breakdown.find(t => t.task_type === type)
    return { subject: type.charAt(0).toUpperCase() + type.slice(1), A: found?.hours ?? 0, fullMark: data?.total_hours ?? 100 }
  })

  return (
    <div className="space-y-5">
      {/* Period selector + Employee selector */}
      <div className="flex flex-col sm:flex-row gap-3 flex-wrap">
        <div className="flex gap-2 flex-wrap">
          {PERIODS.map(p => (
            <button key={p.key} onClick={() => setPeriod(p.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                period === p.key
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
              }`}>
              {p.label}
            </button>
          ))}
        </div>
        
        {isManagerOrAdmin && (
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-slate-600 dark:text-slate-300">Employé:</label>
            <select
              value={selectedEmployeeId ?? ''}
              onChange={e => setSelectedEmployeeId(e.target.value ? Number(e.target.value) : null)}
              className="border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Mes statistiques</option>
              {employees.map(e => (
                <option key={e.employee_id} value={e.employee_id}>
                  {e.first_name} {e.last_name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 size={32} className="animate-spin text-indigo-500" />
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400">
          <AlertTriangle size={20} className="flex-shrink-0" />
          <span className="text-sm">{t('common.error')}</span>
        </div>
      )}

      {!isLoading && !isError && (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard icon={<Clock size={20} />} iconBg="bg-indigo-100" label={t('statistics.totalHours')} value={totalHoursDisplay} trend={0} trendLabel={t('statistics.vsPrev')} />
            <KpiCard icon={<TrendingUp size={20} />} iconBg="bg-amber-100" label={t('statistics.billableHours')} value={billableHoursDisplay} trend={0} trendLabel={t('statistics.vsPrev')} />
            <KpiCard icon={<DollarSign size={20} />} iconBg="bg-emerald-100" label={t('statistics.billableRate')} value={billableRateDisplay} trend={0} trendLabel={t('statistics.vsPrev')} />
            <KpiCard icon={<Calendar size={20} />} iconBg="bg-purple-100" label={t('statistics.daysWorked')} value={daysWorkedDisplay} trend={0} trendLabel={t('statistics.vsPrev')} />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <Card>
              <CardHeader title={t('statistics.weeklyTrend')} subtitle={t('statistics.hoursPerWeek')} />
              {weeklyData.length === 0 ? (
                <p className="text-sm text-slate-400 dark:text-slate-500 py-8 text-center">{t('common.noData')}</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={weeklyData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="week" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    <Bar dataKey="hours" fill="#6366f1" radius={[4, 4, 0, 0]} name={t('common.hours')} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>

            <Card>
              <CardHeader title={t('statistics.projectBreakdown')} subtitle={t('dashboard.thisMonth')} />
              {projectData.length === 0 ? (
                <p className="text-sm text-slate-400 dark:text-slate-500 py-8 text-center">{t('common.noData')}</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={projectData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} dataKey="hours" paddingAngle={3}>
                      {projectData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                    </Pie>
                    <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
                    <Tooltip contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </Card>
          </div>

          {/* Radar + task type breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <Card>
              <CardHeader title={t('statistics.hoursPerWeek')} subtitle={t('statistics.projectBreakdown')} />
              <ResponsiveContainer width="100%" height={260}>
                <RadarChart cx="50%" cy="50%" outerRadius={90} data={radarData}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: '#64748b' }} />
                  <PolarRadiusAxis angle={30} domain={[0, Math.max(data?.total_hours ?? 1, 1)]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                  <Radar name={t('common.hours')} dataKey="A" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} strokeWidth={2} />
                  <Tooltip contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                </RadarChart>
              </ResponsiveContainer>
            </Card>

            {/* Top projects by hours */}
            <Card>
              <CardHeader title={t('statistics.projectBreakdown')} subtitle={t('dashboard.thisMonth')} />
              <div className="space-y-3 mt-2">
                {projectData.length === 0 && (
                  <p className="text-sm text-slate-400 dark:text-slate-500 py-4 text-center">{t('common.noData')}</p>
                )}
                {projectData.slice(0, 5).map((proj, i) => {
                  const maxHours = projectData[0]?.hours || 1
                  const pct = Math.round((proj.hours / maxHours) * 100)
                  return (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 flex items-center justify-center text-xs font-bold flex-shrink-0">
                        {i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between text-xs mb-1">
                          <span className="font-medium text-slate-700 dark:text-slate-200 truncate">{proj.name}</span>
                          <span className="text-slate-500 dark:text-slate-400 ml-2 flex-shrink-0">{Number(proj.hours).toFixed(1)}h</span>
                        </div>
                        <div className="h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-indigo-500 rounded-full transition-all"
                            style={{ width: `${pct}%`, backgroundColor: proj.fill }}
                          />
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}

import { Clock, Users, CheckSquare, TrendingUp } from 'lucide-react'
import KpiCard from '../components/ui/KpiCard'
import Card, { CardHeader } from '../components/ui/Card'
import { StatusBadge } from '../components/ui/Badge'
import Avatar from '../components/ui/Avatar'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'
import { useManagerApprovals } from '../features/approvals/hooks'
import { useAuthStore } from '../lib/authStore'
import { Navigate } from 'react-router-dom'

// Types
interface MonthlyStats {
  month: string
  hours: number
  overtime: number
}

interface DashboardStats {
  total_hours_this_month: number
  active_employees: number
  pending_approvals: number
  overtime_hours: number
  monthly_hours: MonthlyStats[]
  hours_breakdown: {
    normal: number
    overtime: number
    travel: number
    night: number
  }
}

export default function DashboardPage() {
  const { t } = useTranslation()
  const role = useAuthStore((s) => s.user?.role ?? 'employee')

  // Employees don't have a manager dashboard — redirect to timesheet
  if (role === 'employee') {
    return <Navigate to="/timesheet/my-timesheets" replace />
  }

  // Fetch dashboard stats (using reporting endpoint)
  const { data: stats, isLoading: loadingStats } = useQuery<DashboardStats>({
    queryKey: ['manager-dashboard-stats'],
    queryFn: () => apiClient.get<DashboardStats>('/manager-dashboard'),
    staleTime: 2 * 60 * 1000,
  })

  // Fetch recent approvals
  const { data: approvalsData = [] } = useManagerApprovals('pending')
  const recentApprovals = approvalsData.slice(0, 5)

  // Fetch recent absences
  const { data: absences = [] } = useQuery({
    queryKey: ['manager-recent-absences'],
    queryFn: () => apiClient.get<any[]>('/manager/absences?limit=5&status=pending'),
    staleTime: 2 * 60 * 1000,
  })

  // Calculate KPIs
  const totalHours = stats?.total_hours_this_month ?? 0
  const activeEmployees = stats?.active_employees ?? 0
  const pendingCount = recentApprovals.length
  const overtimeHours = stats?.overtime_hours ?? 0

  // Monthly data for chart
  const monthlyData = stats?.monthly_hours ?? []

  // Hours breakdown
  const breakdown = stats?.hours_breakdown ?? null
  const total = breakdown ? breakdown.normal + breakdown.overtime + breakdown.travel + breakdown.night : 0
  const breakdownPct = breakdown && total > 0 ? {
    normal: Math.round((breakdown.normal / total) * 100),
    overtime: Math.round((breakdown.overtime / total) * 100),
    travel: Math.round((breakdown.travel / total) * 100),
    night: Math.round((breakdown.night / total) * 100),
  } : { normal: 0, overtime: 0, travel: 0, night: 0 }

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard 
          icon={<Clock size={20} />} 
          iconBg="bg-indigo-100" 
          label={t('dashboard.hoursThisMonth')} 
          value={loadingStats ? '...' : `${totalHours.toLocaleString()}h`} 
        />
        <KpiCard 
          icon={<Users size={20} />} 
          iconBg="bg-emerald-100" 
          label={t('dashboard.activeEmployees')} 
          value={loadingStats ? '...' : String(activeEmployees)} 
        />
        <KpiCard 
          icon={<CheckSquare size={20} />} 
          iconBg="bg-amber-100" 
          label={t('dashboard.pendingApprovals')} 
          value={String(pendingCount)} 
        />
        <KpiCard 
          icon={<TrendingUp size={20} />} 
          iconBg="bg-purple-100" 
          label={t('dashboard.overtime')} 
          value={loadingStats ? '...' : `${overtimeHours.toLocaleString()}h`} 
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Hours chart */}
        <Card className="lg:col-span-2">
          <CardHeader title={t('dashboard.hoursWorked')} subtitle={t('dashboard.last9Months')} action={
            <button className="text-xs text-indigo-600 font-medium hover:underline">{t('dashboard.download')}</button>
          } />
          {loadingStats ? (
            <div className="flex items-center justify-center h-[220px] text-slate-400 text-sm">
              Chargement...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={monthlyData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Bar dataKey="hours" fill="#6366f1" radius={[4, 4, 0, 0]} name={t('dashboard.normalHours')} />
                <Bar dataKey="overtime" fill="#a5b4fc" radius={[4, 4, 0, 0]} name={t('dashboard.overtimeHours')} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* Type breakdown */}
        <Card>
          <CardHeader title={t('dashboard.hoursBreakdown')} subtitle={t('dashboard.thisMonth')} />
          <div className="space-y-3">
            {[
              { label: t('dashboard.normalHours'), pct: breakdownPct.normal, color: 'bg-indigo-500' },
              { label: t('dashboard.overtimeHours'), pct: breakdownPct.overtime, color: 'bg-amber-500' },
              { label: t('dashboard.travelHours'), pct: breakdownPct.travel, color: 'bg-blue-500' },
              { label: t('dashboard.nightHours'), pct: breakdownPct.night, color: 'bg-purple-500' },
            ].map((item) => (
              <div key={item.label}>
                <div className="flex justify-between text-xs text-slate-600 mb-1">
                  <span>{item.label}</span>
                  <span className="font-semibold">{item.pct}%</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className={`h-full ${item.color} rounded-full`} style={{ width: `${item.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Tables row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Recent approvals */}
        <Card padding={false}>
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-800">{t('dashboard.recentApprovals')}</h2>
              <p className="text-xs text-slate-400 mt-0.5">{t('dashboard.pendingWeeks')}</p>
            </div>
            <a href="/approvals" className="text-xs text-indigo-600 font-medium hover:underline">{t('dashboard.viewAll')}</a>
          </div>
          <div className="divide-y divide-slate-100">
            {recentApprovals.length === 0 ? (
              <div className="px-5 py-8 text-center text-slate-400 text-sm">
                {t('dashboard.noApprovals', 'Aucune approbation en attente')}
              </div>
            ) : (
              recentApprovals.map((row) => (
                <div key={row.approval_id} className="flex items-center justify-between px-5 py-3.5 hover:bg-slate-50">
                  <div className="flex items-center gap-3">
                    <Avatar name={row.employee_name ?? `Employee ${row.employee_id}`} size="sm" />
                    <div>
                      <p className="text-sm font-medium text-slate-800">{row.employee_name ?? `Employee #${row.employee_id}`}</p>
                      <p className="text-xs text-slate-400">{row.week_start} · {row.total_hours}h</p>
                    </div>
                  </div>
                  <StatusBadge status={row.status} />
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Recent absences */}
        <Card padding={false}>
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-800">{t('dashboard.recentAbsences')}</h2>
              <p className="text-xs text-slate-400 mt-0.5">{t('dashboard.ongoingRequests')}</p>
            </div>
            <a href="/manager/absences" className="text-xs text-indigo-600 font-medium hover:underline">{t('dashboard.viewAll')}</a>
          </div>
          <div className="divide-y divide-slate-100">
            {absences.length === 0 ? (
              <div className="px-5 py-8 text-center text-slate-400 text-sm">
                {t('dashboard.noAbsences', 'Aucune absence en attente')}
              </div>
            ) : (
              absences.map((row: any, i: number) => (
                <div key={i} className="flex items-center justify-between px-5 py-3.5 hover:bg-slate-50">
                  <div className="flex items-center gap-3">
                    <Avatar name={row.employee_name ?? `Employee ${row.employee_id}`} size="sm" />
                    <div>
                      <p className="text-sm font-medium text-slate-800">{row.employee_name ?? `Employee #${row.employee_id}`}</p>
                      <p className="text-xs text-slate-400">{row.absence_type} · {row.days_count} jour(s) · {row.start_date}</p>
                    </div>
                  </div>
                  <StatusBadge status={row.status} />
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

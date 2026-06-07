import { useState } from 'react'
import { Clock, Users, CheckSquare, TrendingUp, Calendar, Plus, MapPin, Briefcase, ChevronLeft, ChevronRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../lib/apiClient'
import { useAuthStore } from '../lib/authStore'
import { useThemeStore } from '../lib/themeStore'
import { useManagerApprovals } from '../features/approvals/hooks'
import type { TimesheetEntry } from '../features/timesheet/types'
import type { Absence } from '../features/absences/types'
import KpiCard from '../components/ui/KpiCard'
import Card, { CardHeader } from '../components/ui/Card'
import Button from '../components/ui/Button'
import QuickTimesheetModal from '../components/modals/QuickTimesheetModal'
import TimeOffRequestModal from '../components/modals/TimeOffRequestModal'
import TimerWidget from '../components/TimerWidget'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface DashboardStats {
  total_hours_this_month: number
  active_employees?: number
  pending_approvals?: number
  overtime_hours: number
  monthly_hours: { month: string; hours: number; overtime: number }[]
  hours_breakdown: {
    normal: number
    overtime: number
    travel: number
    night: number
  }
}

interface Project {
  project_id: number
  project_name: string
  client_name?: string
  client_address?: string
  start_date: string
  end_date?: string
}

function toISOWeek(date: Date): string {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7))
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  const weekNo = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
  return `${d.getUTCFullYear()}-W${String(weekNo).padStart(2, '0')}`
}

function getNextWeekDate(): Date {
  const today = new Date()
  const nextWeek = new Date(today)
  nextWeek.setDate(today.getDate() + 7)
  return nextWeek
}

function isWednesdayOrLater(displayDay: number = 2): boolean {
  const today = new Date()
  const dayOfWeek = today.getDay() // 0 = Sunday, 1 = Monday, 2 = Tuesday, etc.
  return dayOfWeek >= displayDay
}

export default function UnifiedDashboardPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const role = useAuthStore((s) => s.user?.role ?? 'employee')
  const { dark } = useThemeStore()
  const [showQuickEntry, setShowQuickEntry] = useState(false)
  const [showQuickMenu, setShowQuickMenu] = useState(false)
  const [showAbsenceModal, setShowAbsenceModal] = useState(false)
  
  // Pagination states
  const [thisWeekPage, setThisWeekPage] = useState(1)
  const [nextWeekPage, setNextWeekPage] = useState(1)
  const projectsPerPage = 5

  const isManager = ['manager', 'admin', 'payroll'].includes(role)

  // Chart colors based on theme
  const chartColors = {
    grid: dark ? '#334155' : '#e2e8f0',        // slate-700 vs slate-200
    text: dark ? '#94a3b8' : '#64748b',         // slate-400 vs slate-500
    tooltipBg: dark ? '#1e293b' : '#ffffff',    // slate-800 vs white
    tooltipBorder: dark ? '#334155' : '#e2e8f0',
    primary: '#6366f1',   // indigo-500 (identique)
    warning: '#f59e0b',   // amber-500
  }

  // Fetch org config to get next_week_display_day
  const { data: orgConfig } = useQuery({
    queryKey: ['org-config'],
    queryFn: () => apiClient.get<{ next_week_display_day: number }>('/auth/org-config'),
    staleTime: 60 * 60 * 1000, // Cache for 1 hour
  })

  const nextWeekDisplayDay = orgConfig?.next_week_display_day ?? 2 // Default: Tuesday

  // Fetch projects for this week
  const today = new Date()
  const { data: thisWeekProjects = [] } = useQuery({
    queryKey: ['projects-this-week'],
    queryFn: () => apiClient.get<Project[]>(`/projects?active=true&date=${today.toISOString().split('T')[0]}`),
  })

  // Fetch projects for next week (only if configured day or later)
  const showNextWeek = isWednesdayOrLater(nextWeekDisplayDay)
  const nextWeekDate = getNextWeekDate()
  const { data: nextWeekProjects = [] } = useQuery({
    queryKey: ['projects-next-week'],
    queryFn: () => apiClient.get<Project[]>(`/projects?active=true&date=${nextWeekDate.toISOString().split('T')[0]}`),
    enabled: showNextWeek,
  })

  // Employee stats
  const currentWeek = toISOWeek(new Date())
  const { data: myEntries = [] } = useQuery({
    queryKey: ['my-recent-entries'],
    queryFn: () => apiClient.get<TimesheetEntry[]>('/employee/timesheet/entries'),
  })

  const { data: myAbsences = [] } = useQuery({
    queryKey: ['my-absences-summary'],
    queryFn: () => apiClient.get<Absence[]>('/employee/absences'),
  })

  // Calculate employee stats with comparisons
  const draftCount = myEntries.filter(e => e.status === 'draft').length
  const submittedCount = myEntries.filter(e => e.status === 'submitted').length
  
  // Current week hours
  const thisWeekHours = myEntries
    .filter(e => toISOWeek(new Date(e.work_date + 'T12:00:00')) === currentWeek)
    .reduce((sum, e) => sum + Number(e.hours_worked), 0)

  // Last week hours for comparison
  const lastWeekDate = new Date()
  lastWeekDate.setDate(lastWeekDate.getDate() - 7)
  const lastWeek = toISOWeek(lastWeekDate)
  const lastWeekHours = myEntries
    .filter(e => toISOWeek(new Date(e.work_date + 'T12:00:00')) === lastWeek)
    .reduce((sum, e) => sum + Number(e.hours_worked), 0)
  const weekTrend = lastWeekHours > 0 ? ((thisWeekHours - lastWeekHours) / lastWeekHours) * 100 : 0

  // Current month hours
  const now = new Date()
  const currentMonth = now.getMonth()
  const currentYear = now.getFullYear()
  const thisMonthHours = myEntries
    .filter(e => {
      const d = new Date(e.work_date + 'T12:00:00')
      return d.getMonth() === currentMonth && d.getFullYear() === currentYear
    })
    .reduce((sum, e) => sum + Number(e.hours_worked), 0)

  // Last month hours for comparison
  const lastMonth = currentMonth === 0 ? 11 : currentMonth - 1
  const lastMonthYear = currentMonth === 0 ? currentYear - 1 : currentYear
  const lastMonthHours = myEntries
    .filter(e => {
      const d = new Date(e.work_date + 'T12:00:00')
      return d.getMonth() === lastMonth && d.getFullYear() === lastMonthYear
    })
    .reduce((sum, e) => sum + Number(e.hours_worked), 0)
  const monthTrend = lastMonthHours > 0 ? ((thisMonthHours - lastMonthHours) / lastMonthHours) * 100 : 0

  const pendingAbsences = myAbsences.filter(a => a.status === 'pending').length
  const approvedAbsences = myAbsences.filter(a => a.status === 'approved').length

  // Manager stats (if applicable)
  const { data: managerStats } = useQuery<DashboardStats>({
    queryKey: ['manager-dashboard-stats'],
    queryFn: () => apiClient.get<DashboardStats>('/manager-dashboard'),
    enabled: isManager,
    staleTime: 2 * 60 * 1000,
  })

  const { data: pendingApprovals = [] } = useManagerApprovals('pending')

  // Pagination calculations
  const thisWeekTotalPages = Math.ceil(thisWeekProjects.length / projectsPerPage)
  const nextWeekTotalPages = Math.ceil(nextWeekProjects.length / projectsPerPage)

  const thisWeekPaginated = thisWeekProjects.slice(
    (thisWeekPage - 1) * projectsPerPage,
    thisWeekPage * projectsPerPage
  )
  const nextWeekPaginated = nextWeekProjects.slice(
    (nextWeekPage - 1) * projectsPerPage,
    nextWeekPage * projectsPerPage
  )

  return (
    <div className="space-y-6">
      {/* Welcome header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white">
            {t('dashboard.welcome', 'Bienvenue')}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          </p>
        </div>
        
        {/* Desktop only - Quick actions menu */}
        <div className="hidden lg:block relative">
          <Button 
            icon={<Plus size={16} />} 
            onClick={() => setShowQuickMenu(!showQuickMenu)}
          >
            Saisie rapide
          </Button>

          {/* Quick menu popup */}
          {showQuickMenu && (
            <>
              <div className="absolute top-full right-0 mt-2 flex flex-col gap-2 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 p-2 min-w-[200px] z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                <button
                  onClick={() => {
                    setShowQuickMenu(false)
                    setShowQuickEntry(true)
                  }}
                  className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-left"
                >
                  <Clock size={18} />
                  <span className="text-sm font-medium">Saisie rapide</span>
                </button>
                <button
                  onClick={() => {
                    setShowQuickMenu(false)
                    setShowAbsenceModal(true)
                  }}
                  className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-left"
                >
                  <Calendar size={18} />
                  <span className="text-sm font-medium">Déclarer absence</span>
                </button>
              </div>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowQuickMenu(false)}
              />
            </>
          )}
        </div>
      </div>

      {/* Employee KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        <KpiCard
          label={t('dashboard.thisWeekHours', 'Heures cette semaine')}
          value={thisWeekHours.toFixed(1)}
          icon={<Clock size={18} className="sm:w-5 sm:h-5" />}
          trend={Math.round(weekTrend)}
          trendLabel={`vs semaine dernière (${lastWeekHours.toFixed(1)}h)`}
        />
        <KpiCard
          label={t('dashboard.thisMonthHours', 'Heures ce mois')}
          value={thisMonthHours.toFixed(1)}
          icon={<TrendingUp size={18} className="sm:w-5 sm:h-5" />}
          trend={Math.round(monthTrend)}
          trendLabel={`vs mois dernier (${lastMonthHours.toFixed(1)}h)`}
        />
        <button onClick={() => navigate('/timesheet/my-timesheets')} className="text-left">
          <KpiCard
            label={t('dashboard.drafts', 'Brouillons')}
            value={draftCount}
            icon={<Clock size={18} className="sm:w-5 sm:h-5" />}
          />
        </button>
        <button onClick={() => navigate('/timesheet/my-timesheets')} className="text-left">
          <KpiCard
            label={t('dashboard.submitted', 'En attente')}
            value={submittedCount}
            icon={<CheckSquare size={18} className="sm:w-5 sm:h-5" />}
          />
        </button>
        <button onClick={() => navigate('/history')} className="text-left">
          <KpiCard
            label={t('dashboard.absencesPending', 'Absences en attente')}
            value={pendingAbsences}
            icon={<Calendar size={18} className="sm:w-5 sm:h-5" />}
          />
        </button>
        <button onClick={() => navigate('/history')} className="text-left">
          <KpiCard
            label={t('dashboard.absencesApproved', 'Absences approuvées')}
            value={approvedAbsences}
            icon={<Calendar size={18} className="sm:w-5 sm:h-5" />}
            subtitle={`${25 - approvedAbsences} jours restants`}
          />
        </button>
      </div>

      {/* Timer Widget — désactivé (fonctionnalité en cours) */}
      {false && <TimerWidget />}

      {/* Manager KPIs (if applicable) */}
      {isManager && managerStats && (
        <>
          <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
            <h2 className="text-lg font-semibold text-slate-800 dark:text-white mb-4">
              {t('dashboard.teamOverview', 'Vue d\'ensemble équipe')}
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <KpiCard
              label={t('dashboard.totalHours', 'Heures totales (mois)')}
              value={Number(managerStats.total_hours_this_month).toFixed(0)}
              icon={<TrendingUp size={18} className="sm:w-5 sm:h-5" />}
            />
            <KpiCard
              label={t('dashboard.activeEmployees', 'Employés actifs')}
              value={managerStats.active_employees || 0}
              icon={<Users size={18} className="sm:w-5 sm:h-5" />}
            />
            <button onClick={() => navigate('/approvals')} className="text-left">
              <KpiCard
                label={t('dashboard.pendingApprovals', 'Validations en attente')}
                value={pendingApprovals.length}
                icon={<CheckSquare size={18} className="sm:w-5 sm:h-5" />}
              />
            </button>
            <KpiCard
              label={t('dashboard.overtime', 'Heures supplémentaires')}
              value={Number(managerStats.overtime_hours).toFixed(0)}
              icon={<TrendingUp size={18} className="sm:w-5 sm:h-5" />}
            />
          </div>
        </>
      )}

      {/* Recent entries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <Card>
          <CardHeader
            title={t('dashboard.thisWeek', 'Cette semaine')}
            action={
              thisWeekProjects.length > projectsPerPage && (
                <span className="text-xs text-slate-400">
                  {thisWeekProjects.length} projet{thisWeekProjects.length > 1 ? 's' : ''}
                </span>
              )
            }
          />
          {thisWeekProjects.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-xs sm:text-sm">
              Aucun projet assigné
            </div>
          ) : (
            <>
              <div className="space-y-2">
                {thisWeekPaginated.map(project => (
                  <div
                    key={project.project_id}
                    className="p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                  >
                    <div className="flex items-start gap-2">
                      <Briefcase size={16} className="text-indigo-600 dark:text-indigo-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                          {project.project_name}
                        </p>
                        {project.client_name && (
                          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                            {project.client_name}
                          </p>
                        )}
                        {project.client_address && (
                          <div className="flex items-start gap-1 mt-1">
                            <MapPin size={12} className="text-slate-400 mt-0.5 flex-shrink-0" />
                            <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                              {project.client_address}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {thisWeekTotalPages > 1 && (
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                  <button
                    onClick={() => setThisWeekPage(p => Math.max(1, p - 1))}
                    disabled={thisWeekPage === 1}
                    className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <span className="text-xs text-slate-500">
                    Page {thisWeekPage} / {thisWeekTotalPages}
                  </span>
                  <button
                    onClick={() => setThisWeekPage(p => Math.min(thisWeekTotalPages, p + 1))}
                    disabled={thisWeekPage === thisWeekTotalPages}
                    className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              )}
            </>
          )}
        </Card>

        {/* Next week projects (only if Wednesday or later) */}
        {showNextWeek && (
          <Card>
            <CardHeader
              title={t('dashboard.nextWeek', 'Semaine prochaine')}
              action={
                nextWeekProjects.length > projectsPerPage && (
                  <span className="text-xs text-slate-400">
                    {nextWeekProjects.length} projet{nextWeekProjects.length > 1 ? 's' : ''}
                  </span>
                )
              }
            />
            {nextWeekProjects.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-xs sm:text-sm">
                Aucun projet assigné
              </div>
            ) : (
              <>
                <div className="space-y-2">
                  {nextWeekPaginated.map(project => (
                    <div
                      key={project.project_id}
                      className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                    >
                      <div className="flex items-start gap-2">
                        <Briefcase size={16} className="text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                            {project.project_name}
                          </p>
                          {project.client_name && (
                            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                              {project.client_name}
                            </p>
                          )}
                          {project.client_address && (
                            <div className="flex items-start gap-1 mt-1">
                              <MapPin size={12} className="text-slate-400 mt-0.5 flex-shrink-0" />
                              <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                                {project.client_address}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                {nextWeekTotalPages > 1 && (
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
                    <button
                      onClick={() => setNextWeekPage(p => Math.max(1, p - 1))}
                      disabled={nextWeekPage === 1}
                      className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft size={16} />
                    </button>
                    <span className="text-xs text-slate-500">
                      Page {nextWeekPage} / {nextWeekTotalPages}
                    </span>
                    <button
                      onClick={() => setNextWeekPage(p => Math.min(nextWeekTotalPages, p + 1))}
                      disabled={nextWeekPage === nextWeekTotalPages}
                      className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                )}
              </>
            )}
          </Card>
        )}
      </div>

      {/* Manager chart */}
      {isManager && managerStats && managerStats.monthly_hours.length > 0 && (
        <Card>
          <CardHeader title={t('dashboard.monthlyTrend', 'Évolution mensuelle')} />
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={managerStats.monthly_hours}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
              <XAxis dataKey="month" stroke={chartColors.text} tick={{ fill: chartColors.text }} fontSize={12} />
              <YAxis stroke={chartColors.text} tick={{ fill: chartColors.text }} fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: chartColors.tooltipBg,
                  border: `1px solid ${chartColors.tooltipBorder}`,
                  borderRadius: '8px',
                  color: chartColors.text,
                }}
              />
              <Bar dataKey="hours" fill={chartColors.primary} name="Heures normales" radius={[4, 4, 0, 0]} />
              <Bar dataKey="overtime" fill={chartColors.warning} name="Heures supp." radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      <QuickTimesheetModal open={showQuickEntry} onClose={() => setShowQuickEntry(false)} />
      <TimeOffRequestModal open={showAbsenceModal} onClose={() => setShowAbsenceModal(false)} />
    </div>
  )
}

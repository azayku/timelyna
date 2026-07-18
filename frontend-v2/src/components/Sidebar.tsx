import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Clock, CheckSquare, Users, FolderOpen,
  Building2, BarChart2, CalendarDays, Settings,
  Star, Shield, Mail, TrendingUp, Calendar, ScrollText, LogOut, User
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../lib/authStore'
import { useProxyStore } from '../lib/proxyStore'
import { useManagerApprovals } from '../features/approvals/hooks'
import { useFinanceLicense } from '../features/finance/useFinanceLicense'
import Avatar from './ui/Avatar'
import { displayNameFromUser, initialsFromUser } from '../utils/userDisplay'

type Role = 'employee' | 'manager' | 'admin' | 'finance' | 'payroll'

interface NavItem {
  to: string
  label: string
  icon: React.ReactNode
  roles?: Role[]   // undefined = visible to all authenticated users
  badge?: number
}

interface NavSection {
  group: string
  roles?: Role[]   // undefined = visible to all
  items: NavItem[]
}

export default function Sidebar() {
  const { t } = useTranslation()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const isProxy = useProxyStore((s) => s.isProxy)
  const role = (user?.role ?? 'employee') as Role
  const { isActive: financeLicenseActive } = useFinanceLicense()

  // Live pending approvals badge — only for managers/admins
  const isValidator = ['manager', 'admin', 'payroll'].includes(role)
  const { data: pendingApprovals = [] } = useManagerApprovals('pending')
  const pendingCount = isValidator ? pendingApprovals.length : 0

  const NAV: NavSection[] = [
    {
      group: t('nav.main'),
      items: [
        { to: '/', label: t('nav.dashboard'), icon: <LayoutDashboard size={16} /> },
      ],
    },
    {
      group: t('nav.timesheet'),
      items: [
        { to: '/timesheet/my-timesheets', label: t('nav.myTimesheets', 'Mes pointages'), icon: <Clock size={16} /> },
        {
          to: '/approvals',
          label: t('nav.approvals'),
          icon: <CheckSquare size={16} />,
          roles: ['manager', 'admin', 'payroll'],
          badge: pendingCount,
        },
        { to: '/history', label: t('nav.history', 'Historique'), icon: <ScrollText size={16} /> },
        {
          to: '/manager/absences',
          label: t('nav.teamAbsences'),
          icon: <CalendarDays size={16} />,
          roles: ['manager', 'admin'],
        },
        { to: '/calendar', label: t('nav.calendar'), icon: <Calendar size={16} /> },
      ],
    },
    {
      group: t('nav.management', 'GESTION'),
      roles: ['manager', 'admin'],
      items: [
        { to: '/manager/team', label: t('nav.myTeam', 'Mon équipe'), icon: <Users size={16} /> },
        { to: '/manager/projects', label: t('nav.myProjects', 'Mes projets'), icon: <FolderOpen size={16} /> },
        { to: '/manager/organizations', label: t('nav.myOrganizations', 'Mes organisations'), icon: <Building2 size={16} /> },
      ],
    },
    {
      group: t('nav.finance'),
      roles: ['finance', 'admin'],
      items: [
        { to: '/finance/dashboard', label: t('nav.financeDashboard'), icon: <TrendingUp size={16} /> },
        { to: '/finance/invoices', label: t('nav.invoices'), icon: <BarChart2 size={16} /> },
        { to: '/finance/reports', label: t('nav.financeReports'), icon: <BarChart2 size={16} /> },
        { to: '/finance/advanced-reports', label: t('nav.advancedReports', 'Rapports avancés'), icon: <BarChart2 size={16} /> },
      ],
    },
    {
      group: t('nav.admin'),
      roles: ['admin'],
      items: [
        { to: '/admin/users', label: t('nav.users'), icon: <Users size={16} /> },
        { to: '/admin/organizations', label: t('nav.organizations'), icon: <Building2 size={16} /> },
        { to: '/admin/clients', label: t('nav.clients'), icon: <Building2 size={16} /> },
        { to: '/admin/projects', label: t('nav.projects'), icon: <FolderOpen size={16} /> },
        { to: '/budget', label: t('nav.budget', 'Budget'), icon: <TrendingUp size={16} /> },
        { to: '/admin/availability', label: t('nav.availability'), icon: <CalendarDays size={16} /> },
        { to: '/admin/hours-report', label: t('nav.hoursReport'), icon: <BarChart2 size={16} /> },
        { to: '/admin/skill-rates', label: t('nav.skillRates'), icon: <Star size={16} /> },
        { to: '/admin/email-templates', label: t('nav.emailTemplates'), icon: <Mail size={16} /> },
        { to: '/admin/license', label: t('nav.license'), icon: <Shield size={16} /> },
        { to: '/admin/settings', label: t('nav.orgSettings'), icon: <Settings size={16} /> },
        { to: '/admin/proxy/logs', label: t('nav.proxyLogs'), icon: <ScrollText size={16} /> },
        { to: '/admin/audit-logs', label: 'Audit', icon: <Shield size={16} /> },
      ],
    },
    {
      group: t('nav.account'),
      items: [
        { to: '/profile', label: t('nav.profile', 'Mon profil'), icon: <User size={16} /> },
      ],
    },
  ]

  // Filter sections and items by role; in proxy mode hide admin/finance
  // Hide finance section if license is not active
  const visibleNav = NAV
    .filter(section => {
      if (isProxy && section.roles?.includes('admin')) return false
      if (isProxy && section.roles?.includes('finance')) return false
      if (section.roles?.includes('finance') && !financeLicenseActive) return false
      if (!section.roles) return true
      return section.roles.includes(role)
    })
    .map(section => ({
      ...section,
      items: section.items.filter(item => !item.roles || item.roles.includes(role)),
    }))
    .filter(section => section.items.length > 0)

  const displayName = displayNameFromUser(user)
  const initials = initialsFromUser(user)

  return (
    <aside className="w-60 flex-shrink-0 flex flex-col h-screen bg-slate-900 dark:bg-slate-950 overflow-y-auto">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-slate-800">
        <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
          <Clock size={16} className="text-white" />
        </div>
        <span className="text-white font-bold text-base tracking-tight">Timelyna</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {visibleNav.map((section) => (
          <div key={section.group}>
            <p className="px-3 mb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
              {section.group}
            </p>
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  aria-current={undefined}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                    }`
                  }
                >
                  <span className="flex-shrink-0">{item.icon}</span>
                  <span className="flex-1 truncate">{item.label}</span>
                  {item.badge != null && item.badge > 0 && (
                    <span className="inline-flex items-center justify-center w-5 h-5 text-[10px] font-bold bg-red-500 text-white rounded-full">
                      {item.badge > 9 ? '9+' : item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* User footer */}
      <div className="px-4 py-4 border-t border-slate-800">
        <div className="flex items-center gap-3">
          <Avatar name={displayName} initials={initials} size="sm" />
          <div className="flex-1 min-w-0">
            <p className="text-white text-xs font-semibold truncate">{displayName}</p>
            <p className="text-slate-400 text-[10px] truncate capitalize">{user?.role}</p>
          </div>
          <button
            onClick={() => void logout()}
            aria-label={t('nav.logout', 'Déconnexion')}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  )
}

import { Outlet, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Sidebar from './Sidebar'
import Header from './Header'
import ProxyBanner from './ProxyBanner'
import BottomNav from './BottomNav'
import LicenseBanner from '../features/license/LicenseBanner'
import ErrorBoundary from './ErrorBoundary'
import { useProxyStore } from '../lib/proxyStore'
import OnboardingWizard, { useOnboarding } from './OnboardingWizard'
import { useAuthStore } from '../lib/authStore'

type PageRoute = {
  titleKey: string
  breadcrumbKeys: string[]
}

const PAGE_ROUTES: Record<string, PageRoute> = {
  '/': { titleKey: 'layout.pageTitles.dashboard', breadcrumbKeys: ['nav.main', 'layout.pageTitles.dashboard'] },
  '/timesheet/my-timesheets': { titleKey: 'layout.pageTitles.myTimesheets', breadcrumbKeys: ['nav.timesheet', 'layout.pageTitles.myTimesheets'] },
  '/timesheet/drafts': { titleKey: 'layout.pageTitles.myTimesheets', breadcrumbKeys: ['nav.timesheet', 'layout.pageTitles.myTimesheets'] },
  '/submissions': { titleKey: 'layout.pageTitles.myTimesheets', breadcrumbKeys: ['nav.timesheet', 'layout.pageTitles.myTimesheets'] },
  '/approvals': { titleKey: 'layout.pageTitles.approvals', breadcrumbKeys: ['nav.timesheet', 'layout.pageTitles.approvals'] },
  '/history': { titleKey: 'layout.pageTitles.history', breadcrumbKeys: ['nav.timesheet', 'layout.pageTitles.history'] },
  '/absences': { titleKey: 'layout.pageTitles.history', breadcrumbKeys: ['nav.timesheet', 'layout.pageTitles.history'] },
  '/manager/absences': { titleKey: 'layout.pageTitles.teamAbsences', breadcrumbKeys: ['nav.main', 'layout.pageTitles.teamAbsences'] },
  '/finance/dashboard': { titleKey: 'layout.pageTitles.financeDashboard', breadcrumbKeys: ['nav.finance', 'layout.pageTitles.financeDashboard'] },
  '/finance/invoices': { titleKey: 'layout.pageTitles.invoices', breadcrumbKeys: ['nav.finance', 'layout.pageTitles.invoices'] },
  '/finance/reports': { titleKey: 'layout.pageTitles.financeReports', breadcrumbKeys: ['nav.finance', 'layout.pageTitles.financeReports'] },
  '/admin/users': { titleKey: 'layout.pageTitles.users', breadcrumbKeys: ['nav.admin', 'layout.pageTitles.users'] },
  '/admin/clients': { titleKey: 'layout.pageTitles.clients', breadcrumbKeys: ['nav.admin', 'layout.pageTitles.clients'] },
  '/admin/projects': { titleKey: 'layout.pageTitles.projects', breadcrumbKeys: ['nav.admin', 'layout.pageTitles.projects'] },
  '/admin/availability': { titleKey: 'layout.pageTitles.availability', breadcrumbKeys: ['nav.admin', 'layout.pageTitles.availability'] },
  '/admin/hours-report': { titleKey: 'layout.pageTitles.hoursReport', breadcrumbKeys: ['nav.admin', 'layout.pageTitles.hoursReport'] },
  '/admin/skill-rates': { titleKey: 'layout.pageTitles.skillRates', breadcrumbKeys: ['nav.admin', 'layout.pageTitles.skillRates'] },
  '/admin/email-templates': { titleKey: 'layout.pageTitles.emailTemplates', breadcrumbKeys: ['nav.admin', 'layout.pageTitles.emailTemplates'] },
  '/admin/license': { titleKey: 'layout.pageTitles.license', breadcrumbKeys: ['nav.admin', 'layout.pageTitles.license'] },
  '/admin/settings': { titleKey: 'layout.pageTitles.orgSettings', breadcrumbKeys: ['nav.admin', 'layout.pageTitles.orgSettings'] },
  '/profile': { titleKey: 'layout.pageTitles.profile', breadcrumbKeys: ['nav.account', 'layout.pageTitles.profile'] },
  '/settings/password': { titleKey: 'layout.pageTitles.profile', breadcrumbKeys: ['nav.account', 'layout.pageTitles.profile'] },
  '/settings/notifications': { titleKey: 'layout.pageTitles.profile', breadcrumbKeys: ['nav.account', 'layout.pageTitles.profile'] },
}

export default function Layout() {
  const { t } = useTranslation()
  const location = useLocation()
  const routes = PAGE_ROUTES[location.pathname]
  const meta = routes ? {
    title: t(routes.titleKey),
    breadcrumb: routes.breadcrumbKeys.map(key => t(key))
  } : { title: 'Timelyn', breadcrumb: [] }
  const isProxy = useProxyStore(s => s.isProxy)
  const role = useAuthStore(s => s.user?.role)
  const { show: showOnboarding, complete: completeOnboarding } = useOnboarding(role === 'admin')

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100 dark:bg-slate-900">
      {showOnboarding && <OnboardingWizard onComplete={completeOnboarding} />}
      <div className="hidden md:flex">
        <Sidebar />
      </div>
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {isProxy && <ProxyBanner />}
        <LicenseBanner />
        <Header title={meta.title} breadcrumb={meta.breadcrumb} />
        <main className="flex-1 overflow-y-auto p-6 pb-24 md:pb-6 dark:bg-slate-900">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
        {/* Bottom nav — mobile only */}
        <div className="md:hidden">
          <BottomNav />
        </div>
      </div>
    </div>
  )
}

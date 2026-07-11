import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useThemeStore } from './lib/themeStore'
import { useAuthStore } from './lib/authStore'
import Layout from './components/Layout'
import PrivateRoute from './components/PrivateRoute'
import SetupPage from './pages/SetupPage'
import LoginPage from './pages/LoginPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import UnifiedDashboardPage from './pages/UnifiedDashboardPage'
import MyTimesheetsPage from './pages/MyTimesheetsPage'
import ApprovalsPage from './pages/ApprovalsPage'
import ManagerApprovalsPage from './pages/ManagerApprovalsPage'
import ValidationHistoryPage from './pages/ValidationHistoryPage'
import ManagerAbsencesPage from './pages/ManagerAbsencesPage'
import MyProfilePage from './pages/MyProfilePage'
import StatisticsPage from './pages/StatisticsPage'
import AdminUsersPage from './pages/AdminUsersPage'
import AdminClientsPage from './pages/AdminClientsPage'
import AdminProjectsPage from './pages/AdminProjectsPage'
import AvailabilityPage from './pages/AvailabilityPage'
import HoursReportPage from './pages/HoursReportPage'
import InvoicesPage from './pages/InvoicesPage'
import InvoiceDetailPage from './pages/InvoiceDetailPage'
import FinanceDashboardPage from './pages/FinanceDashboardPage'
import FinancialReportsPage from './pages/FinancialReportsPage'
import FinanceLicensePage from './pages/FinanceLicensePage'
import OrgSettingsPage from './pages/OrgSettingsPage'
import LicenseSettingsPage from './pages/LicenseSettingsPage'
import CalendarPage from './pages/CalendarPage'
import AdminOrganizationsPage from './pages/AdminOrganizationsPage'
import ProxyLogsPage from './pages/ProxyLogsPage'
import AuditLogPage from './pages/AuditLogPage'
import SkillRatesPage from './pages/SkillRatesPage'
import EmailTemplatesPage from './pages/EmailTemplatesPage'
import FinanceLicenseRoute from './components/FinanceLicenseRoute'
import ManagerOrganizationsPage from './pages/ManagerOrganizationsPage'
import ManagerTeamPage from './pages/ManagerTeamPage'
import ManagerProjectsPage from './pages/ManagerProjectsPage'
import BudgetDashboardPage from './pages/BudgetDashboardPage'
import { fetchSetupStatus } from './features/setup/api'

// ─── Role-based route guard ───────────────────────────────────────────────────
function RoleRoute({ roles, children }: { roles: string[]; children: React.ReactNode }) {
  const role = useAuthStore((s) => s.user?.role ?? 'employee')
  if (!roles.includes(role)) return <Navigate to="/" replace />
  return <>{children}</>
}

// ─── Setup guard — redirects to /setup when not installed ────────────────────
function SetupGuard({ children }: { children: React.ReactNode }) {
  const [checking, setChecking] = useState(true)
  const [installed, setInstalled] = useState<boolean | null>(null)

  useEffect(() => {
    fetchSetupStatus()
      .then(s => setInstalled(s.is_installed))
      .catch(() => setInstalled(true)) // if API unreachable, don't block
      .finally(() => setChecking(false))
  }, [])

  if (checking) return null // invisible while checking

  if (!installed) return <Navigate to="/setup" replace />

  return <>{children}</>
}

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const { dark } = useThemeStore()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  return (
    <BrowserRouter basename={import.meta.env.VITE_BASE_PATH || '/'}>
      <Routes>
        {/* Setup wizard — only when not installed */}
        <Route path="/setup" element={<SetupPage />} />

        {/* Public routes — guarded: redirect to /setup if not installed */}
        <Route path="/login" element={<SetupGuard><LoginPage /></SetupGuard>} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        <Route element={<PrivateRoute />}>
          <Route element={<Layout />}>
            {/* Dashboard */}
            <Route path="/" element={<UnifiedDashboardPage />} />

            {/* Timesheet — all authenticated */}
            <Route path="/timesheet/my-timesheets" element={<MyTimesheetsPage />} />
            <Route path="/timesheet/drafts" element={<MyTimesheetsPage />} /> {/* Redirect old route */}
            <Route path="/submissions" element={<MyTimesheetsPage />} /> {/* Redirect old route */}
            <Route path="/history" element={<ValidationHistoryPage />} />
            <Route path="/absences" element={<ValidationHistoryPage />} /> {/* Redirect old route */}
            <Route path="/calendar" element={<CalendarPage />} />

            {/* Approvals — manager + admin + payroll */}
            <Route path="/approvals" element={<RoleRoute roles={['manager','admin','payroll']}><ManagerApprovalsPage /></RoleRoute>} />
            <Route path="/manager/absences" element={<RoleRoute roles={['manager','admin']}><ManagerAbsencesPage /></RoleRoute>} />
            <Route path="/manager/organizations" element={<RoleRoute roles={['manager','admin']}><ManagerOrganizationsPage /></RoleRoute>} />
            <Route path="/manager/team" element={<RoleRoute roles={['manager','admin']}><ManagerTeamPage /></RoleRoute>} />
            <Route path="/manager/projects" element={<RoleRoute roles={['manager','admin']}><ManagerProjectsPage /></RoleRoute>} />
            <Route path="/budget" element={<RoleRoute roles={['admin']}><BudgetDashboardPage /></RoleRoute>} />
            
            {/* Admin approvals (keep old page for admin/payroll if needed) */}
            <Route path="/admin/approvals" element={<RoleRoute roles={['admin','payroll']}><ApprovalsPage /></RoleRoute>} />

            {/* Reporting — manager + admin + finance */}
            <Route path="/statistics" element={<RoleRoute roles={['manager','admin','finance']}><StatisticsPage /></RoleRoute>} />

            {/* Finance — finance + admin (with license check) */}
            <Route path="/finance/dashboard" element={<RoleRoute roles={['finance','admin']}><FinanceLicenseRoute><FinanceDashboardPage /></FinanceLicenseRoute></RoleRoute>} />
            <Route path="/finance/invoices" element={<RoleRoute roles={['finance','admin']}><FinanceLicenseRoute><InvoicesPage /></FinanceLicenseRoute></RoleRoute>} />
            <Route path="/finance/invoices/:id" element={<RoleRoute roles={['finance','admin']}><FinanceLicenseRoute><InvoiceDetailPage /></FinanceLicenseRoute></RoleRoute>} />
            <Route path="/finance/reports" element={<RoleRoute roles={['finance','admin']}><FinanceLicenseRoute><FinancialReportsPage /></FinanceLicenseRoute></RoleRoute>} />
            <Route path="/finance/advanced-reports" element={<Navigate to="/finance/reports" replace />} />
            <Route path="/finance/license" element={<RoleRoute roles={['finance','admin']}><FinanceLicensePage /></RoleRoute>} />

            {/* Admin — admin only */}
            <Route path="/admin/organizations" element={<RoleRoute roles={['admin']}><AdminOrganizationsPage /></RoleRoute>} />
            <Route path="/admin/users" element={<RoleRoute roles={['admin']}><AdminUsersPage /></RoleRoute>} />
            <Route path="/admin/clients" element={<RoleRoute roles={['admin']}><AdminClientsPage /></RoleRoute>} />
            <Route path="/admin/projects" element={<RoleRoute roles={['admin']}><AdminProjectsPage /></RoleRoute>} />
            <Route path="/admin/availability" element={<RoleRoute roles={['admin','manager']}><AvailabilityPage /></RoleRoute>} />
            <Route path="/admin/hours-report" element={<RoleRoute roles={['admin','manager']}><HoursReportPage /></RoleRoute>} />
            <Route path="/admin/skill-rates" element={<RoleRoute roles={['admin']}><SkillRatesPage /></RoleRoute>} />
            <Route path="/admin/email-templates" element={<RoleRoute roles={['admin']}><EmailTemplatesPage /></RoleRoute>} />
            <Route path="/admin/license" element={<RoleRoute roles={['admin']}><LicenseSettingsPage /></RoleRoute>} />
            <Route path="/admin/license/settings" element={<RoleRoute roles={['admin']}><LicenseSettingsPage /></RoleRoute>} />
            <Route path="/licenses" element={<LicenseSettingsPage />} />
            <Route path="/admin/finance-license" element={<RoleRoute roles={['admin','finance']}><FinanceLicensePage /></RoleRoute>} />
            <Route path="/admin/settings" element={<RoleRoute roles={['admin']}><OrgSettingsPage /></RoleRoute>} />
            <Route path="/admin/proxy/logs" element={<RoleRoute roles={['admin']}><ProxyLogsPage /></RoleRoute>} />
            <Route path="/admin/audit-logs" element={<RoleRoute roles={['admin']}><AuditLogPage /></RoleRoute>} />

            {/* User settings — all authenticated */}
            <Route path="/profile" element={<MyProfilePage />} />
            <Route path="/settings/password" element={<MyProfilePage />} /> {/* Redirect old route */}
            <Route path="/settings/notifications" element={<MyProfilePage />} /> {/* Redirect old route */}

            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

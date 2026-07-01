import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { X, BarChart2, Receipt, Users, Building2, FolderOpen, Shield, LogOut, Settings, Globe, User, Calendar as CalendarIcon, Clock, CalendarDays, CheckSquare, TrendingUp, ScrollText } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../lib/authStore'
import { useFinanceLicense } from '../features/finance/useFinanceLicense'
import { displayNameFromUser } from '../utils/userDisplay'
import QuickTimesheetModal from './modals/QuickTimesheetModal'
import TimeOffRequestModal from './modals/TimeOffRequestModal'

interface Props { onClose: () => void }

const LANGS = ['fr', 'en', 'it'] as const

export default function MobileMenu({ onClose }: Props) {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const { i18n, t } = useTranslation()
  const role = user?.role ?? 'employee'
  const { isActive: financeLicenseActive } = useFinanceLicense()
  const [showTimesheetModal, setShowTimesheetModal] = useState(false)
  const [showAbsenceModal, setShowAbsenceModal] = useState(false)

  const displayName = displayNameFromUser(user)
  const isValidator = ['admin', 'payroll', 'manager'].includes(role)

  const link = (to: string, icon: React.ReactNode, label: string) => (
    <NavLink
      key={to}
      to={to}
      onClick={onClose}
      className={({ isActive }) =>
        `flex items-center gap-4 px-4 py-3.5 rounded-xl text-base font-medium transition-colors ${
          isActive
            ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
            : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
        }`
      }
    >
      <span className="text-slate-500 dark:text-slate-400">{icon}</span>
      {label}
    </NavLink>
  )

  const actionButton = (icon: React.ReactNode, label: string, onClick: () => void) => (
    <button
      onClick={() => {
        onClick()
        onClose()
      }}
      className="flex items-center gap-4 px-4 py-3.5 rounded-xl text-base font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
    >
      <span className="text-slate-500 dark:text-slate-400">{icon}</span>
      {label}
    </button>
  )

  const sectionTitle = (label: string) => (
    <p className="px-4 pt-3 pb-1 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">{label}</p>
  )

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-white dark:bg-slate-900">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <p className="font-semibold text-slate-900 dark:text-white">{displayName}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 capitalize">{user?.role} · {user?.email}</p>
        </div>
        <button onClick={onClose} className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800">
          <X size={22} className="text-slate-600 dark:text-slate-400" />
        </button>
      </div>

      {/* Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {sectionTitle(t('mobileMenu.quickActions', 'Actions rapides'))}
        {actionButton(<Clock size={20} />, t('mobileMenu.quickEntry', 'Saisie rapide'), () => setShowTimesheetModal(true))}
        {actionButton(<CalendarDays size={20} />, t('mobileMenu.declareAbsence', 'Declarer une absence'), () => setShowAbsenceModal(true))}

        {sectionTitle(t('mobileMenu.navigation', 'Navigation'))}
        {link('/calendar', <CalendarIcon size={20} />, t('nav.calendar', 'Calendrier'))}
        {link('/history', <ScrollText size={20} />, t('nav.history', 'Historique'))}
        {link('/statistics', <BarChart2 size={20} />, t('nav.statistics', 'Statistiques'))}

        {isValidator && (
          <>
            {sectionTitle(t('mobileMenu.management', 'Gestion'))}
            {link('/approvals', <CheckSquare size={20} />, t('nav.approvals', 'Validations'))}
            {link('/manager/absences', <CalendarDays size={20} />, t('nav.teamAbsences', 'Absences equipe'))}
          </>
        )}

        {['manager', 'admin'].includes(role) && (
          <>
            {link('/manager/team', <Users size={20} />, t('nav.myTeam', 'Mon equipe'))}
            {link('/manager/projects', <FolderOpen size={20} />, t('nav.myProjects', 'Mes projets'))}
            {link('/manager/organizations', <Building2 size={20} />, t('nav.myOrganizations', 'Mes organisations'))}
          </>
        )}

        {['finance', 'admin'].includes(role) && financeLicenseActive && (
          <>
            {sectionTitle(t('mobileMenu.finance', 'Finance'))}
            {link('/finance/dashboard', <TrendingUp size={20} />, t('nav.financeDashboard', 'Dashboard Finance'))}
            {link('/finance/reports', <BarChart2 size={20} />, t('nav.reports', 'Rapports'))}
            {link('/finance/invoices', <Receipt size={20} />, t('nav.invoices', 'Factures'))}
          </>
        )}

        {role === 'admin' && (
          <>
            {sectionTitle(t('mobileMenu.administration', 'Administration'))}
            {link('/admin/users', <Users size={20} />, t('nav.users', 'Utilisateurs'))}
            {link('/admin/organizations', <Building2 size={20} />, t('nav.organizations', 'Organisations'))}
            {link('/admin/clients', <Building2 size={20} />, t('nav.clients', 'Clients'))}
            {link('/admin/projects', <FolderOpen size={20} />, t('nav.projects', 'Projets'))}
            {link('/admin/availability', <CalendarIcon size={20} />, t('nav.availability', 'Disponibilites'))}
            {link('/admin/hours-report', <BarChart2 size={20} />, t('nav.hoursReport', 'Rapport heures'))}
            {link('/admin/skill-rates', <Settings size={20} />, t('nav.skillRates', 'Competences et Taux'))}
            {link('/admin/email-templates', <Settings size={20} />, t('nav.emailTemplates', 'Modeles email'))}
            {link('/admin/license', <Shield size={20} />, t('nav.license', 'Licence'))}
            {link('/admin/settings', <Settings size={20} />, t('nav.orgSettings', 'Parametres organisation'))}
          </>
        )}

        {sectionTitle(t('mobileMenu.account', 'Compte'))}
        {link('/profile', <User size={20} />, t('nav.profile', 'Mon profil'))}
      </div>

      <QuickTimesheetModal open={showTimesheetModal} onClose={() => setShowTimesheetModal(false)} />
      <TimeOffRequestModal open={showAbsenceModal} onClose={() => setShowAbsenceModal(false)} />

      <div className="px-3 py-3 border-t border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2 px-4 py-2">
          <Globe size={16} className="text-slate-400 flex-shrink-0" />
          <span className="text-xs font-medium text-slate-500 mr-1">{t('mobileMenu.language', 'Langue')}</span>
          <div className="flex items-center gap-1">
            {LANGS.map((l) => (
              <button key={l} onClick={() => i18n.changeLanguage(l)}
                className={`text-xs px-2 py-1 rounded font-semibold uppercase transition-colors ${
                  i18n.language === l
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
                }`}>
                {l}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="px-3 py-4 border-t border-slate-100 dark:border-slate-800">
        <button
          onClick={() => { void logout(); onClose() }}
          className="w-full flex items-center gap-4 px-4 py-3.5 rounded-xl text-base font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
        >
          <LogOut size={20} />
          {t('nav.logout', 'Deconnexion')}
        </button>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Home, Clock, Plus, History, CheckSquare, Menu, Calendar } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../lib/authStore'
import { useManagerApprovals } from '../features/approvals/hooks'
import MobileMenu from './MobileMenu'
import QuickTimesheetModal from './modals/QuickTimesheetModal'
import TimeOffRequestModal from './modals/TimeOffRequestModal'

export default function BottomNav() {
  const user = useAuthStore((s) => s.user)
  const role = user?.role ?? 'employee'
  const [menuOpen, setMenuOpen] = useState(false)
  const [showQuickMenu, setShowQuickMenu] = useState(false)
  const [showTimesheetModal, setShowTimesheetModal] = useState(false)
  const [showAbsenceModal, setShowAbsenceModal] = useState(false)
  const { t } = useTranslation()

  const { data: pendingApprovals = [] } = useManagerApprovals('pending')
  const pendingCount = pendingApprovals.length

  const isValidator = ['admin', 'payroll', 'manager'].includes(role)

  const navCls = ({ isActive }: { isActive: boolean }) =>
    `flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl transition-colors min-w-[56px] ${
      isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400'
    }`

  return (
    <>
      <nav className="fixed bottom-0 left-0 right-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 z-40">
        <div className="flex items-center justify-around px-2 py-1">

          <NavLink to="/" className={navCls}>
            <Home size={22} />
            <span className="text-[10px] font-medium">{t('nav.home', 'Accueil')}</span>
          </NavLink>

          <NavLink to="/timesheet/my-timesheets" className={navCls}>
            <Clock size={22} />
            <span className="text-[10px] font-medium">{t('nav.timesheets', 'Pointages')}</span>
          </NavLink>

          {/* Raccourcis button - Icon only */}
          <div className="relative">
            <button
              onClick={() => setShowQuickMenu(!showQuickMenu)}
              className="flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl text-indigo-600 dark:text-indigo-400 min-w-[56px]"
            >
              <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center">
                <Plus size={20} className="text-white" />
              </div>
            </button>

            {/* Quick menu popup */}
            {showQuickMenu && (
              <>
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 flex flex-col gap-2 animate-in fade-in slide-in-from-bottom-2 duration-200">
                  <button
                    onClick={() => {
                      setShowQuickMenu(false)
                      setShowTimesheetModal(true)
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors whitespace-nowrap text-sm font-medium"
                  >
                    <Clock size={16} />
                    {t('bottomNav.quickEntry', 'Saisie rapide')}
                  </button>
                  <button
                    onClick={() => {
                      setShowQuickMenu(false)
                      setShowAbsenceModal(true)
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors whitespace-nowrap text-sm font-medium"
                  >
                    <Calendar size={16} />
                    {t('bottomNav.declareAbsence', 'Déclarer absence')}
                  </button>
                </div>
                <div
                  className="fixed inset-0 -z-10"
                  onClick={() => setShowQuickMenu(false)}
                />
              </>
            )}
          </div>

          <NavLink to="/history" className={navCls}>
            <History size={22} />
            <span className="text-[10px] font-medium">{t('nav.history', 'Historique')}</span>
          </NavLink>

          {isValidator ? (
            <NavLink to="/approvals" className={navCls}>
              <div className="relative">
                <CheckSquare size={22} />
                {pendingCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                    {pendingCount > 9 ? '9+' : pendingCount}
                  </span>
                )}
              </div>
              <span className="text-[10px] font-medium">{t('nav.approvals', 'Validations')}</span>
            </NavLink>
          ) : (
            <button
              onClick={() => setMenuOpen(true)}
              className="flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl text-slate-500 dark:text-slate-400 min-w-[56px]"
            >
              <Menu size={22} />
              <span className="text-[10px] font-medium">Menu</span>
            </button>
          )}

          {isValidator && (
            <button
              onClick={() => setMenuOpen(true)}
              className="flex flex-col items-center gap-0.5 px-3 py-2 rounded-xl text-slate-500 dark:text-slate-400 min-w-[56px]"
            >
              <Menu size={22} />
              <span className="text-[10px] font-medium">Menu</span>
            </button>
          )}

        </div>
      </nav>

      {menuOpen && <MobileMenu onClose={() => setMenuOpen(false)} />}
      
      {/* Modals */}
      <QuickTimesheetModal
        open={showTimesheetModal}
        onClose={() => setShowTimesheetModal(false)}
      />
      <TimeOffRequestModal
        open={showAbsenceModal}
        onClose={() => setShowAbsenceModal(false)}
      />
    </>
  )
}

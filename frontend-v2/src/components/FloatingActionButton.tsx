import { useState } from 'react'
import { Plus, Clock, Calendar, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import QuickTimesheetModal from './modals/QuickTimesheetModal'
import TimeOffRequestModal from './modals/TimeOffRequestModal'

export default function FloatingActionButton() {
  const { t } = useTranslation()
  const [showMenu, setShowMenu] = useState(false)
  const [showTimesheetModal, setShowTimesheetModal] = useState(false)
  const [showAbsenceModal, setShowAbsenceModal] = useState(false)

  const handleTimesheetClick = () => {
    setShowMenu(false)
    setShowTimesheetModal(true)
  }

  const handleAbsenceClick = () => {
    setShowMenu(false)
    setShowAbsenceModal(true)
  }

  return (
    <>
      {/* FAB - Mobile/Tablet only, centered at bottom */}
      <div className="lg:hidden fixed bottom-20 left-1/2 -translate-x-1/2 z-40">
        {/* Action menu */}
        {showMenu && (
          <div className="absolute bottom-16 left-1/2 -translate-x-1/2 flex flex-col gap-2 mb-2 animate-in fade-in slide-in-from-bottom-2 duration-200">
            <button
              onClick={handleTimesheetClick}
              className="flex items-center gap-3 px-5 py-3 bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors whitespace-nowrap"
            >
              <Clock size={20} />
              <span className="text-sm font-semibold">{t('fabs.quickEntry', 'Saisie rapide')}</span>
            </button>
            <button
              onClick={handleAbsenceClick}
              className="flex items-center gap-3 px-5 py-3 bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors whitespace-nowrap"
            >
              <Calendar size={20} />
              <span className="text-sm font-semibold">{t('fabs.declareAbsence', 'Déclarer absence')}</span>
            </button>
          </div>
        )}

        {/* Main FAB button */}
        <button
          onClick={() => setShowMenu(!showMenu)}
          className={`w-16 h-16 rounded-full shadow-2xl flex items-center justify-center transition-all ${
            showMenu
              ? 'bg-slate-700 dark:bg-slate-600 rotate-45 scale-95'
              : 'bg-indigo-600 hover:bg-indigo-700 hover:scale-105'
          }`}
          aria-label={t(showMenu ? 'fabs.closeMenu' : 'fabs.openMenu', showMenu ? 'Fermer' : 'Raccourcis')}
        >
          {showMenu ? (
            <X size={28} className="text-white" />
          ) : (
            <Plus size={28} className="text-white" />
          )}
        </button>

        {/* Backdrop */}
        {showMenu && (
          <div
            className="fixed inset-0 bg-black/20 -z-10"
            onClick={() => setShowMenu(false)}
          />
        )}
      </div>

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

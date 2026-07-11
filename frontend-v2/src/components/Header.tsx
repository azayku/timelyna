import { Sun, Moon } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useThemeStore } from '../lib/themeStore'
import GlobalSearch from './GlobalSearch'
import NotificationBell from '../features/notifications/NotificationBell'
import { useAuthStore } from '../lib/authStore'
import { displayNameFromUser, initialsFromUser } from '../utils/userDisplay'
import { NavLink } from 'react-router-dom'

interface HeaderProps {
  title: string
  breadcrumb?: string[]
}

export default function Header({ title, breadcrumb }: HeaderProps) {
  const { dark, toggle } = useThemeStore()
  const { t } = useTranslation()
  const user = useAuthStore(s => s.user)
  const role = user?.role
  const displayName = displayNameFromUser(user)
  const initials = initialsFromUser(user)

  return (
    <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 px-6 py-3.5 flex items-center justify-between flex-shrink-0">
      {/* Left: title + breadcrumb */}
      <div>
        <h1 className="text-lg font-semibold text-slate-800 dark:text-slate-100">{title}</h1>
        {breadcrumb && (
          <p className="text-xs text-slate-400 mt-0.5">
            {breadcrumb.join(' / ')}
          </p>
        )}
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2">
        {role === 'admin' && <GlobalSearch />}

        {/* Dark mode toggle */}
        <button
          onClick={toggle}
          aria-label={t('common.toggleDarkMode', dark ? 'Activer le mode clair' : 'Activer le mode sombre')}
          className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 transition-colors"
        >
          {dark ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        {/* Notifications */}
        <NotificationBell />

        {/* User avatar + name */}
        <NavLink
          to="/profile"
          className="hidden sm:flex items-center gap-2 pl-2 border-l border-slate-200 dark:border-slate-700 ml-1 hover:opacity-80 transition-opacity"
        >
          <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
            {initials}
          </div>
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300 max-w-[120px] truncate">
            {displayName}
          </span>
        </NavLink>
      </div>
    </header>
  )
}

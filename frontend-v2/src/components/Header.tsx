import { Sun, Moon } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useThemeStore } from '../lib/themeStore'
import GlobalSearch from './GlobalSearch'
import NotificationBell from '../features/notifications/NotificationBell'
import { useAuthStore } from '../lib/authStore'

interface HeaderProps {
  title: string
  breadcrumb?: string[]
}

export default function Header({ title, breadcrumb }: HeaderProps) {
  const { dark, toggle } = useThemeStore()
  const { t } = useTranslation()
  const role = useAuthStore(s => s.user?.role)

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
      </div>
    </header>
  )
}

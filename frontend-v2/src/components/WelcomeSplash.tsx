import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { AuthUser } from '../lib/authStore'
import { useAppConfig } from '../features/app-config/hooks'

interface Props {
  user: AuthUser
  onComplete: () => void
  duration?: number // ms, default 3000
}

export default function WelcomeSplash({ user, onComplete, duration = 3000 }: Props) {
  const { t } = useTranslation()
  const [progress, setProgress] = useState(0)
  const { data: appConfig } = useAppConfig()

  const firstName = user.first_name
    ? user.first_name.charAt(0).toUpperCase() + user.first_name.slice(1).toLowerCase()
    : user.email.split('@')[0].split('.')[0].replace(/^\w/, (c) => c.toUpperCase())

  // Determine display name: if custom app_name, show "CustomName by Timelyna"
  const appNameDisplay = appConfig?.app_name && appConfig.app_name !== 'Timelyna'
    ? `${appConfig.app_name} by Timelyna`
    : appConfig?.app_name || 'Timelyna'

  // Use company logo if available, otherwise fall back to icons8 logo
  const logoSrc = appConfig?.company_logo 
    ? appConfig.company_logo 
    : 'https://img.icons8.com/?size=100&id=20935&format=png&color=ffffff'

  useEffect(() => {
    const startTime = Date.now()
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime
      const pct = Math.min((elapsed / duration) * 100, 100)
      setProgress(pct)
      if (pct >= 100) {
        clearInterval(interval)
        setTimeout(onComplete, 150)
      }
    }, 30)
    return () => clearInterval(interval)
  }, [duration, onComplete])

  const roleLabel: Record<string, string> = {
    admin: t('roles.admin', 'Administrateur'),
    manager: t('roles.manager', 'Manager'),
    employee: t('roles.employee', 'Employé'),
    finance: t('roles.finance', 'Finance'),
    payroll: t('roles.payroll', 'Paie'),
  }

  return (
    <div className="fixed inset-0 z-[999] flex flex-col items-center justify-center bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800">
      {/* Logo */}
      <div className="mb-8 flex flex-col items-center gap-3">
        <div className="w-20 h-20 rounded-2xl bg-white/20 flex items-center justify-center shadow-lg overflow-hidden">
          <img 
            src={logoSrc}
            alt="Application Logo"
            className="w-full h-full object-cover"
          />
        </div>
        <span className="text-white/80 text-sm font-semibold tracking-widest uppercase">{appNameDisplay}</span>
      </div>

      {/* Greeting */}
      <h1 className="text-4xl sm:text-5xl font-bold text-white mb-2 text-center px-6">
        {t('welcome.greeting', 'Bonjour')}, {firstName}&nbsp;!
      </h1>
      <p className="text-indigo-200 text-lg mb-12">
        {roleLabel[user.role] ?? user.role}
      </p>

      {/* Progress bar */}
      <div className="w-64 sm:w-80">
        <div className="h-1.5 bg-white/20 rounded-full overflow-hidden">
          <div
            className="h-full bg-white rounded-full transition-none"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  )
}

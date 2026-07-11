import { useEffect, useState } from 'react'
import { Clock } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { AuthUser } from '../lib/authStore'

interface Props {
  user: AuthUser
  onComplete: () => void
  duration?: number // ms, default 3000
}

export default function WelcomeSplash({ user, onComplete, duration = 3000 }: Props) {
  const { t } = useTranslation()
  const [progress, setProgress] = useState(0)

  const firstName = user.first_name
    ? user.first_name.charAt(0).toUpperCase() + user.first_name.slice(1).toLowerCase()
    : user.email.split('@')[0].split('.')[0].replace(/^\w/, (c) => c.toUpperCase())

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
        <div className="w-16 h-16 rounded-2xl bg-white/20 flex items-center justify-center shadow-lg">
          <Clock size={32} className="text-white" />
        </div>
        <span className="text-white/80 text-sm font-semibold tracking-widest uppercase">Timelyna</span>
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

import { AlertTriangle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../lib/authStore'
import { useDaysUntilExpiry } from './hooks'

export default function LicenseBanner() {
  const user = useAuthStore((s) => s.user)
  const days = useDaysUntilExpiry()

  if (user?.role !== 'admin') return null
  if (days > 60) return null

  return (
    <div className="sticky top-0 z-30 bg-amber-50 border-b border-amber-200 px-4 py-2 flex items-center gap-2 text-amber-800 text-sm">
      <AlertTriangle size={15} className="flex-shrink-0" />
      <span>
        Votre licence expire dans <strong>{days}</strong> jour{days !== 1 ? 's' : ''}.{' '}
        <Link to="/admin/license" className="underline font-medium hover:text-amber-900">
          Renouveler →
        </Link>
      </span>
    </div>
  )
}

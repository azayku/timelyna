import { Lock, AlertTriangle } from 'lucide-react'
import Card from './ui/Card'
import Button from './ui/Button'
import { Link } from 'react-router-dom'

interface FinanceLicenseGateProps {
  isActive: boolean
  isLoading: boolean
  daysLeft: number | null
}

export default function FinanceLicenseGate({ isActive, isLoading, daysLeft }: FinanceLicenseGateProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
        <div className="animate-spin rounded-full h-4 w-4 border border-slate-300 border-t-slate-600"></div>
        Vérification de la licence...
      </div>
    )
  }

  if (!isActive) {
    return (
      <div className="max-w-2xl mx-auto py-16">
        <Card className="border-amber-200 bg-amber-50 dark:bg-amber-900/20">
          <div className="flex gap-4">
            <div className="flex-shrink-0">
              <Lock size={24} className="text-amber-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-bold text-amber-900 dark:text-amber-100">
                Module Finance verrouillé
              </h2>
              <p className="text-sm text-amber-800 dark:text-amber-200 mt-2">
                Le module Finance est une fonctionnalité premium. Vous devez activer une licence Finance Pro pour accéder à cette section.
              </p>
              <div className="mt-4 flex gap-3">
                <Link to="/finance/license">
                  <Button variant="primary">
                    Activer une licence
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  // License active but expiring soon
  if (daysLeft !== null && daysLeft > 0 && daysLeft <= 30) {
    return (
      <div className="mb-4">
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <AlertTriangle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-amber-900">Votre licence expire bientôt</p>
            <p className="text-sm text-amber-800 mt-0.5">
              Votre licence Finance Pro expire dans <strong>{daysLeft} jour{daysLeft > 1 ? 's' : ''}</strong>.
              <Link to="/finance/license" className="underline font-semibold ml-1">
                Renouvelez-la
              </Link>
            </p>
          </div>
        </div>
      </div>
    )
  }

  return null
}

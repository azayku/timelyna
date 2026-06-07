import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Key, AlertTriangle, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useFinanceLicense, useActivateFinanceLicense } from '../features/finance/useFinanceLicense'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

const schema = z.object({
  license_key: z.string().min(1, 'La clé de licence est requise'),
})
type FormData = z.infer<typeof schema>

export default function FinanceLicensePage() {
  const { t } = useTranslation()
  const { isActive, expiresAt, daysLeft, isLoading } = useFinanceLicense()
  const activateMutation = useActivateFinanceLicense()
  const [activationSuccess, setActivationSuccess] = useState(false)

  const { register, handleSubmit, formState: { errors }, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    try {
      await activateMutation.mutateAsync(data.license_key)
      setActivationSuccess(true)
      reset()
      setTimeout(() => setActivationSuccess(false), 5000)
    } catch {
      // error handled via activateMutation.isError
    }
  }

  const getBadge = () => {
    if (!isActive) return { label: 'Inactive', icon: XCircle, cls: 'bg-slate-100 text-slate-600' }
    if (daysLeft !== null && daysLeft <= 0) return { label: 'Expiré', icon: XCircle, cls: 'bg-red-100 text-red-700' }
    if (daysLeft !== null && daysLeft <= 30) return { label: 'Actif', icon: AlertTriangle, cls: 'bg-amber-100 text-amber-700' }
    return { label: 'Actif', icon: CheckCircle, cls: 'bg-emerald-100 text-emerald-700' }
  }

  const badge = getBadge()
  const BadgeIcon = badge.icon
  const showWarning = isActive && daysLeft !== null && daysLeft > 0 && daysLeft <= 30

  if (isLoading) return (
    <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
      <Loader2 size={16} className="animate-spin" /> Chargement…
    </div>
  )

  return (
    <div className="max-w-4xl space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-white">
          {t('finance.licenseTitle', 'Licence Finance Pro')}
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          {t('finance.licenseSubtitle', 'Gérez votre licence pour accéder aux fonctionnalités avancées de facturation et reporting')}
        </p>
      </div>

      {/* Warning banner */}
      {showWarning && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl">
          <AlertTriangle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-amber-900">Votre licence expire bientôt</p>
            <p className="text-sm text-amber-800 mt-0.5">
              Votre licence Finance Pro expire dans <strong>{daysLeft} jour{daysLeft! > 1 ? 's' : ''}</strong>. Renouvelez-la pour continuer à accéder aux fonctionnalités avancées.
            </p>
          </div>
        </div>
      )}

      {/* Success banner */}
      {activationSuccess && (
        <div className="flex items-start gap-3 p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
          <CheckCircle size={18} className="text-emerald-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-emerald-900">Licence activée avec succès</p>
            <p className="text-sm text-emerald-800 mt-0.5">Votre licence Finance Pro est maintenant active.</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Status card */}
        <Card>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">Statut de la licence</h2>
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${badge.cls}`}>
              <BadgeIcon size={13} />
              {badge.label}
            </span>
          </div>

          {isActive && expiresAt ? (
            <div className="space-y-3">
              <div>
                <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-1">Date d'expiration</p>
                <p className="text-sm text-slate-900 dark:text-white">
                  {new Date(expiresAt).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' })}
                </p>
              </div>
              {daysLeft !== null && daysLeft > 0 && (
                <div>
                  <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-1">Jours restants</p>
                  <p className="text-sm text-slate-900 dark:text-white">{daysLeft} jour{daysLeft > 1 ? 's' : ''}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-start gap-3 p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
              <XCircle size={18} className="text-slate-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Aucune licence active</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Activez une licence pour accéder aux fonctionnalités Finance Pro
                </p>
              </div>
            </div>
          )}

          {/* Features list */}
          <div className="mt-5 pt-5 border-t border-slate-100 dark:border-slate-700">
            <h3 className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase mb-3">Fonctionnalités incluses</h3>
            <ul className="space-y-2">
              {[
                'Dashboard financier avec KPIs avancés',
                'Gestion avancée des factures et lignes manuelles',
                'Rapports P&L et rentabilité par projet',
                'Prévisions de trésorerie et aging report',
              ].map((feat) => (
                <li key={feat} className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-400">
                  <CheckCircle size={13} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                  {feat}
                </li>
              ))}
            </ul>
          </div>
        </Card>

        {/* Activation form */}
        <Card>
          <div className="flex items-center gap-2 mb-5">
            <Key size={18} className="text-indigo-600" />
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">Activer une licence</h2>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">
                Clé de licence
              </label>
              <input
                {...register('license_key')}
                type="text"
                placeholder={t('license.keyPlaceholder', 'Entrez votre clé de licence')}
                disabled={activateMutation.isPending}
                className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm font-mono dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
              />
              {errors.license_key && (
                <p className="text-red-500 text-xs mt-1">{errors.license_key.message}</p>
              )}
            </div>

            {activateMutation.isError && (
              <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                <XCircle size={14} className="text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-semibold text-red-900">Erreur d'activation</p>
                  <p className="text-xs text-red-700 mt-0.5">
                    La clé de licence est invalide ou a expiré.
                  </p>
                </div>
              </div>
            )}

            <Button type="submit" loading={activateMutation.isPending} icon={<Key size={14} />} className="w-full justify-center">
              Activer la licence
            </Button>
          </form>
        </Card>
      </div>
    </div>
  )
}

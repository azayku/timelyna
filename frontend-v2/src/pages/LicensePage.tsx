import { useState } from 'react'
import { Shield, CheckCircle, AlertTriangle, Key, Zap, Loader2, XCircle } from 'lucide-react'
import Card, { CardHeader } from '../components/ui/Card'
import Button from '../components/ui/Button'
import { useTranslation } from 'react-i18next'
import { useLicenseStatus, useActivateLicense } from '../features/license/hooks'

export default function LicensePage() {
  const { t } = useTranslation()
  const [licenseKey, setLicenseKey] = useState('')
  const { data: status, isLoading } = useLicenseStatus()
  const activateMutation = useActivateLicense()

  const isActive = status?.validation_status === 'valid'
  const isExpired = status?.validation_status === 'expired'
  const hasLicense = status?.status !== 'no_license' && !!status?.validation_status
  const daysLeft = status?.days_until_expiry ?? null
  const expiresAt = status?.expires_at ?? null

  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!licenseKey.trim()) return
    try {
      await activateMutation.mutateAsync(licenseKey.trim())
      setLicenseKey('')
    } catch {
      // error shown via activateMutation.isError
    }
  }

  const features = [
    t('license.feature1', 'Gestion des heures illimitée'),
    t('license.feature2', 'Approbations multi-niveaux'),
    t('license.feature3', 'Rapports avancés'),
    t('license.feature4', 'Support prioritaire'),
  ]

  if (isLoading) return (
    <div className="flex items-center justify-center py-24 text-slate-400 text-sm gap-2">
      <Loader2 size={16} className="animate-spin" /> Chargement…
    </div>
  )

  return (
    <div className="max-w-2xl space-y-5">
      {/* Expiry warning */}
      {isActive && daysLeft !== null && daysLeft <= 30 && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800">
          <AlertTriangle size={18} className="flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold">{t('license.warningTitle', 'Licence bientôt expirée')}</p>
            <p className="text-sm mt-0.5">{t('license.warningHint', { days: daysLeft, defaultValue: `Il reste ${daysLeft} jour(s) avant expiration.` })}</p>
          </div>
        </div>
      )}

      {/* Expired banner */}
      {isExpired && (
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-800">
          <XCircle size={18} className="flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold">Licence expirée</p>
            <p className="text-sm mt-0.5">Renouvelez votre licence pour continuer à utiliser toutes les fonctionnalités.</p>
          </div>
        </div>
      )}

      {/* Status card */}
      <Card>
        <CardHeader title={t('license.title', 'Licence')} subtitle={t('license.subtitle', 'Gérez votre licence Timelyna')} />
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-2">{t('license.status', 'Statut')}</p>
            {isActive ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700">
                <CheckCircle size={12} /> {t('license.active', 'Actif')}
              </span>
            ) : isExpired ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700">
                <XCircle size={12} /> Expiré
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600">
                {t('license.inactive', 'Inactif')}
              </span>
            )}
          </div>

          <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-2">{t('license.expiresAt', "Date d'expiration")}</p>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              {expiresAt
                ? new Date(expiresAt).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
                : '—'}
            </p>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-2">{t('license.daysLeft', 'Jours restants')}</p>
            {daysLeft !== null ? (
              <p className={`text-2xl font-bold ${daysLeft <= 30 ? 'text-amber-600' : 'text-emerald-600'}`}>
                {daysLeft}
                <span className="text-sm font-normal text-slate-400 ml-1">{t('common.days', 'j')}</span>
              </p>
            ) : (
              <p className="text-2xl font-bold text-slate-400">—</p>
            )}
          </div>
        </div>

        {/* Pack info */}
        {status?.pack && (
          <div className="mt-3 px-3 py-2 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
            <p className="text-xs text-indigo-600 dark:text-indigo-400 font-medium">
              Pack : <span className="font-bold uppercase">{status.pack}</span>
            </p>
          </div>
        )}
      </Card>

      {/* Activation form */}
      <Card>
        <CardHeader title={t('license.activate', 'Activer une licence')} />
        <form onSubmit={handleActivate} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">
              {t('license.licenseKey', 'Clé de licence')}
            </label>
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <Key size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={licenseKey}
                  onChange={e => setLicenseKey(e.target.value)}
                  placeholder={t('license.keyPlaceholder', 'Collez votre clé JWT ici')}
                  className="w-full pl-9 pr-3 py-2.5 border border-slate-300 dark:border-slate-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono dark:bg-slate-700 dark:text-white"
                />
              </div>
              <Button
                type="submit"
                disabled={!licenseKey.trim() || activateMutation.isPending}
                icon={<Shield size={14} />}
                loading={activateMutation.isPending}
              >
                {t('license.activateBtn', 'Activer')}
              </Button>
            </div>
            {activateMutation.isError && (
              <p className="text-xs text-red-500 mt-1.5">Clé invalide ou expirée.</p>
            )}
            {activateMutation.isSuccess && (
              <p className="text-xs text-emerald-600 mt-1.5">Licence activée avec succès.</p>
            )}
          </div>
        </form>
      </Card>

      {/* Features */}
      {(!hasLicense || isExpired) && (
        <Card>
          <CardHeader title={t('license.features', 'Fonctionnalités incluses')} />
          <ul className="mt-4 space-y-3">
            {features.map((feature, i) => (
              <li key={i} className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Zap size={11} className="text-indigo-600" />
                </div>
                <span className="text-sm text-slate-700 dark:text-slate-300">{feature}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}

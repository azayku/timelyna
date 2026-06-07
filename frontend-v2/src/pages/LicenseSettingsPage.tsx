import { useState } from 'react'
import {
  Lock, Unlock, Key, AlertTriangle, CheckCircle, XCircle,
  Loader2, FlaskConical, Clock,
} from 'lucide-react'
import { useFinanceLicense, useActivateFinanceLicense } from '../features/finance/useFinanceLicense'
import { useAllModulesStatus, useStartModuleTrial } from '../features/modules/hooks'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

// ── Module catalogue — add new modules here as the product grows ──────────

interface ModuleDef {
  id: string
  name: string
  description: string
  features: string[]
  color: string
}

const MODULES: ModuleDef[] = [
  {
    id: 'finance_pro',
    name: 'Finance Pro',
    description: 'Gestion avancée des factures, rapports financiers et prévisions de trésorerie',
    features: ['Dashboard financier avec KPIs', 'Gestion complète des factures', 'Rapports P&L et trésorerie'],
    color: 'amber',
  },
  {
    id: 'advanced_analytics',
    name: 'Analytics Avancé',
    description: 'Rapports détaillés, analyses prédictives et tableaux de bord personnalisés',
    features: ['Rapports personnalisés', 'Analyses prédictives', 'Export avancé'],
    color: 'blue',
  },
  {
    id: 'api_access',
    name: 'Accès API',
    description: 'Intégrations API complètes pour synchroniser avec vos outils métier',
    features: ['API REST complète', 'Webhooks', 'SDK client'],
    color: 'purple',
  },
  {
    id: 'multi_org',
    name: 'Multi-Organisations',
    description: 'Gérez plusieurs organisations depuis une seule instance',
    features: ['Organisations illimitées', 'Consolidation des rapports', 'SSO centralisé'],
    color: 'cyan',
  },
]

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; badge: string; badgeText: string }> = {
  amber:  { bg: 'bg-amber-50 dark:bg-amber-900/10',  border: 'border-amber-200 dark:border-amber-700',  text: 'text-amber-600',  badge: 'bg-amber-100 dark:bg-amber-900',  badgeText: 'text-amber-700 dark:text-amber-200' },
  blue:   { bg: 'bg-blue-50 dark:bg-blue-900/10',    border: 'border-blue-200 dark:border-blue-700',    text: 'text-blue-600',   badge: 'bg-blue-100 dark:bg-blue-900',    badgeText: 'text-blue-700 dark:text-blue-200' },
  purple: { bg: 'bg-purple-50 dark:bg-purple-900/10',border: 'border-purple-200 dark:border-purple-700',text: 'text-purple-600', badge: 'bg-purple-100 dark:bg-purple-900', badgeText: 'text-purple-700 dark:text-purple-200' },
  cyan:   { bg: 'bg-cyan-50 dark:bg-cyan-900/10',    border: 'border-cyan-200 dark:border-cyan-700',    text: 'text-cyan-600',   badge: 'bg-cyan-100 dark:bg-cyan-900',    badgeText: 'text-cyan-700 dark:text-cyan-200' },
}

function fmtTs(ts: number) {
  return new Date(ts * 1000).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

// ── Module card ───────────────────────────────────────────────────────────

interface ModuleCardProps {
  mod: ModuleDef
  status: { active: boolean; expires_at: string | null; expires_ts: number | null; days_remaining: number | null } | undefined
  onTrial: () => void
  trialPending: boolean
  trialError: string | null
  // finance-specific activation
  isFinance?: boolean
  licenseKey?: string
  onLicenseKeyChange?: (v: string) => void
  onActivate?: () => void
  activatePending?: boolean
  activateError?: string | null
  activateSuccess?: string | null
}

function ModuleCard({
  mod, status, onTrial, trialPending, trialError,
  isFinance, licenseKey, onLicenseKeyChange, onActivate,
  activatePending, activateError, activateSuccess,
}: ModuleCardProps) {
  const c = COLOR_MAP[mod.color]
  const isActive = status?.active ?? false
  const expiresTs = status?.expires_ts
  const daysLeft = status?.days_remaining

  return (
    <Card className={`border-2 transition-all ${isActive ? `${c.border} ${c.bg}` : 'border-slate-200 dark:border-slate-700'}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3">
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${c.bg} ${c.border} border`}>
            {isActive ? <Unlock size={16} className={c.text} /> : <Lock size={16} className="text-slate-400" />}
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white text-base">{mod.name}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{mod.description}</p>
          </div>
        </div>

        {isActive ? (
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold flex-shrink-0 ${c.badge} ${c.badgeText}`}>
            <CheckCircle size={11} /> Actif
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 text-xs font-semibold flex-shrink-0">
            <Lock size={11} /> Inactif
          </span>
        )}
      </div>

      {/* Active info */}
      {isActive && expiresTs && (
        <div className="flex items-center gap-2 mb-4 p-2.5 bg-white/60 dark:bg-slate-800/60 rounded-lg border border-slate-200 dark:border-slate-700">
          <Clock size={13} className="text-slate-400 flex-shrink-0" />
          <div className="text-xs text-slate-600 dark:text-slate-300">
            Expire le <strong>{fmtTs(expiresTs)}</strong>
            {daysLeft !== null && (
              <span className={`ml-1.5 font-semibold ${(daysLeft ?? 999) <= 7 ? 'text-red-600' : (daysLeft ?? 999) <= 30 ? 'text-amber-600' : 'text-emerald-600'}`}>
                ({daysLeft}j restants)
              </span>
            )}
          </div>
        </div>
      )}

      {/* Features */}
      <ul className="space-y-1 mb-4">
        {mod.features.map(f => (
          <li key={f} className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
            <CheckCircle size={11} className={`${c.text} flex-shrink-0`} />
            {f}
          </li>
        ))}
      </ul>

      {/* Actions — only when not active */}
      {!isActive && (
        <div className="space-y-3 pt-3 border-t border-slate-200 dark:border-slate-700">
          {/* Trial button */}
          <button
            onClick={onTrial}
            disabled={trialPending}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg border-2 border-dashed border-indigo-300 dark:border-indigo-700 text-indigo-600 dark:text-indigo-400 text-sm font-medium hover:bg-indigo-50 dark:hover:bg-indigo-900/20 disabled:opacity-50 transition-colors"
          >
            {trialPending ? <Loader2 size={14} className="animate-spin" /> : <FlaskConical size={14} />}
            Essayer gratuitement 15 jours
          </button>

          {trialError && (
            <div className="flex items-start gap-2 p-2.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
              <XCircle size={13} className="text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-red-700 dark:text-red-300">{trialError}</p>
            </div>
          )}

          {/* License key input — finance only for now, extensible */}
          {isFinance && (
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400">
                Clé de licence
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="XXXX-XXXXX-XXXXX-XXXXX"
                  value={licenseKey ?? ''}
                  onChange={e => onLicenseKeyChange?.(e.target.value)}
                  disabled={activatePending}
                  className="flex-1 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm font-mono dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                />
                <Button onClick={onActivate} loading={activatePending} icon={<Key size={13} />}>
                  Activer
                </Button>
              </div>
              {activateError && (
                <div className="flex items-start gap-2 p-2.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
                  <XCircle size={13} className="text-red-500 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-red-700 dark:text-red-300">{activateError}</p>
                </div>
              )}
              {activateSuccess && (
                <div className="flex items-start gap-2 p-2.5 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700 rounded-lg">
                  <CheckCircle size={13} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-emerald-700 dark:text-emerald-300">{activateSuccess}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function LicenseSettingsPage() {
  const { isLoading: licLoading } = useFinanceLicense()
  const activateFinance = useActivateFinanceLicense()
  const { data: modulesData, isLoading: modLoading } = useAllModulesStatus()
  const trialMutation = useStartModuleTrial()

  const [licenseKey, setLicenseKey] = useState('')
  const [activateSuccess, setActivateSuccess] = useState<string | null>(null)
  const [activateError, setActivateError] = useState<string | null>(null)
  const [trialErrors, setTrialErrors] = useState<Record<string, string>>({})

  const isLoading = licLoading || modLoading

  const handleActivateFinance = async () => {
    if (!licenseKey.trim()) return
    setActivateError(null)
    setActivateSuccess(null)
    try {
      await activateFinance.mutateAsync(licenseKey.trim())
      setActivateSuccess('Licence Finance Pro activée avec succès !')
      setLicenseKey('')
      setTimeout(() => setActivateSuccess(null), 5000)
    } catch {
      setActivateError('Clé invalide ou expirée.')
    }
  }

  const handleTrial = async (moduleId: string) => {
    setTrialErrors(e => ({ ...e, [moduleId]: '' }))
    try {
      await trialMutation.mutateAsync(moduleId)
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? err?.message ?? 'Erreur lors de l\'activation de l\'essai.'
      setTrialErrors(e => ({ ...e, [moduleId]: msg }))
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
        <Loader2 size={16} className="animate-spin" /> Chargement des licences…
      </div>
    )
  }

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Gestion des Licences</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Activez ou essayez les modules premium. Chaque essai dure 15 jours.
        </p>
      </div>

      {/* Warning if any module expires soon */}
      {Object.entries(modulesData?.modules ?? {}).some(([, s]) => s.active && (s.days_remaining ?? 999) <= 14) && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl dark:bg-amber-900/20 dark:border-amber-700">
          <AlertTriangle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-amber-800 dark:text-amber-200">
            Un ou plusieurs modules expirent dans moins de 14 jours. Renouvelez vos licences pour éviter toute interruption.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {MODULES.map(mod => {
          const status = modulesData?.modules[mod.id]
          return (
            <ModuleCard
              key={mod.id}
              mod={mod}
              status={status}
              onTrial={() => handleTrial(mod.id)}
              trialPending={trialMutation.isPending && trialMutation.variables === mod.id}
              trialError={trialErrors[mod.id] || null}
              isFinance={mod.id === 'finance_pro'}
              licenseKey={mod.id === 'finance_pro' ? licenseKey : undefined}
              onLicenseKeyChange={mod.id === 'finance_pro' ? setLicenseKey : undefined}
              onActivate={mod.id === 'finance_pro' ? handleActivateFinance : undefined}
              activatePending={mod.id === 'finance_pro' ? activateFinance.isPending : undefined}
              activateError={mod.id === 'finance_pro' ? activateError : undefined}
              activateSuccess={mod.id === 'finance_pro' ? activateSuccess : undefined}
            />
          )
        })}
      </div>

      {/* Support */}
      <Card className="bg-slate-50 dark:bg-slate-800/50">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white">Besoin d'une licence complète ?</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Contactez notre équipe pour obtenir une clé ou discuter d'un abonnement.
            </p>
          </div>
          <div className="flex gap-2 flex-shrink-0">
            <Button variant="secondary" size="sm">Demo</Button>
            <Button variant="secondary" size="sm">Contact</Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

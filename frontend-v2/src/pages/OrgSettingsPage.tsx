import { useCallback, useEffect, useState } from 'react'
import { Save, Loader2, AlertTriangle } from 'lucide-react'
import Card, { CardHeader } from '../components/ui/Card'
import Button from '../components/ui/Button'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'

interface OrgSettings {
  org_name: string
  standard_hours_per_day: number
  max_hours_per_day: number
  overtime_rate_multiplier: number
  travel_rate_multiplier: number
  default_currency: string
  account_creation_lead_days: number
}

export default function OrgSettingsPage() {
  const { t } = useTranslation()

  const { data, isLoading, isError } = useQuery<OrgSettings>({
    queryKey: ['org-settings'],
    queryFn: () => apiClient.get<OrgSettings>('/admin/settings'),
  })

  const [form, setForm] = useState<OrgSettings>({
    org_name: '',
    standard_hours_per_day: 8,
    max_hours_per_day: 24,
    overtime_rate_multiplier: 1.25,
    travel_rate_multiplier: 0.5,
    default_currency: 'EUR',
    account_creation_lead_days: 2,
  })
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (data) setForm(data)
  }, [data])

  const saveMutation = useMutation({
    mutationFn: (payload: OrgSettings) => apiClient.put('/admin/settings', payload),
    onSuccess: () => {
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    },
  })

  const set = useCallback((k: keyof OrgSettings, v: string | number) => {
    setForm(f => ({ ...f, [k]: v }))
  }, [])

  const handleOrgNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    set('org_name', e.target.value)
  }, [set])

  const handleCurrencyChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    set('default_currency', e.target.value)
  }, [set])

  const handleStandardHoursChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    set('standard_hours_per_day', parseFloat(e.target.value))
  }, [set])

  const handleMaxHoursChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    set('max_hours_per_day', parseFloat(e.target.value))
  }, [set])

  const handleOvertimeRateChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    set('overtime_rate_multiplier', parseFloat(e.target.value))
  }, [set])

  const handleTravelRateChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    set('travel_rate_multiplier', parseFloat(e.target.value))
  }, [set])

  const handleLeadDaysChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    set('account_creation_lead_days', parseInt(e.target.value))
  }, [set])

  if (isLoading) return (
    <div className="flex items-center justify-center py-24 text-slate-400 text-sm gap-2">
      <Loader2 size={16} className="animate-spin" /> Chargement…
    </div>
  )

  if (isError) return (
    <div className="flex items-center justify-center gap-2 py-24 text-red-500 text-sm">
      <AlertTriangle size={16} /> Impossible de charger les paramètres.
    </div>
  )

  return (
    <div className="max-w-2xl space-y-5">
      <Card>
        <CardHeader title={t('orgSettings.orgName', 'Organisation')} subtitle={t('orgSettings.subtitle', 'Informations générales')} />
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">{t('orgSettings.orgName', 'Nom')}</label>
            <input value={form.org_name} onChange={handleOrgNameChange}
              className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">{t('orgSettings.currency', 'Devise')}</label>
            <select value={form.default_currency} onChange={handleCurrencyChange}
              className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
              {['EUR', 'USD', 'GBP', 'CHF', 'MAD'].map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title={t('orgSettings.workHours', 'Heures de travail')} subtitle={t('orgSettings.workHoursSubtitle', 'Paramètres horaires')} />
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">{t('orgSettings.standardHours', 'Heures standard / jour')}</label>
            <div className="flex items-center gap-2">
              <input type="number" min={1} max={24} step={0.5} value={form.standard_hours_per_day}
                onChange={handleStandardHoursChange}
                className="w-24 border border-slate-300 rounded-lg px-3 py-2 text-sm text-center focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              <span className="text-sm text-slate-400">{t('common.hours_unit', 'h')}</span>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">{t('orgSettings.maxHours', 'Max heures / jour')}</label>
            <div className="flex items-center gap-2">
              <input type="number" min={1} max={24} step={0.5} value={form.max_hours_per_day}
                onChange={handleMaxHoursChange}
                className="w-24 border border-slate-300 rounded-lg px-3 py-2 text-sm text-center focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              <span className="text-sm text-slate-400">{t('common.hours_unit', 'h')}</span>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title={t('orgSettings.rates', 'Multiplicateurs')} subtitle={t('orgSettings.ratesSubtitle', 'Taux appliqués aux heures spéciales')} />
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">{t('orgSettings.overtimeRate', 'Heures supplémentaires')}</label>
            <div className="flex items-center gap-2">
              <input type="number" min={1} max={5} step={0.05} value={form.overtime_rate_multiplier}
                onChange={handleOvertimeRateChange}
                className="w-24 border border-slate-300 rounded-lg px-3 py-2 text-sm text-center focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              <span className="text-sm text-slate-400">{t('orgSettings.xNormal', '× normal')}</span>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">{t('orgSettings.travelRate', 'Déplacements')}</label>
            <div className="flex items-center gap-2">
              <input type="number" min={0} max={5} step={0.05} value={form.travel_rate_multiplier}
                onChange={handleTravelRateChange}
                className="w-24 border border-slate-300 rounded-lg px-3 py-2 text-sm text-center focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              <span className="text-sm text-slate-400">{t('orgSettings.xNormal', '× normal')}</span>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title={t('orgSettings.onboarding', 'Onboarding')} subtitle={t('orgSettings.onboardingSubtitle', 'Création différée des comptes')} />
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1.5">{t('orgSettings.leadDays', 'Délai de création de compte (jours)')}</label>
          <div className="flex items-center gap-2">
            <input type="number" min={0} max={30} value={form.account_creation_lead_days}
              onChange={handleLeadDaysChange}
              className="w-24 border border-slate-300 rounded-lg px-3 py-2 text-sm text-center focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            <span className="text-sm text-slate-400">{t('common.days', 'jours')}</span>
          </div>
          <p className="text-xs text-slate-400 mt-1.5">{t('orgSettings.leadDaysHint', 'Le compte est créé X jours avant la date d\'entrée.')}</p>
        </div>
      </Card>

      {saveMutation.isError && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertTriangle size={15} /> Erreur lors de la sauvegarde.
        </div>
      )}

      <Button size="lg" icon={<Save size={16} />} className="w-full justify-center"
        loading={saveMutation.isPending}
        onClick={() => saveMutation.mutate(form)}>
        {saved ? '✓ Enregistré' : t('orgSettings.saveSettings', 'Enregistrer les paramètres')}
      </Button>
    </div>
  )
}

import { useState } from 'react'
import { User, Lock, Bell, Calendar, Save, Eye, EyeOff, Languages } from 'lucide-react'
import { swalDark } from '../lib/swalConfig'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient, ApiError } from '../lib/apiClient'
import { useAuthStore } from '../lib/authStore'
import Card, { CardHeader } from '../components/ui/Card'
import Button from '../components/ui/Button'
import FormInput from '../components/ui/FormInput'
import MFASection from '../features/mfa/MFASection'

type TabType = 'profile' | 'security' | 'notifications'

interface NotificationPreferences {
  email_enabled: boolean
  timesheet_reminders: boolean
  approval_notifications: boolean
  rejection_notifications: boolean
  weekly_summary: boolean
}

const LANGUAGES = [
  { code: 'fr', label: 'Français', flag: 'FR' },
  { code: 'en', label: 'English', flag: 'EN' },
  { code: 'it', label: 'Italiano', flag: 'IT' },
] as const

export default function MyProfilePage() {
  const { t, i18n } = useTranslation()
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const [activeTab, setActiveTab] = useState<TabType>('profile')

  // Password change state
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  })

  // Notification preferences
  const { data: notifPrefs, isLoading: loadingPrefs } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: () => apiClient.get<NotificationPreferences>('/employee/notification-preferences'),
  })

  const [localPrefs, setLocalPrefs] = useState<NotificationPreferences | null>(null)

  // Use local state if available, otherwise use fetched data
  const currentPrefs = localPrefs || notifPrefs || {
    email_enabled: true,
    timesheet_reminders: true,
    approval_notifications: true,
    rejection_notifications: true,
    weekly_summary: false,
  }

  // Password change mutation
  const changePasswordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      apiClient.post('/auth/change-password', data),
    onSuccess: () => {
      void swalDark({ icon: 'success', title: 'Mot de passe modifié', text: 'Votre mot de passe a été mis à jour avec succès.', timer: 2500, showConfirmButton: false })
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
    },
    onError: (error: ApiError) => {
      void swalDark({ icon: 'error', title: 'Erreur', text: error.message || 'Erreur lors du changement de mot de passe' })
    },
  })

  // Notification preferences mutation
  const updatePrefsMutation = useMutation({
    mutationFn: (data: NotificationPreferences) =>
      apiClient.put('/employee/notification-preferences', data),
    onSuccess: () => {
      void swalDark({ icon: 'success', title: 'Préférences enregistrées', timer: 1800, showConfirmButton: false })
      qc.invalidateQueries({ queryKey: ['notification-preferences'] })
    },
    onError: (error: ApiError) => {
      void swalDark({ icon: 'error', title: 'Erreur', text: error.message || 'Erreur lors de la sauvegarde' })
    },
  })

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      void swalDark({ icon: 'error', title: 'Erreur', text: 'Les mots de passe ne correspondent pas.' })
      return
    }
    if (passwordForm.new_password.length < 8) {
      void swalDark({ icon: 'error', title: 'Erreur', text: 'Le mot de passe doit contenir au moins 8 caractères.' })
      return
    }
    changePasswordMutation.mutate({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
  }

  const handlePrefsChange = (key: keyof NotificationPreferences, value: boolean) => {
    const updated = { ...currentPrefs, [key]: value }
    setLocalPrefs(updated)
  }

  const handlePrefsSave = () => {
    if (localPrefs) {
      updatePrefsMutation.mutate(localPrefs)
    }
  }

  const tabs = [
    { id: 'profile' as TabType, label: 'Profil', icon: <User size={16} /> },
    { id: 'security' as TabType, label: 'Sécurité', icon: <Lock size={16} /> },
    { id: 'notifications' as TabType, label: 'Notifications', icon: <Bell size={16} /> },
  ]

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white">
          {t('profile.title', 'Mon profil')}
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          Gérez vos informations personnelles et préférences
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200 dark:border-slate-700 overflow-x-auto">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-3 sm:px-4 py-3 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            {tab.icon}
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="space-y-6">
          <Card>
            <CardHeader title="Informations personnelles" />
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormInput
                  label="Email"
                  type="email"
                  value={user?.email || ''}
                  disabled
                  className="bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-400 cursor-not-allowed"
                />
                <FormInput
                  label="Rôle"
                  type="text"
                  value={user?.role || ''}
                  disabled
                  className="bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-400 cursor-not-allowed capitalize"
                />
              </div>

              <FormInput
                label="Organisation"
                type="text"
                value={(user as any)?.organization_name || 'N/A'}
                disabled
                className="bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-400 cursor-not-allowed"
              />

              <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  <Calendar size={12} className="inline mr-1" />
                  Membre depuis: {(user as any)?.created_at ? new Date((user as any).created_at).toLocaleDateString('fr-FR') : 'N/A'}
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <CardHeader title={t('profile.preferences', 'Préférences')} />
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">
                  <Languages size={14} className="inline mr-1" />
                  {t('profile.language', 'Langue')}
                </label>
                <div className="flex flex-wrap gap-2" role="radiogroup" aria-label={t('profile.language', 'Langue')}>
                  {LANGUAGES.map((lang) => {
                    const active = i18n.language === lang.code || i18n.language?.startsWith(lang.code)
                    return (
                      <button
                        key={lang.code}
                        type="button"
                        role="radio"
                        aria-checked={active}
                        onClick={() => {
                          void i18n.changeLanguage(lang.code)
                          void swalDark({ icon: 'success', title: t('profile.languageSaved', 'Langue mise à jour'), timer: 1500, showConfirmButton: false })
                        }}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                          active
                            ? 'bg-indigo-600 border-indigo-600 text-white shadow-sm'
                            : 'bg-white dark:bg-slate-700 border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-200 hover:border-indigo-300 dark:hover:border-indigo-500'
                        }`}
                      >
                        <span className={`text-xs font-bold ${active ? 'text-white' : 'text-indigo-600 dark:text-indigo-400'}`}>
                          {lang.flag}
                        </span>
                        <span>{lang.label}</span>
                      </button>
                    )
                  })}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                  {t('profile.languageHint', 'Le changement est appliqué immédiatement.')}
                </p>
              </div>
            </div>
          </Card>

          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              {t('profile.adminHintIcon', '💡 Pour modifier vos informations personnelles, contactez votre administrateur.')}
            </p>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          <Card>
            <CardHeader title="Changer le mot de passe" />
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">
                Mot de passe actuel *
              </label>
              <div className="relative">
                <input
                  type={showPasswords.current ? 'text' : 'password'}
                  value={passwordForm.current_password}
                  onChange={e => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                  required
                  className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                />
                <button
                  type="button"
                  onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPasswords.current ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">
                Nouveau mot de passe *
              </label>
              <div className="relative">
                <input
                  type={showPasswords.new ? 'text' : 'password'}
                  value={passwordForm.new_password}
                  onChange={e => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                  required
                  minLength={8}
                  className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                />
                <button
                  type="button"
                  onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPasswords.new ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Minimum 8 caractères
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">
                Confirmer le mot de passe *
              </label>
              <div className="relative">
                <input
                  type={showPasswords.confirm ? 'text' : 'password'}
                  value={passwordForm.confirm_password}
                  onChange={e => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                  required
                  className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                />
                <button
                  type="button"
                  onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPasswords.confirm ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" icon={<Save size={16} />} loading={changePasswordMutation.isPending}>
                Enregistrer
              </Button>
            </div>
          </form>
          </Card>

          <MFASection />
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <Card>
          <CardHeader title="Préférences de notification" />
          {loadingPrefs ? (
            <div className="text-center py-8 text-slate-400 text-sm">Chargement...</div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                    Notifications par email
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Recevoir des notifications par email
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={currentPrefs.email_enabled}
                    onChange={e => handlePrefsChange('email_enabled', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-indigo-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                </label>
              </div>

              <div className="space-y-3 pl-4 border-l-2 border-slate-200 dark:border-slate-700">
                {[
                  { key: 'timesheet_reminders' as const, label: 'Rappels de saisie', desc: 'Rappel hebdomadaire pour soumettre vos heures' },
                  { key: 'approval_notifications' as const, label: 'Approbations', desc: 'Notification quand vos heures sont approuvées' },
                  { key: 'rejection_notifications' as const, label: 'Rejets', desc: 'Notification quand vos heures sont rejetées' },
                  { key: 'weekly_summary' as const, label: 'Résumé hebdomadaire', desc: 'Récapitulatif de vos heures chaque semaine' },
                ].map(item => (
                  <div key={item.key} className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50">
                    <div>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        {item.label}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        {item.desc}
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={currentPrefs[item.key]}
                        onChange={e => handlePrefsChange(item.key, e.target.checked)}
                        disabled={!currentPrefs.email_enabled}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-indigo-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600 peer-disabled:opacity-50 peer-disabled:cursor-not-allowed"></div>
                    </label>
                  </div>
                ))}
              </div>

              {localPrefs && (
                <div className="flex justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
                  <Button icon={<Save size={16} />} onClick={handlePrefsSave} loading={updatePrefsMutation.isPending}>
                    Enregistrer les préférences
                  </Button>
                </div>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}

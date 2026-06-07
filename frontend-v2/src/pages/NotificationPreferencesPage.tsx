import { useState, useEffect } from 'react'
import { CheckCircle, Loader2, Bell } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNotificationPreferences, useUpdateNotificationPreferences } from '../features/notifications/hooks'
import type { NotificationPreference } from '../features/notifications/types'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import { requestNotificationPermission } from '../lib/pushNotifications'

export default function NotificationPreferencesPage() {
  const { t } = useTranslation()
  const { data: serverPrefs = [], isLoading } = useNotificationPreferences()
  const updateMutation = useUpdateNotificationPreferences()

  const [prefs, setPrefs] = useState<NotificationPreference[]>([])
  const [saved, setSaved] = useState(false)
  const [permission, setPermission] = useState(typeof Notification !== 'undefined' ? Notification.permission : 'default')

  // Sync local state when server data loads
  useEffect(() => {
    if (serverPrefs.length > 0) setPrefs(serverPrefs)
  }, [serverPrefs])

  const toggle = (type: string, field: 'email_enabled' | 'in_app_enabled') => {
    setPrefs(prev => prev.map(p => p.type === type ? { ...p, [field]: !p[field] } : p))
  }

  const handleSave = async () => {
    await updateMutation.mutateAsync(prefs)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleEnablePush = async () => {
    await requestNotificationPermission()
    setPermission(typeof Notification !== 'undefined' ? Notification.permission : 'default')
  }

  return (
    <div className="max-w-2xl space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-white">
          {t('notifications.preferences', 'Préférences de notifications')}
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          {t('notifications.preferencesSubtitle', 'Choisissez comment vous souhaitez être notifié')}
        </p>
      </div>

      <Card>
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Bell className="h-4 w-4 text-indigo-500" />
              <p className="font-medium text-slate-800 dark:text-white text-sm">Notifications navigateur</p>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Recevez des alertes même quand l'application est en arrière-plan
            </p>
          </div>
          <button
            onClick={handleEnablePush}
            disabled={permission === 'denied'}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              permission === 'granted'
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 cursor-default'
                : permission === 'denied'
                ? 'bg-slate-100 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 text-white'
            }`}
          >
            {permission === 'granted' ? '✓ Activées' : permission === 'denied' ? 'Bloquées' : 'Activer'}
          </button>
        </div>
      </Card>

      <Card padding={false}>
        {isLoading ? (
          <div className="flex items-center justify-center py-12 text-slate-400 text-sm gap-2">
            <Loader2 size={16} className="animate-spin" /> Chargement…
          </div>
        ) : prefs.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-sm">
            Aucune préférence disponible.
          </div>
        ) : (
          <table className="min-w-full">
            <thead className="bg-slate-50 dark:bg-slate-700 border-b border-slate-200 dark:border-slate-600">
              <tr>
                <th className="px-5 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Type de notification
                </th>
                <th className="px-5 py-3 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-5 py-3 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  In-App
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {prefs.map((pref) => (
                <tr key={pref.type} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                  <td className="px-5 py-4 text-sm text-slate-700 dark:text-slate-300 capitalize">
                    {pref.type.replace(/_/g, ' ')}
                  </td>
                  <td className="px-5 py-4 text-center">
                    <input
                      type="checkbox"
                      checked={pref.email_enabled}
                      onChange={() => toggle(pref.type, 'email_enabled')}
                      className="w-4 h-4 rounded text-indigo-600 border-slate-300 focus:ring-indigo-500 cursor-pointer"
                    />
                  </td>
                  <td className="px-5 py-4 text-center">
                    <input
                      type="checkbox"
                      checked={pref.in_app_enabled}
                      onChange={() => toggle(pref.type, 'in_app_enabled')}
                      className="w-4 h-4 rounded text-indigo-600 border-slate-300 focus:ring-indigo-500 cursor-pointer"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {!isLoading && prefs.length > 0 && (
        <div className="flex items-center gap-3">
          <Button onClick={handleSave} loading={updateMutation.isPending}>
            {t('common.save', 'Enregistrer')}
          </Button>
          {saved && (
            <span className="flex items-center gap-1.5 text-emerald-600 text-sm font-medium">
              <CheckCircle size={15} /> Enregistré
            </span>
          )}
        </div>
      )}
    </div>
  )
}

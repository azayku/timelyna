import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, CheckCircle, Eye, EyeOff, ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { apiClient, ApiError } from '../lib/apiClient'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

export default function ChangePasswordPage() {
  const navigate = useNavigate()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showCurrent, setShowCurrent] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const { t } = useTranslation()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (newPassword !== confirmPassword) {
      setError(t('changePassword.errorMismatch', 'Les nouveaux mots de passe ne correspondent pas'))
      return
    }

    if (newPassword.length < 8) {
      setError(t('changePassword.errorTooShort', 'Le nouveau mot de passe doit contenir au moins 8 caractères'))
      return
    }

    if (newPassword === currentPassword) {
      setError(t('changePassword.errorSame', 'Le nouveau mot de passe doit être différent de l\'ancien'))
      return
    }

    setLoading(true)
    try {
      await apiClient.post('/auth/password/change', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      setSuccess(true)
      setTimeout(() => navigate('/'), 2000)
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setError(t('changePassword.errorWrongPassword', 'Mot de passe actuel incorrect'))
        } else {
          setError(err.message)
        }
      } else {
        setError(t('changePassword.errorGeneric', 'Une erreur est survenue'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors"
        >
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">
            {t('changePassword.heading', 'Changer le mot de passe')}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {t('changePassword.subtitle', 'Modifiez votre mot de passe pour sécuriser votre compte')}
          </p>
        </div>
      </div>

      <Card>
        {success ? (
          <div className="text-center py-8">
            <div className="flex items-center justify-center mb-4">
              <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                <CheckCircle size={24} className="text-emerald-600" />
              </div>
            </div>
            <h2 className="text-lg font-semibold text-slate-800 mb-2">
              {t('changePassword.successTitle', 'Mot de passe modifié')}
            </h2>
            <p className="text-sm text-slate-500">
              {t('changePassword.successMessage', 'Votre mot de passe a été mis à jour avec succès')}
            </p>
          </div>
        ) : (
          <form className="space-y-5" onSubmit={handleSubmit}>
            {/* Error banner */}
            {error && (
              <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-3 py-2.5 text-sm">
                <AlertCircle size={15} className="shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Current password */}
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1.5">
                {t('changePassword.currentPassword', 'Mot de passe actuel')} *
              </label>
              <div className="relative">
                <input
                  type={showCurrent ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={e => setCurrentPassword(e.target.value)}
                  placeholder={t('changePassword.currentPlaceholder', 'Entrez votre mot de passe actuel')}
                  required
                  autoComplete="current-password"
                  className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm pr-10 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent(!showCurrent)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showCurrent ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <div className="border-t border-slate-100 pt-5">
              {/* New password */}
              <div className="mb-4">
                <label className="block text-xs font-semibold text-slate-500 mb-1.5">
                  {t('changePassword.newPassword', 'Nouveau mot de passe')} *
                </label>
                <div className="relative">
                  <input
                    type={showNew ? 'text' : 'password'}
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    placeholder={t('changePassword.newPlaceholder', 'Minimum 8 caractères')}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm pr-10 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNew(!showNew)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showNew ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              {/* Confirm password */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1.5">
                  {t('changePassword.confirmPassword', 'Confirmer le nouveau mot de passe')} *
                </label>
                <div className="relative">
                  <input
                    type={showConfirm ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    placeholder={t('changePassword.confirmPlaceholder', 'Retapez le nouveau mot de passe')}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm pr-10 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showConfirm ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>
            </div>

            {/* Password requirements */}
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
              <p className="text-xs font-semibold text-slate-600 mb-2">
                {t('changePassword.requirements', 'Exigences du mot de passe')}:
              </p>
              <ul className="text-xs text-slate-500 space-y-1">
                <li className={newPassword.length >= 8 ? 'text-emerald-600' : ''}>
                  • {t('changePassword.req1', 'Au moins 8 caractères')}
                </li>
                <li className={newPassword !== currentPassword && newPassword.length > 0 ? 'text-emerald-600' : ''}>
                  • {t('changePassword.req2', 'Différent du mot de passe actuel')}
                </li>
                <li className={newPassword === confirmPassword && newPassword.length > 0 ? 'text-emerald-600' : ''}>
                  • {t('changePassword.req3', 'Les deux mots de passe correspondent')}
                </li>
              </ul>
            </div>

            {/* Actions */}
            <div className="flex gap-3 justify-end pt-2">
              <Button variant="secondary" type="button" onClick={() => navigate(-1)}>
                {t('common.cancel', 'Annuler')}
              </Button>
              <Button type="submit" loading={loading}>
                {t('changePassword.submit', 'Changer le mot de passe')}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  )
}

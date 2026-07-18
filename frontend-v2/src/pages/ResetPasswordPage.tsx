import { useState, useEffect } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { Clock, AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { apiClient, ApiError } from '../lib/apiClient'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const { t } = useTranslation()

  useEffect(() => {
    if (!token) {
      setError(t('resetPassword.errorNoToken', 'Lien invalide ou expiré'))
    }
  }, [token, t])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError(t('resetPassword.errorMismatch', 'Les mots de passe ne correspondent pas'))
      return
    }

    if (password.length < 8) {
      setError(t('resetPassword.errorTooShort', 'Le mot de passe doit contenir au moins 8 caractères'))
      return
    }

    if (!token) {
      setError(t('resetPassword.errorNoToken', 'Lien invalide ou expiré'))
      return
    }

    setLoading(true)
    try {
      await apiClient.post('/auth/password/reset', { token, new_password: password })
      setSuccess(true)
      setTimeout(() => navigate('/login'), 3000)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(t('resetPassword.errorGeneric', 'Une erreur est survenue'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-indigo-500 flex items-center justify-center">
            <Clock size={20} className="text-white" />
          </div>
          <span className="text-white text-xl font-bold">Timelyna</span>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {success ? (
            <>
              <div className="flex items-center justify-center mb-4">
                <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                  <CheckCircle size={24} className="text-emerald-600" />
                </div>
              </div>
              <h1 className="text-xl font-bold text-slate-800 mb-2 text-center">
                {t('resetPassword.successTitle', 'Mot de passe réinitialisé')}
              </h1>
              <p className="text-sm text-slate-500 mb-6 text-center">
                {t('resetPassword.successMessage', 'Vous allez être redirigé vers la page de connexion...')}
              </p>
            </>
          ) : (
            <>
              <h1 className="text-xl font-bold text-slate-800 mb-1">
                {t('resetPassword.heading', 'Nouveau mot de passe')}
              </h1>
              <p className="text-sm text-slate-400 mb-6">
                {t('resetPassword.subtitle', 'Choisissez un nouveau mot de passe sécurisé')}
              </p>

              {/* Error banner */}
              {error && (
                <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-3 py-2.5 mb-4 text-sm">
                  <AlertCircle size={15} className="shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1.5">
                    {t('resetPassword.newPassword', 'Nouveau mot de passe')}
                  </label>
                  <div className="relative">
                    <input
                      type={showPwd ? 'text' : 'password'}
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      placeholder={t('resetPassword.passwordPlaceholder', 'Minimum 8 caractères')}
                      required
                      minLength={8}
                      autoComplete="new-password"
                      className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm pr-10 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPwd(!showPwd)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                      {showPwd ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1.5">
                    {t('resetPassword.confirmPassword', 'Confirmer le mot de passe')}
                  </label>
                  <div className="relative">
                    <input
                      type={showConfirm ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={e => setConfirmPassword(e.target.value)}
                      placeholder={t('resetPassword.confirmPlaceholder', 'Retapez le mot de passe')}
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
                <button
                  type="submit"
                  disabled={loading || !token}
                  className="w-full bg-indigo-600 text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {loading ? t('resetPassword.submitting', 'Réinitialisation...') : t('resetPassword.submit', 'Réinitialiser')}
                </button>
              </form>

              <div className="mt-5 pt-4 border-t border-slate-100 text-center">
                <Link to="/login" className="text-sm text-indigo-600 hover:underline">
                  {t('resetPassword.backToLogin', 'Retour à la connexion')}
                </Link>
              </div>
            </>
          )}
        </div>

        <p className="text-center text-slate-500 text-xs mt-6">© 2026 Timelyna</p>
      </div>
    </div>
  )
}

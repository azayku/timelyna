import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Clock, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { apiClient, ApiError } from '../lib/apiClient'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const { t } = useTranslation()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await apiClient.post('/auth/password/reset-request', { email })
      setSuccess(true)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(t('forgotPassword.errorGeneric', 'Une erreur est survenue'))
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
          <img 
            src="https://img.icons8.com/?size=100&id=20935&format=png&color=ffffff" 
            alt="Timelyna Logo"
            className="w-10 h-10 rounded-xl"
          />
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
                {t('forgotPassword.successTitle', 'Email envoyé')}
              </h1>
              <p className="text-sm text-slate-500 mb-6 text-center">
                {t('forgotPassword.successMessage', 'Si un compte existe avec cet email, vous recevrez un lien de réinitialisation.')}
              </p>
              <Link
                to="/login"
                className="flex items-center justify-center gap-2 w-full bg-indigo-600 text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors shadow-sm"
              >
                <ArrowLeft size={15} />
                {t('forgotPassword.backToLogin', 'Retour à la connexion')}
              </Link>
            </>
          ) : (
            <>
              <h1 className="text-xl font-bold text-slate-800 mb-1">
                {t('forgotPassword.heading', 'Mot de passe oublié')}
              </h1>
              <p className="text-sm text-slate-400 mb-6">
                {t('forgotPassword.subtitle', 'Entrez votre email pour recevoir un lien de réinitialisation')}
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
                    {t('forgotPassword.email', 'Email')}
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder={t('forgotPassword.emailPlaceholder', 'votre.email@exemple.com')}
                    required
                    autoComplete="email"
                    className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-indigo-600 text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {loading ? t('forgotPassword.submitting', 'Envoi...') : t('forgotPassword.submit', 'Envoyer le lien')}
                </button>
              </form>

              <div className="mt-5 pt-4 border-t border-slate-100 text-center">
                <Link to="/login" className="text-sm text-indigo-600 hover:underline inline-flex items-center gap-1">
                  <ArrowLeft size={13} />
                  {t('forgotPassword.backToLogin', 'Retour à la connexion')}
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

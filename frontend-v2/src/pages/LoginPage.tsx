import { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { Eye, EyeOff, AlertCircle, CheckSquare } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../lib/authStore'
import type { AuthUser } from '../lib/authStore'
import { ApiError } from '../lib/apiClient'
import WelcomeSplash from '../components/WelcomeSplash'

const LANGS = ['fr', 'en', 'it', 'es'] as const

export default function LoginPage() {
  const [showPwd, setShowPwd] = useState(false)
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [splashUser, setSplashUser] = useState<AuthUser | null>(null)

  const { t, i18n } = useTranslation()
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as { from?: Location } | null)?.from?.pathname ?? '/'

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(identifier, password)
      const loggedUser = useAuthStore.getState().user
      if (loggedUser) {
        setSplashUser(loggedUser)
      } else {
        navigate(from, { replace: true })
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError(t('login.errorInvalidCredentials'))
      } else {
        setError(t('login.errorGeneric'))
      }
    } finally {
      setLoading(false)
    }
  }

  if (splashUser) {
    return <WelcomeSplash user={splashUser} onComplete={() => navigate(from, { replace: true })} />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex">
      {/* Left side - Illustration */}
      <div className="hidden lg:flex lg:w-1/2 items-center justify-center p-12 bg-white">
        <div className="max-w-md text-center">
          <div className="mb-8 flex justify-center">
            <div className="w-20 h-20 rounded-2xl bg-indigo-100 flex items-center justify-center">
              <CheckSquare size={40} className="text-indigo-600" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-slate-800 mb-4">
            {t('login.welcomeTitle', 'Timelyna')}
          </h1>
          <p className="text-lg text-slate-600 mb-8">
            {t('login.welcomeSubtitle', "Gérez vos temps et projets efficacement")}
          </p>
          
          {/* Illustration placeholder */}
          <div className="relative">
            <img 
              src="https://media.licdn.com/dms/image/v2/D4E12AQGmmjgu_HHCYQ/article-cover_image-shrink_720_1280/article-cover_image-shrink_720_1280/0/1658479901339?e=1785974400&v=beta&t=7Qc1ox6EFUm_Bd-J60eopMKZlGl8V2pYTTnTO_7Vr5U"
              alt="Timelyna - Gestion des temps"
              className="w-full rounded-lg shadow-md"
            />
          </div>
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Card */}
          <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-3xl shadow-2xl p-8 text-white">
            <div className="mb-8">
              <h2 className="text-2xl font-bold mb-2">{t('login.signIn', 'Connexion')}</h2>
              <p className="text-indigo-100 text-sm">
                {t('login.accessDashboard', 'Accédez à votre espace de travail')}
              </p>
            </div>

            {/* Error banner */}
            {error && (
              <div className="flex items-center gap-2 bg-red-500/20 border border-red-400/30 text-white rounded-lg px-3 py-2.5 mb-4 text-sm">
                <AlertCircle size={15} className="shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="identifier-input" className="block text-sm font-medium text-indigo-100 mb-2">
                  {t('login.emailOrUsername', 'Email ou nom d\'utilisateur')}
                </label>
                <input
                  id="identifier-input"
                  type="text"
                  value={identifier}
                  onChange={e => setIdentifier(e.target.value)}
                  placeholder={t('login.emailPlaceholder', 'name@example.com ou username')}
                  required
                  autoComplete="username"
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-sm text-white placeholder-indigo-200 focus:outline-none focus:ring-2 focus:ring-white/30 focus:border-transparent backdrop-blur-sm"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label htmlFor="password-input" className="block text-sm font-medium text-indigo-100">
                    {t('login.password', 'Password')}
                  </label>
                  <Link to="/forgot-password" className="text-sm text-indigo-200 hover:text-white transition-colors">
                    {t('login.forgotPassword', 'Forgot password?')}
                  </Link>
                </div>
                <div className="relative">
                  <input
                    id="password-input"
                    type={showPwd ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    required
                    autoComplete="current-password"
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-sm text-white placeholder-indigo-200 focus:outline-none focus:ring-2 focus:ring-white/30 focus:border-transparent backdrop-blur-sm pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd(!showPwd)}
                    aria-label={showPwd ? t('login.hidePassword', 'Masquer le mot de passe') : t('login.showPassword', 'Afficher le mot de passe')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-indigo-200 hover:text-white transition-colors"
                  >
                    {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="flex items-center">
                <label className="flex items-center gap-2 text-sm text-indigo-100 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={e => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-white/20 bg-white/10 text-white focus:ring-2 focus:ring-white/30"
                  />
                  {t('login.rememberMe', 'Remember me')}
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-white text-indigo-600 py-3 rounded-lg text-sm font-semibold hover:bg-indigo-50 transition-colors shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loading ? t('login.submitting', 'Connexion...') : t('login.signIn', 'SIGN IN')}
              </button>
            </form>

            {/* Sign up link - Disabled */}
            <p className="text-center text-sm text-indigo-100 mt-6 opacity-50">
              {t('login.noAccount', "Don't have an account yet?")}{' '}
              <span className="text-white/50 font-medium cursor-not-allowed">
                {t('login.contactAdmin', 'Contactez votre administrateur')}
              </span>
            </p>
          </div>

          {/* Language selector */}
          <div className="mt-6 flex items-center justify-center gap-2">
            {LANGS.map(lang => (
              <button
                key={lang}
                onClick={() => i18n.changeLanguage(lang)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase transition-colors ${
                  i18n.language === lang
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                {lang}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

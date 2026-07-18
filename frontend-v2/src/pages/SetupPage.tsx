import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, User, CheckCircle, Upload, X, Eye, EyeOff, ChevronRight, ChevronLeft } from 'lucide-react'
import { runSetup, fetchSetupStatus } from '../features/setup/api'
import { ApiError } from '../lib/apiClient'

// ─── Types ───────────────────────────────────────────────────────────────────

interface FormData {
  company_name: string
  app_name: string
  company_logo: string | null
  admin_first_name: string
  admin_last_name: string
  admin_email: string
  admin_password: string
  admin_password_confirm: string
}

const INITIAL: FormData = {
  company_name: '',
  app_name: 'Timelyna',
  company_logo: null,
  admin_first_name: '',
  admin_last_name: '',
  admin_email: '',
  admin_password: '',
  admin_password_confirm: '',
}

const STEPS = [
  { id: 1, label: 'Entreprise', icon: Building2 },
  { id: 2, label: 'Administrateur', icon: User },
  { id: 3, label: 'Confirmation', icon: CheckCircle },
]

// ─── Component ───────────────────────────────────────────────────────────────

export default function SetupPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState<FormData>(INITIAL)
  const [errors, setErrors] = useState<Partial<Record<keyof FormData | 'global', string>>>({})
  const [loading, setLoading] = useState(false)
  const [showPwd, setShowPwd] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [done, setDone] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Redirect to login if already installed
  useEffect(() => {
    fetchSetupStatus()
      .then(s => { if (s.is_installed) navigate('/login', { replace: true }) })
      .catch(() => {/* ignore, let user proceed */})
  }, [navigate])

  // ── Helpers ──────────────────────────────────────────────────────────────

  function set(field: keyof FormData, value: string | null) {
    setForm(prev => ({ ...prev, [field]: value }))
    setErrors(prev => ({ ...prev, [field]: undefined }))
  }

  function validateStep1(): boolean {
    const e: typeof errors = {}
    if (!form.company_name.trim()) e.company_name = 'Le nom de l\'entreprise est requis'
    if (!form.app_name.trim()) e.app_name = 'Le nom de l\'application est requis'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  function validateStep2(): boolean {
    const e: typeof errors = {}
    if (!form.admin_first_name.trim()) e.admin_first_name = 'Prénom requis'
    if (!form.admin_last_name.trim()) e.admin_last_name = 'Nom requis'
    if (!form.admin_email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.admin_email))
      e.admin_email = 'Email invalide'
    if (form.admin_password.length < 8) e.admin_password = 'Minimum 8 caractères'
    if (form.admin_password !== form.admin_password_confirm)
      e.admin_password_confirm = 'Les mots de passe ne correspondent pas'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  function handleNext() {
    if (step === 1 && !validateStep1()) return
    if (step === 2 && !validateStep2()) return
    setStep(s => s + 1)
  }

  function handleLogoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 2 * 1024 * 1024) {
      setErrors(prev => ({ ...prev, company_logo: 'Logo trop grand (max 2 Mo)' }))
      return
    }
    const reader = new FileReader()
    reader.onload = ev => set('company_logo', ev.target?.result as string)
    reader.readAsDataURL(file)
  }

  async function handleSubmit() {
    setLoading(true)
    setErrors({})
    try {
      await runSetup({
        company_name: form.company_name,
        app_name: form.app_name,
        company_logo: form.company_logo || null,
        admin_first_name: form.admin_first_name,
        admin_last_name: form.admin_last_name,
        admin_email: form.admin_email,
        admin_password: form.admin_password,
      })
      setDone(true)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        // Already installed — redirect to login
        navigate('/login', { replace: true })
        return
      }
      const msg = err instanceof ApiError ? err.message : 'Une erreur est survenue'
      setErrors({ global: msg })
    } finally {
      setLoading(false)
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────

  if (done) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-10 max-w-md w-full text-center">
          <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-emerald-600" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800 mb-2">Installation terminée !</h1>
          <p className="text-slate-500 mb-2">
            <strong>{form.company_name}</strong> est prête sur <strong>{form.app_name}</strong>.
          </p>
          <p className="text-slate-400 text-sm mb-8">
            Connectez-vous avec l'adresse email <strong>{form.admin_email}</strong>.
          </p>
          <button
            onClick={() => navigate('/login')}
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-colors"
          >
            Aller à la connexion
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Logo / Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3">
            <img 
              src="https://img.icons8.com/?size=100&id=20935&format=png&color=ffffff" 
              alt="Timelyna Logo"
              className="w-10 h-10 rounded-xl"
            />
            <span className="text-white text-2xl font-bold tracking-tight">Timelyna</span>
          </div>
          <p className="text-indigo-300 mt-2 text-sm">Assistant de première installation</p>
        </div>

        {/* Step bar */}
        <div className="flex items-center justify-center gap-0 mb-8">
          {STEPS.map((s, i) => {
            const Icon = s.icon
            const active = step === s.id
            const done = step > s.id
            return (
              <div key={s.id} className="flex items-center">
                <div className={`flex flex-col items-center gap-1 ${active ? 'opacity-100' : done ? 'opacity-80' : 'opacity-40'}`}>
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center border-2 transition-all
                    ${active ? 'bg-indigo-500 border-indigo-500 text-white' :
                      done ? 'bg-emerald-500 border-emerald-500 text-white' :
                      'bg-slate-800 border-slate-600 text-slate-400'}`}>
                    {done ? <CheckCircle size={16} /> : <Icon size={16} />}
                  </div>
                  <span className="text-xs text-slate-300 font-medium">{s.label}</span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className={`w-16 h-0.5 mb-5 mx-2 ${step > s.id ? 'bg-emerald-500' : 'bg-slate-700'}`} />
                )}
              </div>
            )
          })}
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {/* ── Step 1 : Entreprise ── */}
          {step === 1 && (
            <div className="space-y-5">
              <div>
                <h2 className="text-xl font-bold text-slate-800">Votre entreprise</h2>
                <p className="text-sm text-slate-500 mt-1">Configurez le nom et l'identité visuelle.</p>
              </div>

              {/* App name */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Nom de l'application
                </label>
                <input
                  type="text"
                  value={form.app_name}
                  onChange={e => set('app_name', e.target.value)}
                  placeholder="Timelyna"
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />
                <p className="text-xs text-slate-400 mt-1">Affiché dans le navigateur et les emails.</p>
                {errors.app_name && <p className="text-xs text-red-500 mt-1">{errors.app_name}</p>}
              </div>

              {/* Company name */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Nom de l'entreprise <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.company_name}
                  onChange={e => set('company_name', e.target.value)}
                  placeholder="Ex : Acme Corp"
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />
                {errors.company_name && <p className="text-xs text-red-500 mt-1">{errors.company_name}</p>}
              </div>

              {/* Logo */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Logo de l'entreprise <span className="text-slate-400">(optionnel)</span>
                </label>
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml"
                  ref={fileInputRef}
                  onChange={handleLogoChange}
                  className="hidden"
                />
                {form.company_logo ? (
                  <div className="flex items-center gap-3 p-3 border border-slate-200 rounded-lg">
                    <img
                      src={form.company_logo}
                      alt="Logo aperçu"
                      className="h-12 w-12 object-contain rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700 font-medium">Logo chargé</p>
                      <p className="text-xs text-slate-400">Cliquez pour changer</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        set('company_logo', null)
                        if (fileInputRef.current) fileInputRef.current.value = ''
                      }}
                      className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full flex items-center gap-3 px-4 py-3 border-2 border-dashed border-slate-200 rounded-lg text-slate-500 hover:border-indigo-400 hover:text-indigo-500 transition-colors"
                  >
                    <Upload size={18} />
                    <span className="text-sm">Choisir un logo (PNG, JPEG, SVG — max 2 Mo)</span>
                  </button>
                )}
                {errors.company_logo && <p className="text-xs text-red-500 mt-1">{errors.company_logo}</p>}
              </div>

              {/* Preview */}
              <div className="bg-slate-50 rounded-lg px-4 py-3 flex items-center gap-3">
                {form.company_logo ? (
                  <img src={form.company_logo} alt="logo" className="h-8 w-8 object-contain" />
                ) : (
                  <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center">
                    <Building2 size={16} className="text-indigo-500" />
                  </div>
                )}
                <span className="text-sm font-semibold text-slate-700">
                  {form.company_name || 'Nom de l\'entreprise'} <span className="text-slate-400 font-normal">by {form.app_name || 'Timelyna'}</span>
                </span>
              </div>
            </div>
          )}

          {/* ── Step 2 : Administrateur ── */}
          {step === 2 && (
            <div className="space-y-5">
              <div>
                <h2 className="text-xl font-bold text-slate-800">Compte administrateur</h2>
                <p className="text-sm text-slate-500 mt-1">Ce compte aura tous les droits sur l'application.</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Prénom <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={form.admin_first_name}
                    onChange={e => set('admin_first_name', e.target.value)}
                    className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                  />
                  {errors.admin_first_name && <p className="text-xs text-red-500 mt-1">{errors.admin_first_name}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Nom <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={form.admin_last_name}
                    onChange={e => set('admin_last_name', e.target.value)}
                    className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                  />
                  {errors.admin_last_name && <p className="text-xs text-red-500 mt-1">{errors.admin_last_name}</p>}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Email <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={form.admin_email}
                  onChange={e => set('admin_email', e.target.value)}
                  placeholder="admin@votreentreprise.com"
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />
                {errors.admin_email && <p className="text-xs text-red-500 mt-1">{errors.admin_email}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Mot de passe <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showPwd ? 'text' : 'password'}
                    value={form.admin_password}
                    onChange={e => set('admin_password', e.target.value)}
                    placeholder="Minimum 8 caractères"
                    className="w-full px-3 py-2.5 pr-10 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd(v => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
                  >
                    {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
                {errors.admin_password && <p className="text-xs text-red-500 mt-1">{errors.admin_password}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Confirmer le mot de passe <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showConfirm ? 'text' : 'password'}
                    value={form.admin_password_confirm}
                    onChange={e => set('admin_password_confirm', e.target.value)}
                    className="w-full px-3 py-2.5 pr-10 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(v => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
                  >
                    {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
                {errors.admin_password_confirm && (
                  <p className="text-xs text-red-500 mt-1">{errors.admin_password_confirm}</p>
                )}
              </div>
            </div>
          )}

          {/* ── Step 3 : Récap ── */}
          {step === 3 && (
            <div className="space-y-5">
              <div>
                <h2 className="text-xl font-bold text-slate-800">Récapitulatif</h2>
                <p className="text-sm text-slate-500 mt-1">Vérifiez les informations avant de finaliser.</p>
              </div>

              <div className="bg-slate-50 rounded-xl divide-y divide-slate-100">
                <div className="flex items-center gap-4 px-4 py-3">
                  {form.company_logo ? (
                    <img src={form.company_logo} alt="logo" className="h-10 w-10 object-contain rounded" />
                  ) : (
                    <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0">
                      <Building2 size={18} className="text-indigo-500" />
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-semibold text-slate-700">{form.company_name}</p>
                    <p className="text-xs text-slate-400">by {form.app_name}</p>
                  </div>
                </div>
                <div className="px-4 py-3 grid grid-cols-2 gap-2 text-sm">
                  <span className="text-slate-500">Administrateur</span>
                  <span className="text-slate-700 font-medium">{form.admin_first_name} {form.admin_last_name}</span>
                  <span className="text-slate-500">Email</span>
                  <span className="text-slate-700 font-medium break-all">{form.admin_email}</span>
                </div>
              </div>

              {errors.global && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
                  {errors.global}
                </div>
              )}

              <p className="text-xs text-slate-400">
                En cliquant sur "Terminer l'installation", la base de données sera configurée et l'application sera opérationnelle.
              </p>
            </div>
          )}

          {/* Navigation */}
          <div className="mt-8 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setStep(s => s - 1)}
              disabled={step === 1}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-0 disabled:pointer-events-none transition-colors"
            >
              <ChevronLeft size={16} />
              Retour
            </button>

            {step < 3 ? (
              <button
                type="button"
                onClick={handleNext}
                className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold transition-colors"
              >
                Suivant
                <ChevronRight size={16} />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-70 text-white rounded-xl text-sm font-semibold transition-colors"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Installation…
                  </>
                ) : (
                  <>
                    <CheckCircle size={16} />
                    Terminer l'installation
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Mail, RotateCcw, Save, Send, AlertCircle, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { apiClient } from '../lib/apiClient'
import Modal from '../components/ui/Modal'
import Button from '../components/ui/Button'

// ─── Types ────────────────────────────────────────────────────────────────────

interface EmailTemplate {
  key: string
  subject: string
  html_body: string
  text_body: string | null
  is_custom: boolean
  updated_at: string | null
}

const TEMPLATE_VARIABLES: Record<string, string[]> = {
  welcome_new_employee: ['first_name', 'last_name', 'username', 'setup_link', 'org_name'],
  password_reset: ['first_name', 'last_name', 'reset_link', 'org_name'],
  onboarding_reminder: ['first_name', 'last_name', 'hire_date', 'manager_first_name', 'org_name'],
  budget_alert: ['project_name', 'consumption_pct', 'budget_hours', 'consumed_hours', 'remaining_hours', 'manager_first_name', 'org_name'],
}

const TEMPLATE_LABELS: Record<string, string> = {
  welcome_new_employee: 'Bienvenue nouvel employé',
  password_reset: 'Réinitialisation mot de passe',
  onboarding_reminder: 'Rappel onboarding J-1',
  budget_alert: 'Alerte dépassement budget',
}

const schema = z.object({
  subject: z.string().min(1, 'Le sujet est requis'),
  html_body: z.string().min(1, 'Le corps HTML est requis'),
})
type FormData = z.infer<typeof schema>

// ─── Test Email Modal ─────────────────────────────────────────────────────────

function TestEmailModal({ templateKey, onClose }: { templateKey: string; onClose: () => void }) {
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [sending, setSending] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSend = async () => {
    if (!email) return
    setSending(true)
    setError(null)
    try {
      await apiClient.post(`/admin/email-templates/${templateKey}/preview`, { to_email: email })
      setSuccess(true)
      setTimeout(() => onClose(), 2000)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? "Erreur lors de l'envoi")
    } finally {
      setSending(false)
    }
  }

  return (
    <Modal open onClose={onClose} title="Envoyer un email de test" size="sm">
      {success ? (
        <div className="flex items-center gap-3 p-4 bg-emerald-50 rounded-lg text-emerald-800">
          <Mail size={20} />
          <p className="text-sm font-medium">Email envoyé avec succès !</p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            L'email sera envoyé avec des données d'exemple pour prévisualisation.
          </p>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Adresse email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder={t('common.emailPlaceholder', 'votre@email.com')} autoFocus
              className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          </div>
          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 rounded-lg text-red-800 text-sm">
              <AlertCircle size={15} className="flex-shrink-0 mt-0.5" />{error}
            </div>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={onClose}>Annuler</Button>
            <Button onClick={handleSend} loading={sending} disabled={!email}>
              <Send size={14} /> Envoyer
            </Button>
          </div>
        </div>
      )}
    </Modal>
  )
}

// ─── Reset Modal ──────────────────────────────────────────────────────────────

function ResetModal({ onConfirm, onClose }: { onConfirm: () => void; onClose: () => void }) {
  return (
    <Modal open onClose={onClose} title="Réinitialiser le template" size="sm">
      <p className="text-sm text-slate-600 dark:text-slate-400 mb-5">
        Êtes-vous sûr de vouloir réinitialiser ce template à sa version par défaut ? Toutes les modifications seront perdues.
      </p>
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>Annuler</Button>
        <Button variant="danger" onClick={onConfirm}>
          <RotateCcw size={14} /> Réinitialiser
        </Button>
      </div>
    </Modal>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function EmailTemplatesPage() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [showTestModal, setShowTestModal] = useState(false)
  const [showResetModal, setShowResetModal] = useState(false)
  const [previewHtml, setPreviewHtml] = useState('')

  const { data: templates = [], isLoading } = useQuery<EmailTemplate[]>({
    queryKey: ['email-templates'],
    queryFn: () => apiClient.get<EmailTemplate[]>('/admin/email-templates'),
  })

  const { data: selectedTemplate } = useQuery<EmailTemplate>({
    queryKey: ['email-template', selectedKey],
    queryFn: () => apiClient.get<EmailTemplate>(`/admin/email-templates/${selectedKey}`),
    enabled: !!selectedKey,
  })

  const { register, handleSubmit, reset, watch, formState: { errors, isDirty } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  useEffect(() => {
    if (selectedTemplate) reset({ subject: selectedTemplate.subject, html_body: selectedTemplate.html_body })
  }, [selectedTemplate, reset])

  const watchedSubject = watch('subject')
  const watchedBody = watch('html_body')

  useEffect(() => {
    if (!watchedBody) return
    const sampleData: Record<string, string> = {
      first_name: 'Jean', last_name: 'Martin', username: 'martjean',
      setup_link: 'https://example.com/setup?token=sample123',
      reset_link: 'https://example.com/reset?token=sample456',
      org_name: 'Mon Organisation',
      hire_date: new Date(Date.now() + 86400000).toLocaleDateString('fr-FR'),
      manager_first_name: 'Sophie',
      project_name: 'Projet Alpha', consumption_pct: '85',
      budget_hours: '200', consumed_hours: '170', remaining_hours: '30',
    }
    let preview = watchedBody
    Object.entries(sampleData).forEach(([key, value]) => {
      preview = preview.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value)
    })
    setPreviewHtml(preview)
  }, [watchedBody])

  const saveMutation = useMutation({
    mutationFn: (data: FormData) => apiClient.put(`/admin/email-templates/${selectedKey}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['email-templates'] })
      qc.invalidateQueries({ queryKey: ['email-template', selectedKey] })
    },
  })

  const resetMutation = useMutation({
    mutationFn: () => apiClient.delete(`/admin/email-templates/${selectedKey}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['email-templates'] })
      qc.invalidateQueries({ queryKey: ['email-template', selectedKey] })
      setShowResetModal(false)
    },
  })

  useEffect(() => {
    if (templates.length > 0 && !selectedKey) setSelectedKey(templates[0].key)
  }, [templates, selectedKey])

  if (isLoading) return (
    <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
      <Loader2 size={16} className="animate-spin" /> Chargement…
    </div>
  )

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-white">
          {t('emailTemplates.title', "Templates d'emails")}
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          {t('emailTemplates.subtitle', 'Personnalisez les emails envoyés automatiquement par le système')}
        </p>
      </div>

      <div className="grid grid-cols-12 gap-5">
        {/* Template list */}
        <div className="col-span-3">
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className="px-4 py-3 bg-slate-50 dark:bg-slate-700 border-b border-slate-200 dark:border-slate-600">
              <h2 className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                Templates disponibles
              </h2>
            </div>
            <div className="divide-y divide-slate-100 dark:divide-slate-700">
              {templates.map((tpl) => (
                <button key={tpl.key} onClick={() => setSelectedKey(tpl.key)}
                  className={`w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${
                    selectedKey === tpl.key ? 'bg-indigo-50 dark:bg-indigo-900/30 border-l-4 border-indigo-600' : ''
                  }`}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                        {TEMPLATE_LABELS[tpl.key] ?? tpl.key}
                      </p>
                      <p className="text-xs mt-0.5">
                        {tpl.is_custom
                          ? <span className="text-indigo-600 dark:text-indigo-400 font-medium">Personnalisé</span>
                          : <span className="text-slate-400">Par défaut</span>
                        }
                      </p>
                    </div>
                    <Mail size={14} className="text-slate-400 flex-shrink-0 mt-0.5" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Editor */}
        <div className="col-span-9">
          {selectedTemplate ? (
            <form onSubmit={handleSubmit(d => saveMutation.mutate(d))} className="space-y-4">
              {/* Header */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                      {TEMPLATE_LABELS[selectedTemplate.key] ?? selectedTemplate.key}
                    </h2>
                    {selectedTemplate.is_custom && selectedTemplate.updated_at && (
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        Modifié le {new Date(selectedTemplate.updated_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' })}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button type="button" variant="secondary" icon={<Send size={14} />} onClick={() => setShowTestModal(true)}>
                      Envoyer un test
                    </Button>
                    {selectedTemplate.is_custom && (
                      <Button type="button" variant="secondary" icon={<RotateCcw size={14} />} onClick={() => setShowResetModal(true)}>
                        Réinitialiser
                      </Button>
                    )}
                    <Button type="submit" loading={saveMutation.isPending} disabled={!isDirty} icon={<Save size={14} />}>
                      Enregistrer
                    </Button>
                  </div>
                </div>
              </div>

              {/* Variables */}
              {TEMPLATE_VARIABLES[selectedTemplate.key] && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                  <h3 className="text-xs font-semibold text-blue-900 dark:text-blue-300 mb-2">Variables disponibles</h3>
                  <div className="flex flex-wrap gap-2">
                    {TEMPLATE_VARIABLES[selectedTemplate.key].map((v) => (
                      <code key={v} className="px-2 py-0.5 bg-white dark:bg-slate-800 border border-blue-200 dark:border-blue-700 rounded text-xs font-mono text-blue-700 dark:text-blue-400">
                        {`{{${v}}}`}
                      </code>
                    ))}
                  </div>
                </div>
              )}

              {/* Subject */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Sujet de l'email</label>
                <input {...register('subject')}
                  className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                {errors.subject && <p className="text-red-500 text-xs mt-1">{errors.subject.message}</p>}
              </div>

              {/* HTML body */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Corps HTML</label>
                <textarea {...register('html_body')} rows={12}
                  className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm font-mono resize-none dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                {errors.html_body && <p className="text-red-500 text-xs mt-1">{errors.html_body.message}</p>}
              </div>

              {/* Preview */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
                <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-3">Aperçu</h3>
                <div className="border border-slate-200 dark:border-slate-600 rounded-lg overflow-hidden">
                  <div className="bg-slate-50 dark:bg-slate-700 border-b border-slate-200 dark:border-slate-600 px-4 py-2">
                    <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Sujet: </span>
                    <span className="text-xs text-slate-700 dark:text-slate-300">{watchedSubject || '(vide)'}</span>
                  </div>
                  <iframe srcDoc={previewHtml} sandbox="allow-same-origin"
                    className="w-full h-64 bg-white" title="Email preview" />
                </div>
              </div>
            </form>
          ) : (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
              <Mail size={48} className="mx-auto text-slate-200 dark:text-slate-600 mb-4" />
              <p className="text-slate-500 dark:text-slate-400 text-sm">Sélectionnez un template pour commencer</p>
            </div>
          )}
        </div>
      </div>

      {showTestModal && selectedKey && (
        <TestEmailModal templateKey={selectedKey} onClose={() => setShowTestModal(false)} />
      )}
      {showResetModal && (
        <ResetModal onConfirm={() => resetMutation.mutate()} onClose={() => setShowResetModal(false)} />
      )}
    </div>
  )
}

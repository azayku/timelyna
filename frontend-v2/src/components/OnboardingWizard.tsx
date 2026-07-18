import { useState, useEffect } from 'react'
import { CheckCircle, Building2, Users, FolderKanban, X } from 'lucide-react'

interface OnboardingWizardProps {
  onComplete: () => void
}

const STEPS = [
  {
    id: 1,
    icon: Building2,
    title: 'Bienvenue dans Timelyna !',
    description: 'Configurez votre organisation en quelques étapes simples.',
    action: 'Paramètres organisation',
    href: '/admin/settings',
  },
  {
    id: 2,
    icon: Users,
    title: 'Invitez vos employés',
    description: 'Ajoutez manuellement ou importez via CSV vos collaborateurs.',
    action: 'Gérer les utilisateurs',
    href: '/admin/users',
  },
  {
    id: 3,
    icon: FolderKanban,
    title: 'Créez vos projets',
    description: 'Organisez le travail en projets et assignez vos équipes.',
    action: 'Gérer les projets',
    href: '/admin/projects',
  },
  {
    id: 4,
    icon: CheckCircle,
    title: 'Tout est prêt !',
    description: 'Vos collaborateurs peuvent maintenant saisir leurs heures. Vous recevrez les demandes d\'approbation dans votre tableau de bord.',
    action: null,
    href: null,
  },
]

const STORAGE_KEY = 'onboarding_completed'

export default function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [step, setStep] = useState(0)
  
  const current = STEPS[step]
  const Icon = current.icon
  const isLast = step === STEPS.length - 1

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg p-8 relative">
        <button
          onClick={onComplete}
          aria-label="Ignorer l'onboarding"
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Progression */}
        <div className="flex gap-2 mb-8">
          {STEPS.map((_, i) => (
            <div key={i} className={`flex-1 h-1.5 rounded-full transition-colors ${i <= step ? 'bg-indigo-500' : 'bg-slate-200 dark:bg-slate-700'}`} />
          ))}
        </div>

        {/* Icône */}
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-900/30 flex items-center justify-center">
            <Icon className="h-8 w-8 text-indigo-500" />
          </div>
        </div>

        {/* Contenu */}
        <div className="text-center space-y-2 mb-8">
          <h2 className="text-xl font-bold text-slate-800 dark:text-white">{current.title}</h2>
          <p className="text-slate-500 dark:text-slate-400">{current.description}</p>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-3">
          {current.href && (
            <a
              href={current.href}
              onClick={onComplete}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 text-white rounded-xl font-medium text-center transition-colors"
            >
              {current.action}
            </a>
          )}
          
          <div className="flex gap-3">
            {step > 0 && (
              <button
                onClick={() => setStep(s => s - 1)}
                className="flex-1 py-2.5 border border-slate-300 dark:border-slate-600 rounded-xl text-slate-700 dark:text-slate-300 text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                Précédent
              </button>
            )}
            
            {isLast ? (
              <button
                onClick={onComplete}
                className="flex-1 py-2.5 bg-green-500 hover:bg-green-600 text-white rounded-xl text-sm font-medium transition-colors"
              >
                Commencer
              </button>
            ) : (
              <button
                onClick={() => setStep(s => s + 1)}
                className="flex-1 py-2.5 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-xl text-sm font-medium transition-colors"
              >
                {current.href ? 'Passer' : 'Suivant'}
              </button>
            )}
          </div>
        </div>

        {/* Étape */}
        <p className="text-center text-xs text-slate-400 mt-4">
          Étape {step + 1} sur {STEPS.length}
        </p>
      </div>
    </div>
  )
}

// Hook pour gérer l'affichage
export function useOnboarding(isAdmin: boolean) {
  const [show, setShow] = useState(false)

  useEffect(() => {
    if (!isAdmin) return
    const completed = localStorage.getItem(STORAGE_KEY)
    if (!completed) setShow(true)
  }, [isAdmin])

  const complete = () => {
    localStorage.setItem(STORAGE_KEY, 'true')
    setShow(false)
  }

  return { show, complete }
}

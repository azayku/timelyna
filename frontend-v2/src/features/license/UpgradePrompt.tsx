import { Lock } from 'lucide-react'
import { Link } from 'react-router-dom'

interface Props {
  feature?: string
}

export default function UpgradePrompt({ feature }: Props) {
  return (
    <div className="flex flex-col items-center justify-center min-h-64 bg-slate-50 dark:bg-slate-800 rounded-xl border-2 border-dashed border-slate-200 dark:border-slate-700 p-8 text-center">
      <Lock size={40} className="text-slate-300 dark:text-slate-600 mb-4" />
      <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-2">
        {feature ? `"${feature}" nécessite un plan supérieur` : 'Cette fonctionnalité nécessite un plan supérieur'}
      </h3>
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-5 max-w-sm">
        Mettez à niveau votre licence pour débloquer cette fonctionnalité.
      </p>
      <Link
        to="/admin/license"
        className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
      >
        Voir les options de licence →
      </Link>
    </div>
  )
}

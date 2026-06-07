type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'default' | 'purple'

const VARIANTS: Record<BadgeVariant, string> = {
  success: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  warning: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  danger: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  info: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  default: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  purple: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
}

export default function Badge({ label, variant = 'default' }: { label: string; variant?: BadgeVariant }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${VARIANTS[variant]}`}>
      {label}
    </span>
  )
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    approved: 'success', active: 'success', paid: 'success',
    pending: 'warning', draft: 'warning', sent: 'info',
    rejected: 'danger', inactive: 'danger', overdue: 'danger',
    cancelled: 'default', invoiced: 'purple',
  }
  const labels: Record<string, string> = {
    approved: 'Approuvé', active: 'Actif', paid: 'Payée',
    pending: 'En attente', draft: 'Brouillon', sent: 'Envoyée',
    rejected: 'Rejeté', inactive: 'Inactif', overdue: 'En retard',
    cancelled: 'Annulé', invoiced: 'Facturé',
  }
  return <Badge label={labels[status] ?? status} variant={map[status] ?? 'default'} />
}

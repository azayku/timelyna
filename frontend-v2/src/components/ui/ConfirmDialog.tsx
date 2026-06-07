import { AlertTriangle } from 'lucide-react'
import Modal from './Modal'
import Button from './Button'

interface Props {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'warning' | 'primary'
  loading?: boolean
}

export default function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirmer',
  cancelText = 'Annuler',
  variant = 'danger',
  loading = false,
}: Props) {
  const variantColors = {
    danger: 'text-red-600',
    warning: 'text-amber-600',
    primary: 'text-indigo-600',
  }

  // Map ConfirmDialog variants to Button variants
  const buttonVariant = variant === 'warning' ? 'primary' : variant

  return (
    <Modal open={open} onClose={onClose} title={title} size="sm">
      <div className="flex items-start gap-3 mb-6">
        <AlertTriangle size={20} className={`flex-shrink-0 mt-0.5 ${variantColors[variant]}`} />
        <p className="text-sm text-slate-600 dark:text-slate-400">{message}</p>
      </div>
      <div className="flex gap-3 justify-end">
        <Button variant="secondary" onClick={onClose} disabled={loading}>
          {cancelText}
        </Button>
        <Button variant={buttonVariant} onClick={onConfirm} loading={loading}>
          {confirmText}
        </Button>
      </div>
    </Modal>
  )
}

import { Loader2 } from 'lucide-react'

interface Props {
  message?: string
  size?: 'sm' | 'md' | 'lg'
}

export default function LoadingState({ message = 'Chargement…', size = 'md' }: Props) {
  const sizeClasses = {
    sm: 'py-8 text-xs',
    md: 'py-16 text-sm',
    lg: 'py-24 text-base',
  }

  const iconSizes = {
    sm: 14,
    md: 16,
    lg: 20,
  }

  return (
    <div className={`flex items-center justify-center text-slate-400 gap-2 ${sizeClasses[size]}`}>
      <Loader2 size={iconSizes[size]} className="animate-spin" />
      <span>{message}</span>
    </div>
  )
}

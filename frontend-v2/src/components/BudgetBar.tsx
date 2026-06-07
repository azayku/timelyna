import { AlertTriangle } from 'lucide-react'
import type { ProjectBudgetStatus } from '../features/budget/api'

interface BudgetBarProps {
  budget: ProjectBudgetStatus
  compact?: boolean
}

export default function BudgetBar({ budget, compact = false }: BudgetBarProps) {
  const pct = Number(budget.consumption_percentage ?? 0)
  const isAlert = budget.alert
  const barColor = pct >= 100 ? 'bg-red-500' : pct >= 80 ? 'bg-amber-500' : 'bg-green-500'
  
  if (!budget.budget_hours) return null
  
  return (
    <div className={compact ? '' : 'space-y-1'}>
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-600 dark:text-slate-400">
          {Number(budget.consumed_hours).toFixed(1)}h / {Number(budget.budget_hours).toFixed(0)}h
        </span>
        <span className={`font-medium flex items-center gap-1 ${isAlert ? 'text-amber-600 dark:text-amber-400' : 'text-slate-500 dark:text-slate-400'}`}>
          {isAlert && <AlertTriangle className="h-3 w-3" />}
          {pct.toFixed(0)}%
        </span>
      </div>
      <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${barColor}`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  )
}

import { TrendingUp, TrendingDown } from 'lucide-react'

interface KpiCardProps {
  icon: React.ReactNode
  iconBg?: string
  label: string
  value: string | number
  trend?: number
  trendLabel?: string
  subtitle?: string
}

export default function KpiCard({ icon, iconBg = 'bg-indigo-100', label, value, trend, trendLabel, subtitle }: KpiCardProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm p-4 sm:p-5 hover:shadow-md transition-shadow h-full flex flex-col">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 sm:w-11 sm:h-11 rounded-lg ${iconBg} flex items-center justify-center text-indigo-600 dark:text-indigo-400 flex-shrink-0`}>
          {icon}
        </div>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 text-xs font-semibold flex-shrink-0 ${trend >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
            {trend >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {Math.abs(trend)}%
          </div>
        )}
      </div>
      <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 line-clamp-2">{label}</p>
      <p className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-slate-100 mb-auto">{value}</p>
      {(subtitle || trendLabel) && (
        <p className="text-xs text-slate-400 dark:text-slate-500 mt-2 line-clamp-2">{subtitle || trendLabel}</p>
      )}
    </div>
  )
}

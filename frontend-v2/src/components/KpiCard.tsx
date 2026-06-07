import { TrendingUp, TrendingDown } from 'lucide-react'

interface KpiCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: number // % change vs previous period
  currency?: boolean
}

const fmt = (n: number) =>
  new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(n)

export default function KpiCard({ title, value, icon, trend, currency = false }: KpiCardProps) {
  const displayValue =
    currency && typeof value === 'number' ? fmt(value) : value

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="w-11 h-11 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
          {icon}
        </div>
        {trend !== undefined && (
          <div
            className={`flex items-center gap-1 text-xs font-semibold ${
              trend >= 0 ? 'text-emerald-600' : 'text-red-500'
            }`}
          >
            {trend >= 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
            {trend >= 0 ? '+' : ''}
            {Number(trend).toFixed(1)}%
          </div>
        )}
      </div>
      <p className="text-xs font-medium text-slate-500 mb-1 truncate">{title}</p>
      <p className="text-2xl font-bold text-slate-800 tabular-nums">{displayValue}</p>
    </div>
  )
}

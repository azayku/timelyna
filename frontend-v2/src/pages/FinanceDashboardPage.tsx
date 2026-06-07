import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { DollarSign, Clock, TrendingUp, FileText } from 'lucide-react'

import { useFinanceDashboard } from '../features/finance/hooks'
import type { Period } from '../features/finance/types'
import KpiCard from '../components/KpiCard'
import RevenueChart from '../components/RevenueChart'
import ClientRevenueDonut from '../components/ClientRevenueDonut'
import ProjectBurnChart from '../components/ProjectBurnChart'
import RecentInvoicesWidget from '../components/RecentInvoicesWidget'
import OverdueWidget from '../components/OverdueWidget'
import Card, { CardHeader } from '../components/ui/Card'

// ─── Period selector ──────────────────────────────────────────────────────────

const PERIODS: Period[] = ['this_month', 'last_month', 'quarter', 'year']

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function SkeletonBlock({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse bg-slate-100 rounded-lg ${className}`} />
}

function DashboardSkeleton() {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
            <div className="flex items-start justify-between mb-3">
              <SkeletonBlock className="w-11 h-11" />
              <SkeletonBlock className="w-12 h-4" />
            </div>
            <SkeletonBlock className="w-24 h-3 mb-2" />
            <SkeletonBlock className="w-32 h-7" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <SkeletonBlock className="w-40 h-4 mb-5" />
          <SkeletonBlock className="w-full h-52" />
        </div>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
          <SkeletonBlock className="w-32 h-4 mb-5" />
          <SkeletonBlock className="w-full h-52" />
        </div>
      </div>
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <SkeletonBlock className="w-40 h-4 mb-5" />
        <SkeletonBlock className="w-full h-56" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <SkeletonBlock className="h-64" />
        <SkeletonBlock className="h-64" />
      </div>
    </div>
  )
}

// ─── Formatters ───────────────────────────────────────────────────────────────

const fmtEur = (n: number) =>
  new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(n)

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function FinanceDashboardPage() {
  const { t } = useTranslation()
  const [period, setPeriod] = useState<Period>('this_month')

  const { data, isLoading, isError, error } = useFinanceDashboard(period)

  return (
    <div className="space-y-5">

      {/* Header + period selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h1 className="text-lg font-bold text-slate-800">{t('finance.dashboard')}</h1>
        <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
          {PERIODS.map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                period === p
                  ? 'bg-white text-slate-800 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {t(`finance.period.${p}`)}
            </button>
          ))}
        </div>
      </div>

      {/* Error state */}
      {isError && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          {(error as Error)?.message ?? t('common.error')}
        </div>
      )}

      {/* Loading skeleton */}
      {isLoading && <DashboardSkeleton />}

      {/* Content */}
      {data && (
        <>
          {/* Row 1 — 4 KPI cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              title={t('finance.revenueThisMonth')}
              value={fmtEur(data.kpis.total_revenue)}
              icon={<DollarSign size={20} />}
              trend={data.kpis.total_revenue_trend}
            />
            <KpiCard
              title={t('finance.billedHours')}
              value={`${Number(data.kpis.billed_hours).toFixed(0)}h`}
              icon={<Clock size={20} />}
              trend={data.kpis.billed_hours_trend}
            />
            <KpiCard
              title={t('finance.grossMargin')}
              value={fmtEur(data.kpis.gross_margin)}
              icon={<TrendingUp size={20} />}
              trend={data.kpis.gross_margin_trend}
            />
            <KpiCard
              title={t('finance.invoicesIssued')}
              value={data.kpis.invoice_count}
              icon={<FileText size={20} />}
              trend={data.kpis.invoice_count_trend}
            />
          </div>

          {/* Row 2 — Revenue chart + Client donut */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <Card className="lg:col-span-2">
              <CardHeader title={t('finance.rollingRevenue')} />
              {data.monthly_revenue.length === 0 ? (
                <div className="flex items-center justify-center h-52 text-sm text-slate-400">
                  {t('common.noData')}
                </div>
              ) : (
                <RevenueChart data={data.monthly_revenue} />
              )}
            </Card>

            <Card>
              <CardHeader title={t('finance.clientBreakdown')} />
              {data.client_revenue.length === 0 ? (
                <div className="flex items-center justify-center h-52 text-sm text-slate-400">
                  {t('common.noData')}
                </div>
              ) : (
                <ClientRevenueDonut data={data.client_revenue} />
              )}
            </Card>
          </div>

          {/* Row 3 — Project burn chart */}
          <Card>
            <CardHeader title={t('finance.burnRate')} />
            {data.burn_rate.length === 0 ? (
              <div className="flex items-center justify-center h-40 text-sm text-slate-400">
                {t('common.noData')}
              </div>
            ) : (
              <ProjectBurnChart data={data.burn_rate} />
            )}
          </Card>

          {/* Row 4 — Recent invoices + Overdue */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <RecentInvoicesWidget invoices={data.recent_invoices} />
            <OverdueWidget invoices={data.overdue_invoices} />
          </div>
        </>
      )}

    </div>
  )
}

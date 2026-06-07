import { useState } from 'react'
import type { ColDef } from 'ag-grid-community'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  LineChart, Line, Legend,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import DataGrid from '../components/DataGrid'
import { formatCurrency } from '../lib/formatters'
import {
  useFinancePnL,
  useProjectProfitability,
  useAgingReport,
  useCashflowForecast,
} from '../features/finance/hooks'
import type { Period } from '../features/finance/types'

// ─── Period selector ──────────────────────────────────────────────────────────

const PERIODS: { value: Period; label: string }[] = [
  { value: 'this_month', label: 'Ce mois' },
  { value: 'last_month', label: 'Mois dernier' },
  { value: 'quarter', label: 'Trimestre' },
  { value: 'year', label: 'Année' },
]

const TABS = ['P&L', 'Rentabilité projets', 'Aging créances', 'Prévision trésorerie'] as const
type Tab = typeof TABS[number]

// ─── P&L Tab ──────────────────────────────────────────────────────────────────

function PnlTab() {
  const [period, setPeriod] = useState<Period>('this_month')
  const { data, isLoading } = useFinancePnL(period)

  const chartData = data ? [
    { name: 'CA', value: data.revenue, fill: '#6366f1' },
    { name: 'Coûts', value: data.costs, fill: '#f87171' },
    { name: 'Marge brute', value: data.gross_margin, fill: '#34d399' },
  ] : []

  return (
    <div className="space-y-5">
      <div className="flex gap-1">
        {PERIODS.map((p) => (
          <button key={p.value} onClick={() => setPeriod(p.value)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              period === p.value
                ? 'bg-indigo-600 text-white'
                : 'bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
            }`}>
            {p.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="h-48 bg-slate-50 dark:bg-slate-800 rounded-xl animate-pulse" />
      ) : data ? (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Revenus', value: formatCurrency(data.revenue), color: 'text-indigo-600 dark:text-indigo-400' },
              { label: 'Coûts', value: formatCurrency(data.costs), color: 'text-red-500 dark:text-red-400' },
              { label: 'Marge brute', value: formatCurrency(data.gross_margin), color: 'text-emerald-600 dark:text-emerald-400' },
              { label: 'Marge brute %', value: `${Number(data.gross_margin_pct).toFixed(1)}%`, color: 'text-emerald-600 dark:text-emerald-400' },
            ].map((item) => (
              <div key={item.label} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 p-4">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">{item.label}</p>
                <p className={`text-xl font-bold ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 p-5">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
                <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k€`} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={60}>
                  {chartData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      ) : null}
    </div>
  )
}

// ─── Profitability Tab ────────────────────────────────────────────────────────

function ProfitabilityTab() {
  const { data = [], isLoading } = useProjectProfitability()

  const cols: ColDef[] = [
    { headerName: 'Projet', field: 'project_name', flex: 1, minWidth: 160 },
    { headerName: 'Client', field: 'client_name', flex: 1, minWidth: 140 },
    { headerName: 'Budget h', field: 'budget_hours', width: 110, valueFormatter: p => `${Number(p.value ?? 0).toFixed(1)}h`, cellStyle: { textAlign: 'right' } },
    { headerName: 'Réel h', field: 'actual_hours', width: 110, valueFormatter: p => `${Number(p.value ?? 0).toFixed(1)}h`, cellStyle: { textAlign: 'right' } },
    { headerName: 'Écart h', field: 'hours_variance', width: 110, valueFormatter: p => `${Number(p.value ?? 0).toFixed(1)}h`,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      cellStyle: (p: any) => ({ textAlign: 'right', color: p.value >= 0 ? '#16a34a' : '#dc2626', fontWeight: '600' }) },
    { headerName: 'CA', field: 'revenue', width: 130, valueFormatter: p => formatCurrency(p.value), cellStyle: { textAlign: 'right' } },
    { headerName: 'Coût', field: 'internal_cost', width: 130, valueFormatter: p => formatCurrency(p.value), cellStyle: { textAlign: 'right' } },
    { headerName: 'Marge', field: 'margin', width: 130, valueFormatter: p => formatCurrency(p.value),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      cellStyle: (p: any) => ({ textAlign: 'right', fontWeight: '600', color: p.value >= 0 ? '#16a34a' : '#dc2626' }) },
    { headerName: 'Marge %', field: 'margin_pct', width: 100, valueFormatter: p => `${Number(p.value ?? 0).toFixed(1)}%`,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      cellStyle: (p: any) => ({ textAlign: 'right', color: p.value >= 0 ? '#16a34a' : '#dc2626' }) },
  ]

  if (isLoading) return <div className="h-48 bg-slate-50 dark:bg-slate-800 rounded-xl animate-pulse" />
  return <DataGrid rowData={data} columnDefs={cols} pageSize={25} storageKey="finance-profitability" />
}

// ─── Aging Tab ────────────────────────────────────────────────────────────────

function AgingTab() {
  const { data, isLoading } = useAgingReport()

  const bucketLabels: Record<string, string> = {
    '0_30': '0–30 jours', '31_60': '31–60 jours', '61_90': '61–90 jours', 'over_90': '> 90 jours',
  }
  const bucketColors: Record<string, string> = {
    '0_30': '#fbbf24', '31_60': '#f97316', '61_90': '#ef4444', 'over_90': '#7f1d1d',
  }

  const summaryData = data
    ? Object.entries(data.totals).map(([key, value]) => ({
        name: bucketLabels[key] ?? key,
        value: value as number,
        fill: bucketColors[key] ?? '#94a3b8',
      }))
    : []

  const cols: ColDef[] = [
    { headerName: 'Facture', field: 'invoice_number', width: 150 },
    { headerName: 'Client', field: 'client_name', flex: 1, minWidth: 140 },
    { headerName: 'Montant', field: 'total_amount', width: 130, valueFormatter: p => formatCurrency(p.value), cellStyle: { textAlign: 'right', fontWeight: '600' } },
    { headerName: 'Échéance', field: 'due_date', width: 120, valueFormatter: p => p.value ? new Date(p.value).toLocaleDateString('fr-FR') : '—' },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    { headerName: 'Retard (j)', field: 'days_overdue', width: 110, cellStyle: (p: any) => ({ textAlign: 'right', color: p.value > 60 ? '#dc2626' : '#ea580c', fontWeight: '600' }) },
  ]

  const allInvoices = data
    ? [...(data.buckets['0_30'] ?? []), ...(data.buckets['31_60'] ?? []), ...(data.buckets['61_90'] ?? []), ...(data.buckets['over_90'] ?? [])]
    : []

  return (
    <div className="space-y-5">
      {isLoading ? (
        <div className="h-48 bg-slate-50 dark:bg-slate-800 rounded-xl animate-pulse" />
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {summaryData.map((item) => (
              <div key={item.name} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 p-4">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">{item.name}</p>
                <p className="text-xl font-bold" style={{ color: item.fill }}>{formatCurrency(item.value)}</p>
              </div>
            ))}
          </div>
          {summaryData.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 p-5">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={summaryData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k€`} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                  <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={60}>
                    {summaryData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <DataGrid rowData={allInvoices} columnDefs={cols} pageSize={25} storageKey="finance-aging" />
        </>
      )}
    </div>
  )
}

// ─── Cashflow Tab ─────────────────────────────────────────────────────────────

function CashflowTab() {
  const [months, setMonths] = useState(3)
  const { data = [], isLoading } = useCashflowForecast(months)

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <span className="text-sm text-slate-600 dark:text-slate-400">Horizon :</span>
        {[1, 3, 6].map((m) => (
          <button key={m} onClick={() => setMonths(m)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              months === m
                ? 'bg-indigo-600 text-white'
                : 'bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
            }`}>
            {m} mois
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="h-48 bg-slate-50 dark:bg-slate-800 rounded-xl animate-pulse" />
      ) : data.length > 0 ? (
        <>
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 p-5">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k€`} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip formatter={(v) => [formatCurrency(Number(v)), 'Encaissements prévus']} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="expected_amount" name="Encaissements prévus" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {data.map((row) => (
              <div key={row.month} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 p-4">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">{row.month}</p>
                <p className="text-lg font-bold text-indigo-600 dark:text-indigo-400">{formatCurrency(row.expected_amount)}</p>
                <p className="text-xs text-slate-400 dark:text-slate-500">{row.invoice_count} facture{row.invoice_count > 1 ? 's' : ''}</p>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 p-8 text-center text-slate-400 text-sm">
          Aucune prévision disponible pour cet horizon.
        </div>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function FinancialReportsPage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<Tab>('P&L')

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-white">
          {t('finance.reports', 'Rapports financiers')}
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          {t('finance.reportsSubtitle', 'Analyse avancée de la performance financière')}
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-700">
        <nav className="flex gap-1 -mb-px">
          {TABS.map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400'
                  : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-500'
              }`}>
              {tab}
            </button>
          ))}
        </nav>
      </div>

      <div>
        {activeTab === 'P&L' && <PnlTab />}
        {activeTab === 'Rentabilité projets' && <ProfitabilityTab />}
        {activeTab === 'Aging créances' && <AgingTab />}
        {activeTab === 'Prévision trésorerie' && <CashflowTab />}
      </div>
    </div>
  )
}

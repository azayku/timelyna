import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import type { ColDef } from 'ag-grid-community'
import DataGrid from '../../components/DataGrid'

// Mock data temporaire
const MOCK_FINANCIAL_DATA = [
  { id: 1, client: 'Client A', hours: 120, revenue: 9000, cost: 3000, margin: 6000 },
  { id: 2, client: 'Client B', hours: 80, revenue: 6400, cost: 2000, margin: 4400 },
  { id: 3, client: 'Client C', hours: 50, revenue: 3000, cost: 1500, margin: 1500 },
]

export default function FinancialReportPage() {
  const { t } = useTranslation()

  const currencyFormatter = (params: any) => {
    if (params.value === undefined || params.value === null) return '—'
    return new Intl.NumberFormat(t('locale', 'fr-FR'), { style: 'currency', currency: 'EUR' }).format(params.value)
  }

  const columnDefs = useMemo<ColDef[]>(() => [
    { headerName: t('financialReport.client', 'Client'), field: 'client', flex: 1, minWidth: 150 },
    { headerName: t('financialReport.hours', 'Heures'), field: 'hours', width: 100 },
    {
      headerName: t('financialReport.revenue', 'CA'),
      field: 'revenue',
      width: 120,
      valueFormatter: currencyFormatter
    },
    {
      headerName: t('financialReport.cost', 'Coût'),
      field: 'cost',
      width: 120,
      valueFormatter: currencyFormatter
    },
    {
      headerName: t('financialReport.margin', 'Marge'),
      field: 'margin',
      width: 120,
      valueFormatter: currencyFormatter,
      cellStyle: (params) => {
        if (params.value < 0) {
          return { color: 'red' }
        }
        return null
      }
    }
  ], [t])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800 dark:text-white">
        {t('nav.financialReport', 'Rapport Financier')}
      </h1>
      <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
        {t('financialReport.subtitle', 'Consultez les données financières de vos projets et clients')}
      </p>

      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <DataGrid
          rowData={MOCK_FINANCIAL_DATA}
          columnDefs={columnDefs}
          storageKey="financial-report-grid"
          height={600}
        />
      </div>
    </div>
  )
}

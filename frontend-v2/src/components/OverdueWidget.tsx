import { AlertTriangle } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export interface OverdueInvoice {
  invoice_id: number
  invoice_number: string
  client_name: string
  total_amount: number
  currency: string
  due_date: string
  days_overdue: number
}

interface OverdueWidgetProps {
  invoices: OverdueInvoice[]
}

const fmtAmount = (amount: number, currency = 'EUR') =>
  new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount)

export default function OverdueWidget({ invoices }: OverdueWidgetProps) {
  const { t } = useTranslation()

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
        <AlertTriangle size={15} className="text-red-500" />
        <h2 className="text-sm font-semibold text-slate-800">{t('finance.overdueInvoices')}</h2>
        {invoices.length > 0 && (
          <span className="ml-auto inline-flex items-center justify-center w-5 h-5 rounded-full bg-red-100 text-red-600 text-xs font-bold">
            {invoices.length}
          </span>
        )}
      </div>

      {invoices.length === 0 ? (
        <div className="px-5 py-8 text-center">
          <p className="text-sm text-emerald-600 font-medium">✓ Aucune facture en retard</p>
        </div>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="px-5 py-2.5 text-left text-xs font-medium text-slate-500">{t('invoices.number')}</th>
              <th className="px-3 py-2.5 text-left text-xs font-medium text-slate-500">{t('common.client')}</th>
              <th className="px-3 py-2.5 text-right text-xs font-medium text-slate-500">{t('invoices.amount')}</th>
              <th className="px-5 py-2.5 text-right text-xs font-medium text-slate-500">{t('finance.daysOverdue')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {invoices.map((inv) => (
              <tr key={inv.invoice_id} className="hover:bg-red-50 transition-colors">
                <td className="px-5 py-3 font-mono text-xs font-semibold text-slate-700">
                  {inv.invoice_number}
                </td>
                <td className="px-3 py-3 text-slate-600 truncate max-w-[120px]">{inv.client_name}</td>
                <td className="px-3 py-3 text-right font-semibold text-slate-800 tabular-nums">
                  {fmtAmount(inv.total_amount, inv.currency)}
                </td>
                <td className="px-5 py-3 text-right">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-100 text-red-700 text-xs font-semibold">
                    {inv.days_overdue}j
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

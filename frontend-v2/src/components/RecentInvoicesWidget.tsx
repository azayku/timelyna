import { useTranslation } from 'react-i18next'
import { StatusBadge } from './ui/Badge'

export interface RecentInvoice {
  invoice_id: number
  invoice_number: string
  client_name: string
  total_amount: number
  currency: string
  status: string
  due_date: string | null
}

interface RecentInvoicesWidgetProps {
  invoices: RecentInvoice[]
}

const fmtAmount = (amount: number, currency = 'EUR') =>
  new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount)

const fmtDate = (d: string | null) => {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

export default function RecentInvoicesWidget({ invoices }: RecentInvoicesWidgetProps) {
  const { t } = useTranslation()

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100">
        <h2 className="text-sm font-semibold text-slate-800">{t('finance.recentInvoices')}</h2>
      </div>
      {invoices.length === 0 ? (
        <div className="px-5 py-8 text-center text-sm text-slate-400">{t('common.noData')}</div>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="px-5 py-2.5 text-left text-xs font-medium text-slate-500">{t('invoices.number')}</th>
              <th className="px-3 py-2.5 text-left text-xs font-medium text-slate-500">{t('common.client')}</th>
              <th className="px-3 py-2.5 text-right text-xs font-medium text-slate-500">{t('invoices.amount')}</th>
              <th className="px-3 py-2.5 text-center text-xs font-medium text-slate-500">{t('common.status')}</th>
              <th className="px-5 py-2.5 text-right text-xs font-medium text-slate-500">{t('invoices.dueDate')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {invoices.map((inv) => (
              <tr key={inv.invoice_id} className="hover:bg-slate-50 transition-colors">
                <td className="px-5 py-3 font-mono text-xs font-semibold text-slate-700">
                  {inv.invoice_number}
                </td>
                <td className="px-3 py-3 text-slate-600 truncate max-w-[120px]">{inv.client_name}</td>
                <td className="px-3 py-3 text-right font-semibold text-slate-800 tabular-nums">
                  {fmtAmount(inv.total_amount, inv.currency)}
                </td>
                <td className="px-3 py-3 text-center">
                  <StatusBadge status={inv.status} />
                </td>
                <td className="px-5 py-3 text-right text-slate-500 text-xs">{fmtDate(inv.due_date)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

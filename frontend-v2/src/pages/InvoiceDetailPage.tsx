import { useParams, useNavigate } from 'react-router-dom'
import { Download, Send, CheckCircle, BadgeCheck, Clock, ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useInvoice, useFinalizeInvoice, useSendInvoice, useMarkInvoicePaid, useInvoiceAuditLogs } from '../features/invoicing/hooks'
import { StatusBadge } from '../components/ui/Badge'
import { formatCurrency, formatDate } from '../lib/formatters'
import { tokenStore } from '../lib/tokenStore'

const ACTION_LABELS: Record<string, string> = {
  finalized: 'Finalisée',
  paid: 'Marquée payée',
  sent: 'Envoyée',
  created: 'Créée',
}

export default function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const invoiceId = Number(id)

  const { data: invoice, isLoading } = useInvoice(invoiceId)
  const { data: auditLogs = [] } = useInvoiceAuditLogs(invoiceId)
  const finalize = useFinalizeInvoice()
  const send = useSendInvoice()
  const markPaid = useMarkInvoicePaid()

  const handleDownload = async () => {
    try {
      const token = tokenStore.get()
      const res = await fetch(`/api/v1/finance/invoices/${invoiceId}/download`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: 'include',
      })
      if (!res.ok) return
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `facture-${invoice?.invoice_number ?? invoiceId}.html`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // silently fail
    }
  }

  if (isLoading) return (
    <div className="flex items-center justify-center py-16 text-slate-400 text-sm">Chargement…</div>
  )
  if (!invoice) return (
    <div className="flex items-center justify-center py-16 text-slate-400 text-sm">Facture introuvable.</div>
  )

  return (
    <div className="max-w-3xl space-y-6">
      {/* Back + Header */}
      <div className="flex items-start gap-3">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 transition-colors mt-0.5"
        >
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-800 dark:text-white">{invoice.invoice_number}</h1>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                {formatDate(invoice.period_start)} – {formatDate(invoice.period_end)}
                {' · '}Créée le {formatDate(invoice.created_at)}
                {invoice.due_date && (
                  <span className="ml-2">· Échéance : <span className="font-medium">{formatDate(invoice.due_date)}</span></span>
                )}
              </p>
            </div>
            <StatusBadge status={invoice.status} />
          </div>
        </div>
      </div>

      {/* Line items */}
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
        <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
          {t('invoice.lineItems', 'Lignes de facturation')}
        </h2>
        {invoice.line_items && invoice.line_items.length > 0 ? (
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 dark:text-slate-400 border-b border-slate-100 dark:border-slate-700">
                <th className="pb-2 font-medium">Description</th>
                <th className="pb-2 text-right font-medium">Qté</th>
                <th className="pb-2 text-right font-medium">Prix unitaire</th>
                <th className="pb-2 text-right font-medium">Total</th>
              </tr>
            </thead>
            <tbody>
              {invoice.line_items.map((item) => (
                <tr key={item.line_item_id} className="border-b border-slate-50 dark:border-slate-700 last:border-0">
                  <td className="py-3 text-slate-700 dark:text-slate-300">{item.description}</td>
                  <td className="py-3 text-right text-slate-600 dark:text-slate-400">{item.quantity}</td>
                  <td className="py-3 text-right text-slate-600 dark:text-slate-400">
                    {formatCurrency(item.unit_price, invoice.currency)}
                  </td>
                  <td className="py-3 text-right font-medium text-slate-800 dark:text-slate-200">
                    {formatCurrency(item.total_price, invoice.currency)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-slate-400 text-sm">Aucune ligne.</p>
        )}

        {/* Totals */}
        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700 space-y-1.5 text-sm">
          <div className="flex justify-between text-slate-600 dark:text-slate-400">
            <span>Sous-total HT</span>
            <span>{formatCurrency(invoice.subtotal_ht, invoice.currency)}</span>
          </div>
          <div className="flex justify-between text-slate-600 dark:text-slate-400">
            <span>TVA ({invoice.tax_rate}%)</span>
            <span>{formatCurrency(invoice.tax_amount, invoice.currency)}</span>
          </div>
          <div className="flex justify-between font-bold text-slate-900 dark:text-white text-base pt-1 border-t border-slate-100 dark:border-slate-700">
            <span>Total TTC</span>
            <span>{formatCurrency(invoice.total_ttc, invoice.currency)}</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        {invoice.status === 'draft' && (
          <button
            onClick={() => finalize.mutate(invoiceId)}
            disabled={finalize.isPending}
            className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            <CheckCircle size={16} />
            {finalize.isPending ? 'Finalisation…' : 'Finaliser'}
          </button>
        )}
        {invoice.status === 'ready' && (
          <button
            onClick={() => send.mutate(invoiceId)}
            disabled={send.isPending}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            <Send size={16} />
            {send.isPending ? 'Envoi…' : 'Envoyer au client'}
          </button>
        )}
        {(invoice.status === 'sent' || invoice.status === 'overdue') && (
          <button
            onClick={() => markPaid.mutate({ id: invoiceId })}
            disabled={markPaid.isPending}
            className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            <BadgeCheck size={16} />
            {markPaid.isPending ? 'Enregistrement…' : 'Marquer payée'}
          </button>
        )}
        {(['sent', 'ready', 'paid'].includes(invoice.status)) && (
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 bg-slate-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors"
          >
            <Download size={16} /> Télécharger PDF
          </button>
        )}
      </div>

      {/* Audit log */}
      {auditLogs.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">Historique</h2>
          <ol className="relative border-l border-slate-200 dark:border-slate-700 space-y-4 ml-2">
            {auditLogs.map((log) => (
              <li key={log.log_id} className="ml-4">
                <div className="absolute -left-1.5 mt-1.5 w-3 h-3 rounded-full bg-indigo-200 dark:bg-indigo-700 border-2 border-white dark:border-slate-800" />
                <div className="flex items-center gap-2">
                  <Clock size={12} className="text-slate-400" />
                  <time className="text-xs text-slate-400">
                    {new Date(log.timestamp).toLocaleString('fr-FR')}
                  </time>
                </div>
                <p className="text-sm text-slate-700 dark:text-slate-300 mt-0.5">
                  <span className="font-medium">{ACTION_LABELS[log.action] ?? log.action}</span>
                  {log.performed_by_name && (
                    <span className="text-slate-500"> par {log.performed_by_name}</span>
                  )}
                </p>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}

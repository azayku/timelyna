import { CheckCircle, FileText, Clock, User } from 'lucide-react'
import Modal from '../ui/Modal'
import Button from '../ui/Button'
import { StatusBadge } from '../ui/Badge'
import { useTranslation } from 'react-i18next'

interface LineItem {
  project_name?: string
  description?: string
  hours?: number
  rate?: number
  subtotal: number
}

interface AuditEntry {
  id: number
  action: string
  performed_by: number | null
  details: Record<string, unknown> | null
  created_at: string
}

interface Invoice {
  id: number
  number: string
  client: string
  period: string
  subtotal_ht: number
  tax_amount: number
  total_ttc: number
  status: string
  due: string | null
  created: string
}

interface Props {
  invoice: Invoice
  open: boolean
  onClose: () => void
  onMarkPaid: (id: number) => void
}

const fmt = (n: number) =>
  new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n)

const fmtDate = (d: string | null) => {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

// Mock line items — in production these come from the API
const MOCK_LINE_ITEMS: LineItem[] = [
  { project_name: 'Développement API', hours: 40, rate: 150, subtotal: 6000 },
  { project_name: 'Intégration frontend', hours: 32, rate: 130, subtotal: 4160 },
  { project_name: 'Tests & QA', hours: 16, rate: 110, subtotal: 1760 },
]

// Mock audit log — in production fetched from /finance/invoices/:id/audit-logs
const MOCK_AUDIT: AuditEntry[] = [
  { id: 1, action: 'created', performed_by: 1, details: null, created_at: '2026-04-01T09:00:00Z' },
  { id: 2, action: 'finalized', performed_by: 1, details: null, created_at: '2026-04-02T10:30:00Z' },
  { id: 3, action: 'sent', performed_by: 2, details: null, created_at: '2026-04-02T11:00:00Z' },
]

const ACTION_LABELS: Record<string, string> = {
  created: 'Brouillon créé',
  finalized: 'Finalisée',
  sent: 'Envoyée au client',
  paid: 'Marquée payée',
  overdue: 'Passée en retard',
}

const ACTION_COLORS: Record<string, string> = {
  created: 'bg-slate-100 text-slate-600',
  finalized: 'bg-indigo-100 text-indigo-700',
  sent: 'bg-blue-100 text-blue-700',
  paid: 'bg-emerald-100 text-emerald-700',
  overdue: 'bg-red-100 text-red-700',
}

export default function InvoiceDetailModal({ invoice, open, onClose, onMarkPaid }: Props) {
  const { t } = useTranslation()
  const canMarkPaid = invoice.status === 'sent' || invoice.status === 'overdue'

  return (
    <Modal open={open} onClose={onClose} title={`Facture ${invoice.number}`} size="lg">
      <div className="space-y-6">

        {/* Header info */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-slate-400 mb-0.5">{t('common.client')}</p>
            <p className="text-sm font-semibold text-slate-800">{invoice.client}</p>
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-0.5">{t('common.period')}</p>
            <p className="text-sm font-semibold text-slate-800">{invoice.period}</p>
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-0.5">{t('invoices.dueDate')}</p>
            <p className={`text-sm font-semibold ${invoice.status === 'overdue' ? 'text-red-600' : 'text-slate-800'}`}>
              {fmtDate(invoice.due)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-0.5">{t('common.status')}</p>
            <StatusBadge status={invoice.status} />
          </div>
        </div>

        {/* Line items */}
        <div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <FileText size={12} />
            Lignes de facturation
          </h3>
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500">Description</th>
                  <th className="px-4 py-2.5 text-right text-xs font-semibold text-slate-500">Heures</th>
                  <th className="px-4 py-2.5 text-right text-xs font-semibold text-slate-500">Taux</th>
                  <th className="px-4 py-2.5 text-right text-xs font-semibold text-slate-500">Montant HT</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {MOCK_LINE_ITEMS.map((li, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="px-4 py-3 text-slate-700">{li.project_name}</td>
                    <td className="px-4 py-3 text-right text-slate-600">{li.hours}h</td>
                    <td className="px-4 py-3 text-right text-slate-600">{fmt(li.rate ?? 0)}/h</td>
                    <td className="px-4 py-3 text-right font-medium text-slate-800">{fmt(li.subtotal)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Totals */}
        <div className="bg-slate-50 rounded-lg p-4 space-y-2">
          <div className="flex justify-between text-sm text-slate-600">
            <span>Sous-total HT</span>
            <span className="font-medium">{fmt(invoice.subtotal_ht)}</span>
          </div>
          <div className="flex justify-between text-sm text-slate-600">
            <span>TVA (20%)</span>
            <span className="font-medium">{fmt(invoice.tax_amount)}</span>
          </div>
          <div className="flex justify-between text-base font-bold text-slate-800 pt-2 border-t border-slate-200">
            <span>Total TTC</span>
            <span className="text-indigo-600">{fmt(invoice.total_ttc)}</span>
          </div>
        </div>

        {/* Audit log */}
        <div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Clock size={12} />
            Historique
          </h3>
          <div className="space-y-2">
            {MOCK_AUDIT.map(entry => (
              <div key={entry.id} className="flex items-start gap-3">
                <div className="mt-0.5 flex-shrink-0">
                  <User size={14} className="text-slate-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${ACTION_COLORS[entry.action] ?? 'bg-slate-100 text-slate-600'}`}>
                      {ACTION_LABELS[entry.action] ?? entry.action}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(entry.created_at).toLocaleString('fr-FR', {
                        day: '2-digit', month: 'short', year: 'numeric',
                        hour: '2-digit', minute: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
          <Button variant="secondary" onClick={onClose}>{t('common.close')}</Button>
          {canMarkPaid && (
            <Button
              icon={<CheckCircle size={14} />}
              onClick={() => onMarkPaid(invoice.id)}
            >
              Marquer payée
            </Button>
          )}
        </div>
      </div>
    </Modal>
  )
}

import { useState, useMemo } from 'react'
import { CheckCircle, XCircle, Loader2, AlertTriangle } from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import DataGrid from '../components/DataGrid'
import type { ColDef } from 'ag-grid-community'
import { useTranslation } from 'react-i18next'
import {
  useManagerApprovals,
  useAdminApprovals,
  useApproveApproval,
  useRejectApproval,
  useApprovalEntries,
} from '../features/approvals/hooks'
import type { Approval } from '../features/approvals/types'
import { ApiError } from '../lib/apiClient'
import { useAuthStore } from '../lib/authStore'

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-700',
  approved: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-red-100 text-red-700',
  invoiced: 'bg-blue-100 text-blue-700',
}

function DetailModal({ approval, onClose }: { approval: Approval | null; onClose: () => void }) {
  const { t } = useTranslation()
  const [rejectReason, setRejectReason] = useState('')
  const [showReject, setShowReject] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)

  const approveMutation = useApproveApproval()
  const rejectMutation = useRejectApproval()
  const { data: entries = [], isLoading: loadingEntries } = useApprovalEntries(approval?.approval_id ?? 0)

  if (!approval) return null

  const handleApprove = async () => {
    setApiError(null)
    try {
      await approveMutation.mutateAsync({ id: approval.approval_id })
      onClose()
    } catch (err) {
      setApiError(err instanceof ApiError ? err.message : 'Erreur inattendue.')
    }
  }

  const handleReject = async () => {
    if (!rejectReason.trim()) return
    setApiError(null)
    try {
      await rejectMutation.mutateAsync({ id: approval.approval_id, reason: rejectReason })
      onClose()
    } catch (err) {
      setApiError(err instanceof ApiError ? err.message : 'Erreur inattendue.')
    }
  }

  return (
    <Modal open={!!approval} onClose={onClose}
      title={`${t('approvals.detail', 'Détail')} — ${approval.employee_name ?? `#${approval.employee_id}`}`}
      size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: t('approvals.week', 'Semaine'), value: approval.week_start },
            { label: t('common.total', 'Total'), value: approval.total_hours != null ? `${approval.total_hours}h` : '---' },
            { label: t('common.status', 'Statut'), value: (
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_COLORS[approval.status] ?? 'bg-slate-100 text-slate-600'}`}>
                {approval.status}
              </span>
            )},
          ].map(item => (
            <div key={item.label} className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs text-slate-400 mb-1">{item.label}</p>
              <div className="text-sm font-semibold text-slate-800">{item.value}</div>
            </div>
          ))}
        </div>

        {loadingEntries ? (
          <div className="flex items-center justify-center py-8 text-slate-400 text-sm gap-2">
            <Loader2 size={14} className="animate-spin" /> Chargement des entrées…
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                {['Date', 'Projet', 'Type', 'Heures'].map(h => (
                  <th key={h} className={`py-2 text-xs text-slate-500 font-semibold ${h === 'Heures' ? 'text-right' : 'text-left'}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {entries.map(e => (
                <tr key={e.timesheet_entry_id} className="hover:bg-slate-50">
                  <td className="py-2.5 text-slate-700">{new Date(e.work_date).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' })}</td>
                  <td className="py-2.5 text-slate-700">{e.project_name}</td>
                  <td className="py-2.5 text-slate-500 capitalize">{e.entry_type}</td>
                  <td className="py-2.5 text-right font-mono font-semibold text-slate-800">{e.hours_worked}h</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {apiError && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertTriangle size={15} className="flex-shrink-0 mt-0.5" />{apiError}
          </div>
        )}

        {approval.status === 'pending' && !showReject && (
          <div className="flex gap-3 pt-2">
            <Button icon={<CheckCircle size={14} />} onClick={handleApprove} loading={approveMutation.isPending}>
              {t('approvals.validate', 'Valider')}
            </Button>
            <Button variant="danger" icon={<XCircle size={14} />} onClick={() => setShowReject(true)}>
              {t('approvals.reject', 'Rejeter')}
            </Button>
          </div>
        )}

        {showReject && (
          <div className="space-y-3 pt-2">
            <textarea rows={3} value={rejectReason} onChange={e => setRejectReason(e.target.value)}
              placeholder={t('approvals.rejectPlaceholder', 'Motif du rejet…')}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-red-400" />
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setShowReject(false)}>{t('common.cancel', 'Annuler')}</Button>
              <Button variant="danger" disabled={rejectReason.length < 5} loading={rejectMutation.isPending} onClick={handleReject}>
                {t('approvals.confirmReject', 'Confirmer le rejet')}
              </Button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}

export default function ApprovalsPage() {
  const { t } = useTranslation()
  const [filter, setFilter] = useState('pending')
  const [detail, setDetail] = useState<Approval | null>(null)
  const role = useAuthStore((s) => s.user?.role ?? 'employee')
  const isAdmin = role === 'admin' || role === 'payroll'

  // Admins use /admin/approvals, managers use /manager/approvals
  const managerQuery = useManagerApprovals(filter)
  const adminQuery = useAdminApprovals(filter)
  const { data: approvals = [], isLoading, isError } = isAdmin ? adminQuery : managerQuery

  const colDefs = useMemo<ColDef<Approval>[]>(() => [
    {
      field: 'employee_name', headerName: t('common.employee', 'Employé'), flex: 1, minWidth: 160,
      cellRenderer: (p: { value: string }) => `<span class="font-medium text-slate-800">${p.value ?? '—'}</span>`,
    },
    {
      field: 'week_start', headerName: t('approvals.week', 'Semaine'), width: 130,
    },
    {
      field: 'total_hours', headerName: t('common.hours', 'Heures'), width: 100,
      valueFormatter: (p: { value: number | undefined }) => p.value != null ? `${p.value}h` : '---',
    },
    {
      field: 'submitted_at', headerName: t('approvals.submittedAt', 'Soumis le'), width: 140,
      valueFormatter: (p: { value: string }) => p.value ? new Date(p.value).toLocaleDateString('fr-FR') : '—',
    },
    {
      field: 'status', headerName: t('common.status', 'Statut'), width: 120,
      cellRenderer: (p: { value: string }) => {
        const cls = STATUS_COLORS[p.value] ?? 'bg-slate-100 text-slate-600'
        return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${cls}">${p.value}</span>`
      },
    },
  ], [t])

  const pendingCount = approvals.filter(a => a.status === 'pending').length

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 flex-wrap">
        {['pending', 'approved', 'rejected', 'all'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === f ? 'bg-indigo-600 text-white' : 'bg-white border border-slate-300 text-slate-600 hover:bg-slate-50'
            }`}>
            {f === 'all' ? t('approvals.all', 'Tous') :
             f === 'pending' ? t('approvals.pending', 'En attente') :
             f === 'approved' ? t('approvals.approved', 'Approuvés') :
             t('approvals.rejected', 'Rejetés')}
            {f === 'pending' && pendingCount > 0 && (
              <span className="ml-2 bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5">{pendingCount}</span>
            )}
          </button>
        ))}
      </div>

      <Card padding={false}>
        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
            <Loader2 size={16} className="animate-spin" /> Chargement…
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center gap-2 py-16 text-red-500 text-sm">
            <AlertTriangle size={16} /> Impossible de charger les approbations.
          </div>
        ) : approvals.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400 dark:text-slate-500">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-12 h-12 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="text-sm font-medium">{t('common.noData', 'Aucune donnée à afficher')}</p>
          </div>
        ) : (
          <DataGrid
            rowData={approvals}
            columnDefs={colDefs}
            storageKey="approvals-table"
            onRowClicked={(row: Approval) => setDetail(row)}
          />
        )}
      </Card>

      <DetailModal approval={detail} onClose={() => setDetail(null)} />
    </div>
  )
}

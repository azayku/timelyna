import { useState } from 'react'
import { X, Loader2, AlertTriangle } from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Table from '../components/ui/Table'
import { StatusBadge } from '../components/ui/Badge'
import { useTranslation } from 'react-i18next'
import { useSubmissions, useCancelSubmission } from '../features/approvals/hooks'
import type { Approval } from '../features/approvals/types'

export default function SubmissionsPage() {
  const { t } = useTranslation()
  const [statusFilter, setStatusFilter] = useState('all')
  const { data: submissions = [], isLoading, isError } = useSubmissions(statusFilter)
  const cancelMutation = useCancelSubmission()

  const counts = {
    pending: submissions.filter(s => s.status === 'pending').length,
    approved: submissions.filter(s => s.status === 'approved').length,
    rejected: submissions.filter(s => s.status === 'rejected').length,
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: t('submissions.pending', 'En attente'), value: counts.pending, color: 'text-amber-600' },
          { label: t('submissions.approved', 'Approuvés'), value: counts.approved, color: 'text-emerald-600' },
          { label: t('submissions.rejected', 'Rejetés'), value: counts.rejected, color: 'text-red-600' },
        ].map(item => (
          <Card key={item.label}>
            <p className="text-xs text-slate-400 mb-1">{item.label}</p>
            <p className={`text-3xl font-bold ${item.color}`}>{item.value}</p>
          </Card>
        ))}
      </div>

      <div className="flex gap-2">
        {[
          { value: 'all', label: t('submissions.filterAll', 'Tous') },
          { value: 'pending', label: t('submissions.filterPending', 'En attente') },
          { value: 'approved', label: t('submissions.filterApproved', 'Approuvés') },
          { value: 'rejected', label: t('submissions.filterRejected', 'Rejetés') },
        ].map(f => (
          <button key={f.value} onClick={() => setStatusFilter(f.value)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === f.value
                ? 'bg-indigo-600 text-white'
                : 'bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600'
            }`}>
            {f.label}
          </button>
        ))}
      </div>

      <Card padding={false}>
        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
            <Loader2 size={16} className="animate-spin" /> Chargement...
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center gap-2 py-16 text-red-500 text-sm">
            <AlertTriangle size={16} /> Impossible de charger les soumissions.
          </div>
        ) : (
          <Table
            columns={[
              {
                key: 'week_start',
                header: t('approvals.week', 'Semaine'),
                render: (r: Approval) => (
                  <span className="font-medium text-slate-800">{r.week_start}</span>
                ),
              },
              {
                key: 'total_hours',
                header: t('common.hours', 'Heures'),
                render: (r: Approval) => r.total_hours != null ? `${r.total_hours}h` : '—',
              },
              {
                key: 'submitted_at',
                header: t('approvals.submittedAt', 'Soumis le'),
                render: (r: Approval) =>
                  r.submitted_at ? new Date(r.submitted_at).toLocaleDateString('fr-FR') : '—',
              },
              {
                key: 'status',
                header: t('common.status', 'Statut'),
                render: (r: Approval) => <StatusBadge status={r.status} />,
              },
              {
                key: 'actions',
                header: '',
                width: '80px',
                render: (r: Approval) =>
                  r.status === 'pending' ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={<X size={13} />}
                      onClick={() => cancelMutation.mutate(r.approval_id)}
                      loading={cancelMutation.isPending}>
                      {t('submissions.cancelSubmission', 'Annuler')}
                    </Button>
                  ) : null,
              },
            ]}
            data={submissions}
          />
        )}
      </Card>
    </div>
  )
}

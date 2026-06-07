import { ScrollText, RefreshCw } from 'lucide-react'
import Card from '../components/ui/Card'
import Table from '../components/ui/Table'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'

interface ProxyLog {
  id: number
  admin_name: string
  employee_name: string
  started_at: string | null
  ended_at: string | null
  duration_seconds: number | null
  entries_created: number
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function ProxyLogsPage() {
  const { data: logs = [], isLoading, isError, refetch, isFetching } = useQuery<ProxyLog[]>({
    queryKey: ['proxy-logs'],
    queryFn: () => apiClient.get<ProxyLog[]>('/admin/proxy/logs'),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-orange-100 flex items-center justify-center">
            <ScrollText size={18} className="text-orange-600" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-800">Journaux proxy</h1>
            <p className="text-xs text-slate-500">Historique des sessions d'impersonation admin</p>
          </div>
        </div>
        <button onClick={() => refetch()} disabled={isFetching}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50">
          <RefreshCw size={14} className={isFetching ? 'animate-spin' : ''} />
          Actualiser
        </button>
      </div>

      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
          Impossible de charger les journaux proxy.
        </div>
      )}

      <Card padding={false}>
        <Table
          columns={[
            { key: 'admin_name', header: 'Administrateur', render: (r: ProxyLog) => <span className="font-medium text-slate-800">{r.admin_name}</span> },
            { key: 'employee_name', header: 'Employé impersonné', render: (r: ProxyLog) => <span className="text-slate-700">{r.employee_name}</span> },
            { key: 'started_at', header: 'Début', render: (r: ProxyLog) => <span className="text-slate-500 text-sm">{formatDate(r.started_at)}</span> },
            { key: 'ended_at', header: 'Fin', render: (r: ProxyLog) => r.ended_at
              ? <span className="text-slate-500 text-sm">{formatDate(r.ended_at)}</span>
              : <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700">En cours</span>
            },
            { key: 'duration_seconds', header: 'Durée', render: (r: ProxyLog) => <span className="text-slate-600 text-sm font-mono">{formatDuration(r.duration_seconds)}</span> },
            { key: 'entries_created', header: 'Pointages créés', render: (r: ProxyLog) => (
              <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold ${r.entries_created > 0 ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-500'}`}>
                {r.entries_created}
              </span>
            )},
          ]}
          data={logs}
        />
        {isLoading && (
          <div className="flex items-center justify-center py-12 text-slate-400 text-sm">Chargement…</div>
        )}
        {!isLoading && logs.length === 0 && (
          <div className="flex items-center justify-center py-12 text-slate-400 text-sm">Aucune session proxy enregistrée</div>
        )}
      </Card>
    </div>
  )
}

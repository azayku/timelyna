import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'
import { Shield, Search } from 'lucide-react'

interface AuditEntry {
  id: number
  timestamp: string
  user_email: string
  action: string
  resource: string
  resource_id?: number
  details?: string
  ip_address?: string
}

async function getAuditLogs(params: { page?: number; search?: string }): Promise<{ items: AuditEntry[]; total: number }> {
  const searchParams = new URLSearchParams()
  if (params.page) searchParams.append('page', params.page.toString())
  if (params.search) searchParams.append('search', params.search)
  const queryString = searchParams.toString()
  const url = `/admin/audit-logs${queryString ? `?${queryString}` : ''}`
  const res = await apiClient.get<{ items: AuditEntry[]; total: number }>(url)
  return res
}

export default function AuditLogPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  
  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', page, search],
    queryFn: () => getAuditLogs({ page, search: search || undefined }),
    placeholderData: prev => prev,
  })

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Shield className="h-6 w-6 text-indigo-500" />
        <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Journal d'audit</h1>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <input
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
          placeholder="Rechercher par utilisateur, action..."
          className="w-full pl-9 pr-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-800 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-slate-500">Chargement...</div>
        ) : !data?.items?.length ? (
          <div className="p-8 text-center text-slate-500">Aucun log trouvé</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Date</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Utilisateur</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Action</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Ressource</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {data.items.map(log => (
                <tr key={log.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400 whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString('fr-FR')}
                  </td>
                  <td className="px-4 py-3 text-slate-800 dark:text-white font-medium">{log.user_email}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 rounded text-xs font-mono">
                      {log.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                    {log.resource}{log.resource_id ? ` #${log.resource_id}` : ''}
                  </td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400 text-xs font-mono">
                    {log.ip_address || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

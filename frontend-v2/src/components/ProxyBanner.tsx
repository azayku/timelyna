import { useState } from 'react'
import { ShieldAlert, X, Clock } from 'lucide-react'
import { useProxyStore } from '../lib/proxyStore'

export default function ProxyBanner() {
  const { isProxy, proxiedEmployee, proxyLogId, proxyToken, endProxy } = useProxyStore()
  const [ending, setEnding] = useState(false)

  if (!isProxy || !proxiedEmployee) return null

  const handleEnd = async () => {
    setEnding(true)
    try {
      await fetch('/api/v1/admin/proxy/end', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(proxyToken ? { Authorization: `Bearer ${proxyToken}` } : {}),
        },
        body: JSON.stringify({ proxy_log_id: proxyLogId, entries_created: 0 }),
      })
    } catch {
      // Quitter le proxy même en cas d'erreur réseau
    } finally {
      endProxy()
      setEnding(false)
    }
  }

  return (
    <div className="flex items-center justify-between gap-4 bg-orange-500 text-white px-5 py-2.5 text-sm font-medium z-50 flex-shrink-0">
      <div className="flex items-center gap-2">
        <ShieldAlert size={16} className="flex-shrink-0" />
        <span>
          Mode proxy actif — vous agissez en tant que{' '}
          <span className="font-bold">{proxiedEmployee.name}</span>
          <span className="ml-2 opacity-80 text-xs">({proxiedEmployee.email})</span>
        </span>
      </div>
      <button
        onClick={handleEnd}
        disabled={ending}
        className="flex items-center gap-1.5 bg-white/20 hover:bg-white/30 transition-colors rounded-lg px-3 py-1 text-xs font-semibold disabled:opacity-60"
      >
        {ending ? (
          <>
            <Clock size={12} className="animate-spin" />
            Fermeture…
          </>
        ) : (
          <>
            <X size={12} />
            Quitter le proxy
          </>
        )}
      </button>
    </div>
  )
}

import { Mail, DollarSign, FolderOpen, Receipt, TrendingUp, ExternalLink } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import Modal from '../ui/Modal'
import { StatusBadge } from '../ui/Badge'

export interface Client {
  id: number
  name: string
  email: string
  rate: number
  currency: string
  status: string
  projects: number
  projectNames?: string[]
  totalRevenue?: number
  pendingInvoices?: number
  totalHours?: number
}

const fmt = (n: number, currency = 'EUR') =>
  new Intl.NumberFormat('fr-FR', { style: 'currency', currency, maximumFractionDigits: 0 }).format(n)

interface Props {
  client: Client | null
  onClose: () => void
  onEdit?: (c: Client) => void
}

export default function ClientDetailModal({ client, onClose, onEdit }: Props) {
  const navigate = useNavigate()
  if (!client) return null

  return (
    <Modal open={!!client} onClose={onClose} title="Fiche client" size="md">
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center text-amber-700 text-lg font-bold">
              {client.name.charAt(0)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-slate-800">{client.name}</h2>
                <StatusBadge status={client.status} />
              </div>
              <p className="text-sm text-slate-400 mt-0.5">{client.email}</p>
            </div>
          </div>
          <div className="flex gap-2 flex-shrink-0">
            {onEdit && (
              <button onClick={() => onEdit(client)} className="px-3 py-1.5 text-sm font-medium text-indigo-600 border border-indigo-200 rounded-lg hover:bg-indigo-50">
                Modifier
              </button>
            )}
            <button
              onClick={() => { navigate('/admin/clients'); onClose() }}
              className="px-3 py-1.5 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 flex items-center gap-1.5"
            >
              <ExternalLink size={13} /> Voir tout
            </button>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 gap-3">
          {[
            { icon: <DollarSign size={16} className="text-indigo-500" />, label: 'Taux horaire', value: `${client.rate} ${client.currency}/h`, bg: 'bg-indigo-50' },
            { icon: <FolderOpen size={16} className="text-emerald-500" />, label: 'Projets actifs', value: client.projects, bg: 'bg-emerald-50' },
            { icon: <TrendingUp size={16} className="text-purple-500" />, label: 'CA total', value: client.totalRevenue ? fmt(client.totalRevenue, client.currency) : '—', bg: 'bg-purple-50' },
            { icon: <Receipt size={16} className="text-amber-500" />, label: 'Factures en attente', value: client.pendingInvoices ?? 0, bg: 'bg-amber-50' },
          ].map(kpi => (
            <div key={kpi.label} className={`${kpi.bg} rounded-xl p-3`}>
              <div className="flex items-center gap-2 mb-1">{kpi.icon}<span className="text-xs text-slate-500">{kpi.label}</span></div>
              <p className="text-lg font-bold text-slate-800">{kpi.value}</p>
            </div>
          ))}
        </div>

        {/* Contact */}
        <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
          <Mail size={15} className="text-slate-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-xs text-slate-400 mb-0.5">Email de facturation</p>
            <a href={`mailto:${client.email}`} className="text-sm font-medium text-indigo-600 hover:underline">{client.email}</a>
          </div>
        </div>

        {/* Projects list */}
        {client.projectNames && client.projectNames.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Projets</p>
            <div className="space-y-1.5">
              {client.projectNames.map((name, i) => (
                <div key={i} className="flex items-center gap-2 px-3 py-2 bg-slate-50 rounded-lg">
                  <FolderOpen size={13} className="text-slate-400" />
                  <span className="text-sm text-slate-700">{name}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}

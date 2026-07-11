import { useState, useMemo } from 'react'
import { Plus, Search, Upload, X, AlertTriangle, Loader2, Pencil, Trash2 } from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import PaginatedTable from '../components/ui/PaginatedTable'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import { useTranslation } from 'react-i18next'
import ClientDetailModal, { type Client as ClientModalShape } from '../components/modals/ClientDetailModal'
import ImportModal from '../components/modals/ImportModal'
import { useClients, useCreateClient, useUpdateClient, useDeleteClient } from '../features/clients/hooks'
import type { Client } from '../features/clients/types'
import { ApiError } from '../lib/apiClient'

function toModalShape(c: Client): ClientModalShape {
  return {
    id: c.client_id,
    name: c.client_name,
    email: c.email,
    rate: Number(c.default_billing_rate),
    currency: c.currency,
    status: c.client_status,
    projects: 0,
  }
}

interface ClientFormModalProps {
  open: boolean
  onClose: () => void
  initial?: Client | null
}

function ClientFormModal({ open, onClose, initial }: ClientFormModalProps) {
  const isEdit = !!initial
  const createMutation = useCreateClient()
  const updateMutation = useUpdateClient()
  const [form, setForm] = useState({
    client_name: initial?.client_name ?? '',
    email: initial?.email ?? '',
    default_billing_rate: initial ? String(initial.default_billing_rate) : '',
    currency: initial?.currency ?? 'EUR',
    phone: initial?.phone ?? '',
    address: initial?.address ?? '',
  })
  const [apiError, setApiError] = useState<string | null>(null)
  const isPending = createMutation.isPending || updateMutation.isPending
  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setApiError(null)
    try {
      const payload = {
        client_name: form.client_name.trim(),
        email: form.email.trim(),
        default_billing_rate: Number(form.default_billing_rate),
        currency: form.currency,
        phone: form.phone.trim() || undefined,
        address: form.address.trim() || undefined,
      }
      if (isEdit && initial) {
        await updateMutation.mutateAsync({ id: initial.client_id, payload })
      } else {
        await createMutation.mutateAsync(payload)
      }
      onClose()
    } catch (err) {
      setApiError(err instanceof ApiError ? err.message : 'Une erreur inattendue est survenue.')
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? 'Modifier le client' : 'Nouveau client'} size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Nom *</label>
          <input value={form.client_name} onChange={e => set('client_name', e.target.value)} required
            className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Email *</label>
          <input type="email" value={form.email} onChange={e => set('email', e.target.value)} required
            className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Taux horaire *</label>
            <input type="number" min={0} step={0.01} value={form.default_billing_rate}
              onChange={e => set('default_billing_rate', e.target.value)} required
              className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Devise</label>
            <select value={form.currency} onChange={e => set('currency', e.target.value)}
              className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
              {['EUR', 'USD', 'GBP', 'CHF', 'MAD'].map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Téléphone</label>
          <input value={form.phone} onChange={e => set('phone', e.target.value)}
            className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Adresse</label>
          <textarea value={form.address} onChange={e => set('address', e.target.value)} rows={2}
            className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        {apiError && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertTriangle size={15} className="flex-shrink-0 mt-0.5" />{apiError}
          </div>
        )}
        <div className="flex gap-3 justify-end pt-2">
          <Button variant="secondary" type="button" onClick={onClose}>Annuler</Button>
          <Button type="submit" loading={isPending}>{isEdit ? 'Enregistrer' : 'Créer'}</Button>
        </div>
      </form>
    </Modal>
  )
}

export default function AdminClientsPage() {
  const { t } = useTranslation()
  const { data: clients = [], isLoading, isError } = useClients()
  const deleteMutation = useDeleteClient()

  const [search, setSearch] = useState('')
  const [createModal, setCreateModal] = useState(false)
  const [editClient, setEditClient] = useState<Client | null>(null)
  const [detailClient, setDetailClient] = useState<ClientModalShape | null>(null)
  const [importModal, setImportModal] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return clients.filter(c =>
      c.client_name.toLowerCase().includes(q) || c.email.toLowerCase().includes(q)
    )
  }, [clients, search])

  const columns = useMemo(() => [
    {
      key: 'client_name',
      header: t('common.name', 'Nom'),
      render: (c: Client) => <span className="font-medium text-slate-800 dark:text-slate-200">{c.client_name}</span>,
    },
    {
      key: 'email',
      header: t('common.email', 'Email'),
      render: (c: Client) => <span className="text-slate-500">{c.email}</span>,
    },
    {
      key: 'default_billing_rate',
      header: 'Taux/h',
      width: '120px',
      render: (c: Client) => <span className="font-mono text-sm">{Number(c.default_billing_rate).toFixed(0)} {c.currency}/h</span>,
    },
    {
      key: 'client_status',
      header: t('common.status', 'Statut'),
      width: '100px',
      render: (c: Client) => (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${c.client_status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
          {c.client_status === 'active' ? 'Actif' : 'Inactif'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '80px',
      sortable: false,
      render: (c: Client) => (
        <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
          <button onClick={() => setEditClient(c)} aria-label="Modifier" className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-indigo-600">
            <Pencil size={13} />
          </button>
          <button onClick={() => setDeleteConfirm(c.client_id)} aria-label="Supprimer" className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-600">
            <Trash2 size={13} />
          </button>
        </div>
      ),
    },
  ], [t, deleteMutation])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 w-72">
          <Search size={14} className="text-slate-400" />
          <input type="text" placeholder={t('common.search', 'Rechercher') + '…'} value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-transparent text-sm text-slate-700 dark:text-slate-300 outline-none w-full placeholder-slate-400" />
          {search && <button onClick={() => setSearch('')} aria-label="Effacer la recherche" className="text-slate-400 hover:text-slate-600"><X size={13} /></button>}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" icon={<Upload size={14} />} onClick={() => setImportModal(true)}>Importer Excel</Button>
          <Button icon={<Plus size={14} />} onClick={() => setCreateModal(true)}>{t('clients.new', 'Nouveau client')}</Button>
        </div>
      </div>

      <Card padding={false}>
        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
            <Loader2 size={16} className="animate-spin" /> Chargement…
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center gap-2 py-16 text-red-500 text-sm">
            <AlertTriangle size={16} /> Impossible de charger les clients.
          </div>
        ) : (
          <PaginatedTable
            data={filtered}
            columns={columns}
            pageSize={25}
            emptyMessage="Aucun client trouvé."
            onRowClick={(c) => setDetailClient(toModalShape(c))}
          />
        )}
      </Card>

      <ClientDetailModal client={detailClient} onClose={() => setDetailClient(null)} />
      {createModal && <ClientFormModal open onClose={() => setCreateModal(false)} />}
      {editClient && <ClientFormModal open onClose={() => setEditClient(null)} initial={editClient} />}
      <ImportModal open={importModal} onClose={() => setImportModal(false)} entity="clients" />
      
      <ConfirmDialog
        open={deleteConfirm !== null}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => {
          if (deleteConfirm !== null) {
            deleteMutation.mutate(deleteConfirm)
            setDeleteConfirm(null)
          }
        }}
        title="Supprimer le client"
        message="Êtes-vous sûr de vouloir supprimer ce client ? Cette action est irréversible."
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  )
}

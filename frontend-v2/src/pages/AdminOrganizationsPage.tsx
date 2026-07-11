import { useState } from 'react'
import { Plus, Pencil, Trash2, Search, Building2, Users, AlertTriangle, X, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Table from '../components/ui/Table'
import Modal from '../components/ui/Modal'
import {
  useOrganizations,
  useCreateOrganization,
  useUpdateOrganization,
  useDeleteOrganization,
} from '../features/organizations/hooks'
import type { Organization } from '../features/organizations/types'
import { useEmployees } from '../features/employees/hooks'
import { ApiError } from '../lib/apiClient'

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
  } catch { return iso }
}

// ── OrgFormModal ───────────────────────────────────────────────────────────

interface OrgFormModalProps {
  open: boolean
  onClose: () => void
  initial?: Organization | null
}

function OrgFormModal({ open, onClose, initial }: OrgFormModalProps) {
  const isEdit = !!initial
  const createMutation = useCreateOrganization()
  const updateMutation = useUpdateOrganization()
  const { data: employees = [] } = useEmployees()

  // Only managers and admins can be org managers
  const managers = employees.filter(e =>
    (e.role === 'manager' || e.role === 'admin') && e.employment_status === 'active'
  )

  const [orgName, setOrgName] = useState(initial?.org_name ?? '')
  const [managerId, setManagerId] = useState<number | ''>(initial?.manager_id ?? '')
  const [apiError, setApiError] = useState<string | null>(null)

  const isPending = createMutation.isPending || updateMutation.isPending

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!orgName.trim() || managerId === '') return
    setApiError(null)
    try {
      if (isEdit && initial) {
        await updateMutation.mutateAsync({
          id: initial.org_id,
          payload: { org_name: orgName.trim(), manager_id: Number(managerId) },
        })
      } else {
        await createMutation.mutateAsync({ org_name: orgName.trim(), manager_id: Number(managerId) })
      }
      onClose()
    } catch (err) {
      if (err instanceof ApiError) {
        setApiError(err.code === 'invalid_manager'
          ? 'Le manager sélectionné est invalide ou n\'a pas le rôle requis.'
          : err.message)
      } else {
        setApiError('Une erreur inattendue est survenue.')
      }
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? 'Modifier l\'organisation' : 'Nouvelle organisation'} size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1.5">Nom de l'organisation *</label>
          <input value={orgName} onChange={e => setOrgName(e.target.value)} placeholder="Ex: Équipe Paris" required
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1.5">Manager responsable *</label>
          <select value={managerId} onChange={e => setManagerId(e.target.value === '' ? '' : Number(e.target.value))} required
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
            <option value="">— Choisir un manager —</option>
            {managers.map(m => (
              <option key={m.employee_id} value={m.employee_id}>{m.first_name} {m.last_name} ({m.role})</option>
            ))}
          </select>
          <p className="text-[11px] text-slate-400 mt-1">
            Seuls les utilisateurs avec le rôle <em>manager</em> ou <em>admin</em> sont listés.
          </p>
        </div>
        {apiError && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertTriangle size={15} className="flex-shrink-0 mt-0.5" />{apiError}
          </div>
        )}
        <div className="flex gap-3 justify-end pt-2">
          <Button variant="secondary" type="button" onClick={onClose}>Annuler</Button>
          <Button type="submit" loading={isPending} disabled={!orgName.trim() || managerId === ''}>
            {isEdit ? 'Enregistrer' : 'Créer l\'organisation'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

// ── DeleteConfirmModal ─────────────────────────────────────────────────────

function DeleteConfirmModal({ org, onClose }: { org: Organization | null; onClose: () => void }) {
  const deleteMutation = useDeleteOrganization()
  const [apiError, setApiError] = useState<string | null>(null)

  const handleDelete = async () => {
    if (!org) return
    setApiError(null)
    try {
      await deleteMutation.mutateAsync(org.org_id)
      onClose()
    } catch (err) {
      setApiError(err instanceof ApiError ? err.message : 'Une erreur inattendue est survenue.')
    }
  }

  return (
    <Modal open={!!org} onClose={onClose} title="Supprimer l'organisation" size="sm">
      <div className="space-y-4">
        <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-xl">
          <AlertTriangle size={16} className="text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-amber-800">
            <p className="font-semibold mb-0.5">Suppression logique</p>
            <p>L'organisation <strong>{org?.org_name}</strong> sera désactivée. Les employés rattachés conservent leur compte.</p>
          </div>
        </div>
        {apiError && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertTriangle size={15} className="flex-shrink-0 mt-0.5" />{apiError}
          </div>
        )}
        <div className="flex gap-3 justify-end">
          <Button variant="secondary" onClick={onClose}>Annuler</Button>
          <Button variant="danger" loading={deleteMutation.isPending} onClick={handleDelete}>Supprimer</Button>
        </div>
      </div>
    </Modal>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function AdminOrganizationsPage() {
  const { t } = useTranslation()
  const { data: orgs = [], isLoading, isError } = useOrganizations()
  const { data: employees = [] } = useEmployees()
  const [search, setSearch] = useState('')
  const [createModal, setCreateModal] = useState(false)
  const [editOrg, setEditOrg] = useState<Organization | null>(null)
  const [deleteOrg, setDeleteOrg] = useState<Organization | null>(null)

  const filtered = orgs.filter(o => o.org_name.toLowerCase().includes(search.toLowerCase()))

  const managerName = (managerId: number | null) => {
    if (!managerId) return '—'
    const emp = employees.find(e => e.employee_id === managerId)
    return emp ? `${emp.first_name} ${emp.last_name}` : `#${managerId}`
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 bg-white border border-slate-300 rounded-lg px-3 py-2 w-72">
          <Search size={14} className="text-slate-400" />
          <input type="text" placeholder={t('common.search', 'Rechercher')} value={search} onChange={e => setSearch(e.target.value)}
            className="bg-transparent text-sm text-slate-700 outline-none w-full placeholder-slate-400" />
          {search && <button onClick={() => setSearch('')} aria-label="Effacer la recherche" className="text-slate-400 hover:text-slate-600"><X size={13} /></button>}
        </div>
        <Button icon={<Plus size={14} />} onClick={() => setCreateModal(true)}>Nouvelle organisation</Button>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center">
            <Building2 size={18} className="text-indigo-500" />
          </div>
          <div>
            <p className="text-xs text-slate-400">Organisations actives</p>
            <p className="text-xl font-bold text-slate-800">{orgs.length}</p>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center">
            <Users size={18} className="text-emerald-500" />
          </div>
          <div>
            <p className="text-xs text-slate-400">Total employés</p>
            <p className="text-xl font-bold text-slate-800">{orgs.reduce((s, o) => s + o.employee_count, 0)}</p>
          </div>
        </div>
      </div>

      <Card padding={false}>
        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
            <Loader2 size={16} className="animate-spin" /> Chargement…
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center gap-2 py-16 text-red-500 text-sm">
            <AlertTriangle size={16} /> Impossible de charger les organisations.
          </div>
        ) : (
          <Table
            columns={[
              {
                key: 'org_name', header: 'Organisation',
                render: (row: Organization) => (
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0">
                      <Building2 size={14} className="text-indigo-600" />
                    </div>
                    <span className="font-medium text-slate-800">{row.org_name}</span>
                  </div>
                ),
              },
              {
                key: 'manager_id', header: 'Manager',
                render: (row: Organization) => <span className="text-slate-600">{managerName(row.manager_id)}</span>,
              },
              {
                key: 'employee_count', header: 'Employés',
                render: (row: Organization) => (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                    <Users size={11} />{row.employee_count}
                  </span>
                ),
              },
              {
                key: 'created_at', header: 'Créée le',
                render: (row: Organization) => <span className="text-slate-400 text-sm">{formatDate(row.created_at)}</span>,
              },
              {
                key: 'actions', header: '', width: '90px',
                render: (row: Organization) => (
                  <div className="flex items-center gap-1">
                    <button onClick={() => setEditOrg(row)} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500" title="Modifier">
                      <Pencil size={13} />
                    </button>
                    <button onClick={() => setDeleteOrg(row)} className="p-1.5 rounded-lg hover:bg-red-50 text-red-400" title="Supprimer">
                      <Trash2 size={13} />
                    </button>
                  </div>
                ),
              },
            ]}
            data={filtered}
          />
        )}
      </Card>

      <OrgFormModal open={createModal} onClose={() => setCreateModal(false)} />
      <OrgFormModal open={!!editOrg} onClose={() => setEditOrg(null)} initial={editOrg} />
      <DeleteConfirmModal org={deleteOrg} onClose={() => setDeleteOrg(null)} />
    </div>
  )
}

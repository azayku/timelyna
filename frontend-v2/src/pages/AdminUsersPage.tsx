import { useState, useMemo } from 'react'
import { Plus, UserCheck, Clock, Search, AlertTriangle, Loader2, X, Pencil, UserX, UserCheck as UserCheckIcon, Shield, Upload } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { swalDark, swalConfirm } from '../lib/swalConfig'
import PaginatedTable from '../components/ui/PaginatedTable'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import Card from '../components/ui/Card'
import Table from '../components/ui/Table'
import EmployeeDetailModal from '../components/modals/EmployeeDetailModal'
import MutationModal from '../components/MutationModal'
import {
  useEmployees,
  useCreateEmployee,
  useUpdateEmployee,
  useDeactivateEmployee,
  useScheduleDeactivation,
  useCancelScheduledDeactivation,
  usePendingEmployees,
  useActivatePendingEmployee,
  useDeletePendingEmployee,
} from '../features/employees/hooks'
import { startProxy } from '../features/employees/api'
import type { Employee, PendingEmployee } from '../features/employees/types'
import { useAuthStore } from '../lib/authStore'
import { useProxyStore } from '../lib/proxyStore'
import { ApiError } from '../lib/apiClient'
import { useOrganizations } from '../features/organizations/hooks'
import { importUsersCSV } from '../features/imports/api'
import { useQueryClient } from '@tanstack/react-query'

// ── Helpers ────────────────────────────────────────────────────────────────

const fullName = (e: Employee) => `${e.first_name} ${e.last_name}`.trim()

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-purple-100 text-purple-700',
  manager: 'bg-blue-100 text-blue-700',
  finance: 'bg-amber-100 text-amber-700',
  payroll: 'bg-teal-100 text-teal-700',
  employee: 'bg-slate-100 text-slate-600',
}

function calcAge(birthDate: string | null): string {
  if (!birthDate) return '—'
  const diff = Date.now() - new Date(birthDate).getTime()
  return `${Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25))} ans`
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

// ── UserFormModal ──────────────────────────────────────────────────────────

interface UserFormModalProps {
  open: boolean
  onClose: () => void
  initial?: Employee | null
  orgs: { org_id: number; org_name: string }[]
}

const ROLES = ['employee', 'manager', 'admin', 'finance', 'payroll'] as const

function UserFormModal({ open, onClose, initial, orgs }: UserFormModalProps) {
  const { t } = useTranslation()
  const isEdit = !!initial
  const createMutation = useCreateEmployee()
  const updateMutation = useUpdateEmployee()

  const [form, setForm] = useState({
    first_name: initial?.first_name ?? '',
    last_name: initial?.last_name ?? '',
    email: initial?.email ?? '',
    role: initial?.role ?? 'employee',
    org_id: initial?.org_id ?? (orgs[0]?.org_id ?? 1),
    birth_date: initial?.birth_date ?? '',
    address: initial?.address ?? '',
    hire_date: '',
  })
  const [apiError, setApiError] = useState<string | null>(null)
  const [pendingBadge, setPendingBadge] = useState<string | null>(null)

  const isPending = createMutation.isPending || updateMutation.isPending

  const set = (k: string, v: string | number) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setApiError(null)
    setPendingBadge(null)
    try {
      if (isEdit && initial) {
        await updateMutation.mutateAsync({
          id: initial.employee_id,
          payload: {
            first_name: form.first_name.trim() || undefined,
            last_name: form.last_name.trim() || undefined,
            role: form.role as Employee['role'],
            org_id: Number(form.org_id),
            birth_date: form.birth_date || undefined,
            address: form.address || undefined,
          },
        })
        onClose()
      } else {
        const result = await createMutation.mutateAsync({
          first_name: form.first_name.trim(),
          last_name: form.last_name.trim(),
          email: form.email.trim(),
          role: form.role as Employee['role'],
          org_id: Number(form.org_id),
          birth_date: form.birth_date || undefined,
          address: form.address.trim() || undefined,
          hire_date: form.hire_date || undefined,
        })
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const r = result as any
        if (r?.type === 'pending') {
          setPendingBadge(r.account_creation_date)
        } else {
          onClose()
        }
      }
    } catch (err) {
      if (err instanceof ApiError) setApiError(err.message)
      else setApiError('Une erreur inattendue est survenue.')
    }
  }

  const age = form.birth_date ? calcAge(form.birth_date) : null

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? 'Modifier l\'utilisateur' : 'Nouvel utilisateur'} size="lg">
      {pendingBadge ? (
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-xl">
            <Clock size={18} className="text-blue-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-blue-800">Compte prévu le {fmtDate(pendingBadge)}</p>
              <p className="text-sm text-blue-600 mt-1">
                La date d'entrée est dans le futur. Le compte sera créé automatiquement à la date prévue.
              </p>
            </div>
          </div>
          <div className="flex justify-end">
            <Button onClick={onClose}>Fermer</Button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {!isEdit && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1.5">Prénom *</label>
                <input value={form.first_name} onChange={e => set('first_name', e.target.value)} required
                  placeholder={t('users.firstName', 'Prénom')}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1.5">Nom *</label>
                <input value={form.last_name} onChange={e => set('last_name', e.target.value)} required
                  placeholder={t('users.lastName', 'Nom')}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-semibold text-slate-500 mb-1.5">Email *</label>
                <input type="email" value={form.email} onChange={e => set('email', e.target.value)} required
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
            </div>
          )}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1.5">Rôle *</label>
              <select value={form.role} onChange={e => set('role', e.target.value)} required
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1.5">Organisation *</label>
              <select value={String(form.org_id)} onChange={e => set('org_id', Number(e.target.value))} required
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                {orgs.map(o => <option key={o.org_id} value={o.org_id}>{o.org_name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1.5">
                Date de naissance * {age && <span className="font-normal text-slate-400">({age})</span>}
              </label>
              <input type="date" value={form.birth_date} onChange={e => set('birth_date', e.target.value)} required
                max={new Date().toISOString().split('T')[0]}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            {!isEdit && (
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1.5">Date d'entrée</label>
                <input type="date" value={form.hire_date} onChange={e => set('hire_date', e.target.value)}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
              </div>
            )}
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Adresse *</label>
            <textarea value={form.address} onChange={e => set('address', e.target.value)} required rows={2}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          </div>
          {apiError && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              <AlertTriangle size={15} className="flex-shrink-0 mt-0.5" />
              {apiError}
            </div>
          )}
          <div className="flex gap-3 justify-end pt-2">
            <Button variant="secondary" type="button" onClick={onClose}>Annuler</Button>
            <Button type="submit" loading={isPending}>{isEdit ? 'Enregistrer' : 'Créer'}</Button>
          </div>
        </form>
      )}
    </Modal>
  )
}

// ── DeactivateModal ────────────────────────────────────────────────────────

interface DeactivateModalProps {
  employee: Employee | null
  onClose: () => void
}

function DeactivateModal({ employee, onClose }: DeactivateModalProps) {
  const [mode, setMode] = useState<'immediate' | 'scheduled'>('immediate')
  const [scheduledAt, setScheduledAt] = useState('')
  const [apiError, setApiError] = useState<string | null>(null)
  const deactivate = useDeactivateEmployee()
  const schedule = useScheduleDeactivation()

  const isPending = deactivate.isPending || schedule.isPending

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!employee) return
    setApiError(null)
    try {
      if (mode === 'immediate') {
        await deactivate.mutateAsync(employee.employee_id)
      } else {
        await schedule.mutateAsync({ id: employee.employee_id, payload: { scheduled_at: scheduledAt } })
      }
      onClose()
    } catch (err) {
      if (err instanceof ApiError) setApiError(err.message)
      else setApiError('Une erreur inattendue est survenue.')
    }
  }

  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  const minDate = tomorrow.toISOString().split('T')[0]

  return (
    <Modal open={!!employee} onClose={onClose} title="Désactiver le compte" size="sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-3">
          {(['immediate', 'scheduled'] as const).map(m => (
            <button key={m} type="button" onClick={() => setMode(m)}
              className={`flex-1 py-2 rounded-lg text-sm font-medium border-2 transition-colors ${
                mode === m ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-slate-200 text-slate-500 hover:border-slate-300'
              }`}>
              {m === 'immediate' ? 'Immédiat' : 'Différé'}
            </button>
          ))}
        </div>
        {mode === 'scheduled' && (
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Date de désactivation *</label>
            <input type="date" value={scheduledAt} onChange={e => setScheduledAt(e.target.value)}
              min={minDate} required
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          </div>
        )}
        {apiError && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertTriangle size={15} className="flex-shrink-0 mt-0.5" />
            {apiError}
          </div>
        )}
        <div className="flex gap-3 justify-end pt-2">
          <Button variant="secondary" type="button" onClick={onClose}>Annuler</Button>
          <Button variant="danger" type="submit" loading={isPending}>
            {mode === 'immediate' ? 'Désactiver' : 'Planifier'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

// ── PendingTab ─────────────────────────────────────────────────────────────

function PendingTab() {
  const { data: pending = [], isLoading, isError } = usePendingEmployees()
  const activate = useActivatePendingEmployee()
  const remove = useDeletePendingEmployee()

  if (isLoading) return (
    <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
      <Loader2 size={16} className="animate-spin" /> Chargement…
    </div>
  )
  if (isError) return (
    <div className="flex items-center justify-center gap-2 py-16 text-red-500 text-sm">
      <AlertTriangle size={16} /> Impossible de charger les recrutements en attente.
    </div>
  )
  if (pending.length === 0) return (
    <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
      Aucun recrutement en attente.
    </div>
  )

  return (
    <Table
      columns={[
        { key: 'full_name', header: 'Nom', render: (r: PendingEmployee) => <span className="font-medium text-slate-800">{r.full_name}</span> },
        { key: 'email', header: 'Email', render: (r: PendingEmployee) => <span className="text-slate-500">{r.email}</span> },
        { key: 'role', header: 'Rôle', render: (r: PendingEmployee) => (
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize ${ROLE_COLORS[r.role] ?? 'bg-slate-100 text-slate-600'}`}>{r.role}</span>
        )},
        { key: 'hire_date', header: 'Date d\'entrée', render: (r: PendingEmployee) => <span className="text-slate-500 text-sm">{fmtDate(r.hire_date)}</span> },
        { key: 'account_creation_date', header: 'Création compte', render: (r: PendingEmployee) => (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
            <Clock size={10} /> {fmtDate(r.account_creation_date)}
          </span>
        )},
        { key: 'actions', header: '', width: '120px', render: (r: PendingEmployee) => (
          <div className="flex items-center gap-1">
            <button onClick={() => activate.mutate(r.id)} disabled={activate.isPending}
              className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium bg-emerald-100 text-emerald-700 hover:bg-emerald-200 disabled:opacity-50 transition-colors"
              title="Forcer la création">
              <UserCheck size={12} /> Forcer
            </button>
            <button 
              onClick={async () => {
                const result = await swalConfirm({
                  title: 'Confirmer',
                  text: 'Cette action est irréversible.',
                  icon: 'warning',
                  confirmButtonColor: '#DC2626',
                  confirmButtonText: 'Supprimer',
                  cancelButtonText: 'Annuler',
                })
                if (result.isConfirmed) {
                  remove.mutate(r.id)
                }
              }}
              disabled={remove.isPending}
              className="p-1.5 rounded-lg hover:bg-red-50 text-red-400 disabled:opacity-50 transition-colors"
              title="Annuler">
              <X size={13} />
            </button>
          </div>
        )},
      ]}
      data={pending}
    />
  )
}

// ── Main component ─────────────────────────────────────────────────────────

type Tab = 'active' | 'pending'

export default function AdminUsersPage() {
  const { t } = useTranslation()
  const currentUser = useAuthStore(s => s.user)
  const isAdmin = currentUser?.role === 'admin'
  const { startProxy: storeStartProxy } = useProxyStore()
  const queryClient = useQueryClient()

  const [tab, setTab] = useState<Tab>('active')
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [editEmployee, setEditEmployee] = useState<Employee | null>(null)
  const [detailEmployee, setDetailEmployee] = useState<Employee | null>(null)
  const [deactivateEmployee, setDeactivateEmployee] = useState<Employee | null>(null)
  const [mutationEmployee, setMutationEmployee] = useState<Employee | null>(null)
  const [isImporting, setIsImporting] = useState(false)
  const [fileInputRef, setFileInputRef] = useState<HTMLInputElement | null>(null)

  const { data: employees = [], isLoading, isError } = useEmployees()
  const { data: orgs = [] } = useOrganizations()
  const cancelDeactivation = useCancelScheduledDeactivation()

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return employees.filter(e =>
      fullName(e).toLowerCase().includes(q) ||
      e.email.toLowerCase().includes(q) ||
      e.role.toLowerCase().includes(q)
    )
  }, [employees, search])

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setIsImporting(true)
    try {
      const result = await importUsersCSV(file)
      await swalDark({
        icon: result.errors.length === 0 ? 'success' : 'warning',
        title: 'Import terminé',
        html: `<p>${result.message}</p>${result.errors.length > 0 ? `<ul class="text-left text-sm mt-2">${result.errors.slice(0, 5).map(err => `<li>• ${err}</li>`).join('')}</ul>` : ''}`,
      })
      queryClient.invalidateQueries({ queryKey: ['employees'] })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Import échoué'
      await swalDark({ icon: 'error', title: 'Erreur', text: message })
    } finally {
      setIsImporting(false)
      if (fileInputRef) fileInputRef.value = ''
    }
  }

  const handleProxy = async (emp: Employee) => {
    try {
      const res = await startProxy(emp.employee_id)
      storeStartProxy({ id: emp.employee_id, name: fullName(emp), email: emp.email }, res.log_id, res.token)
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Erreur lors du démarrage du proxy'
      await swalDark({
        icon: 'error',
        title: 'Erreur proxy',
        text: message,
        confirmButtonColor: '#4F46E5',
      })
    }
  }

  const toDetailShape = (e: Employee) => ({
    id: e.employee_id,
    name: fullName(e),
    username: e.username ?? '',
    email: e.email,
    role: e.role,
    status: e.employment_status,
    created: e.created_at ? new Date(e.created_at).toLocaleDateString('fr-FR') : '—',
    birthDate: e.birth_date ? new Date(e.birth_date).toLocaleDateString('fr-FR') : undefined,
    address: e.address ?? undefined,
    deactivationScheduledAt: e.deactivation_scheduled_at ?? undefined,
  })

  const columns = useMemo(() => [
    {
      key: 'first_name',
      header: 'Nom',
      render: (e: Employee) => (
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-800 dark:text-slate-200">{fullName(e)}</span>
          {e.deactivation_scheduled_at && (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-semibold bg-orange-100 text-orange-700">
              Désact. {new Date(e.deactivation_scheduled_at).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })}
            </span>
          )}
        </div>
      ),
    },
    { key: 'email', header: 'Email', render: (e: Employee) => <span className="text-slate-500">{e.email}</span> },
    {
      key: 'role', header: 'Rôle', width: '110px',
      render: (e: Employee) => (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize ${ROLE_COLORS[e.role] ?? 'bg-slate-100 text-slate-600'}`}>
          {e.role}
        </span>
      ),
    },
    {
      key: 'employment_status', header: 'Statut', width: '100px',
      render: (e: Employee) => (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${e.employment_status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
          {e.employment_status === 'active' ? 'Actif' : 'Inactif'}
        </span>
      ),
    },

    {
      key: 'actions', header: '', width: '120px', sortable: false,
      render: (e: Employee) => (
        <div className="flex items-center gap-1" onClick={ev => ev.stopPropagation()}>
          <button onClick={() => setEditEmployee(e)} aria-label="Modifier" className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-indigo-600" title="Modifier"><Pencil size={13} /></button>
          <button onClick={() => setMutationEmployee(e)} aria-label="Muter" className="p-1.5 rounded-lg hover:bg-purple-50 text-slate-400 hover:text-purple-600" title="Muter"><Clock size={13} /></button>
          {isAdmin && <button onClick={() => handleProxy(e)} aria-label="Proxy" className="p-1.5 rounded-lg hover:bg-amber-50 text-slate-400 hover:text-amber-600" title="Proxy"><Shield size={13} /></button>}
          {e.employment_status === 'active'
            ? <button onClick={() => setDeactivateEmployee(e)} aria-label="Désactiver" className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-600" title="Désactiver"><UserX size={13} /></button>
            : <button onClick={async () => { await cancelDeactivation.mutate(e.employee_id) }} aria-label="Réactiver" className="p-1.5 rounded-lg hover:bg-emerald-50 text-slate-400 hover:text-emerald-600" title="Réactiver"><UserCheckIcon size={13} /></button>
          }
        </div>
      ),
    },
  ], [isAdmin])


  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-white">{t('nav.users', 'Utilisateurs')}</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {employees.length} employé{employees.length !== 1 ? 's' : ''} actif{employees.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={(ref) => setFileInputRef(ref)}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleImport}
          />
          <div className="flex items-center gap-2 bg-white border border-slate-300 rounded-lg px-3 py-2 w-64">
            <Search size={14} className="text-slate-400" />
            <input type="text" placeholder={t('common.search', 'Rechercher')} value={search} onChange={e => setSearch(e.target.value)}
              className="bg-transparent text-sm text-slate-700 outline-none w-full placeholder-slate-400" />
            {search && <button onClick={() => setSearch('')} aria-label="Effacer la recherche" className="text-slate-400 hover:text-slate-600"><X size={13} /></button>}
          </div>
          {isAdmin && (
            <>
              <Button
                variant="secondary"
                icon={<Upload size={14} />}
                onClick={() => fileInputRef?.click()}
                disabled={isImporting}
              >
                {isImporting ? 'Import...' : 'CSV'}
              </Button>
              <Button icon={<Plus size={14} />} onClick={() => setCreateOpen(true)}>
                {t('users.add', 'Nouvel utilisateur')}
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200">
        {(['active', 'pending'] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}>
            {t === 'active' ? 'Employés actifs' : 'En attente'}
          </button>
        ))}
      </div>

      {/* Content */}
      {tab === 'active' ? (
        <Card padding={false}>
          {isLoading ? (
            <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
              <Loader2 size={16} className="animate-spin" /> Chargement…
            </div>
          ) : isError ? (
            <div className="flex items-center justify-center gap-2 py-16 text-red-500 text-sm">
              <AlertTriangle size={16} /> Impossible de charger les utilisateurs.
            </div>
          ) : (
          <PaginatedTable
              data={filtered}
              columns={columns}
              pageSize={25}
              onRowClick={(row: Employee) => setDetailEmployee(row)}
            />
          )}
        </Card>
      ) : (
        <Card padding={false}>
          <PendingTab />
        </Card>
      )}

      {/* Modals */}
      {createOpen && (
        <UserFormModal open onClose={() => setCreateOpen(false)} orgs={orgs} />
      )}
      {editEmployee && (
        <UserFormModal open onClose={() => setEditEmployee(null)} initial={editEmployee} orgs={orgs} />
      )}
      {detailEmployee && (
        <EmployeeDetailModal
          employee={toDetailShape(detailEmployee)}
          onClose={() => setDetailEmployee(null)}
          onEdit={() => { setDetailEmployee(null); setEditEmployee(detailEmployee) }}
          isAdmin={isAdmin}
        />
      )}
      <DeactivateModal employee={deactivateEmployee} onClose={() => setDeactivateEmployee(null)} />
      {mutationEmployee && (
        <MutationModal
          employeeId={mutationEmployee.employee_id}
          employeeName={fullName(mutationEmployee)}
          onClose={() => setMutationEmployee(null)}
        />
      )}
    </div>
  )
}

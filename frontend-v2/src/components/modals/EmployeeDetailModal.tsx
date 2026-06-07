import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Mail, Phone, MapPin, Calendar, Shield, Clock, TrendingUp,
  CheckSquare, ArrowRightLeft, History, Loader2, Building2,
} from 'lucide-react'
import Modal from '../ui/Modal'
import Avatar from '../ui/Avatar'
import { StatusBadge } from '../ui/Badge'
import EmployeeSkillsPanel from '../EmployeeSkillsPanel'
import MutationModal from '../MutationModal'
import { apiClient } from '../../lib/apiClient'
import { fetchOrganizations } from '../../features/organizations/api'

export interface Employee {
  id: number
  name: string
  username: string
  email: string
  role: string
  status: string
  created: string
  birthDate?: string
  address?: string
  phone?: string
  manager?: string
  hoursThisMonth?: number
  pendingApprovals?: number
  absenceDaysLeft?: number
  /** ISO date string — set when a deferred deactivation is scheduled (12c.2) */
  deactivationScheduledAt?: string
}

interface MutationLogEntry {
  id: number
  employee_id: number
  from_org_id: number
  to_org_id: number
  mutated_by: number
  mutated_at: string
  reason: string | null
}

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-purple-100 text-purple-700',
  manager: 'bg-blue-100 text-blue-700',
  finance: 'bg-amber-100 text-amber-700',
  employee: 'bg-slate-100 text-slate-600',
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString('fr-FR', {
      day: '2-digit', month: 'short', year: 'numeric',
    })
  } catch {
    return iso
  }
}

// ---------------------------------------------------------------------------
// Mutation history sub-section
// ---------------------------------------------------------------------------
function MutationHistory({ employeeId }: { employeeId: number }) {
  const { data: history = [], isLoading: loadingHistory } = useQuery({
    queryKey: ['mutation-history', employeeId],
    queryFn: () => apiClient.get<MutationLogEntry[]>(
      `/admin/employees/${employeeId}/mutation-history`,
    ),
    enabled: employeeId > 0,
  })

  const { data: orgs = [] } = useQuery({
    queryKey: ['organizations'],
    queryFn: fetchOrganizations,
  })

  const orgName = (id: number) =>
    orgs.find(o => o.org_id === id)?.org_name ?? `Org #${id}`

  if (loadingHistory) {
    return (
      <div className="flex items-center gap-2 text-slate-400 text-xs py-2">
        <Loader2 size={12} className="animate-spin" />
        Chargement de l'historique…
      </div>
    )
  }

  if (history.length === 0) {
    return (
      <p className="text-xs text-slate-400 italic">Aucune mutation enregistrée.</p>
    )
  }

  return (
    <ol className="space-y-3">
      {history.map(entry => (
        <li key={entry.id} className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
          <div className="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-0.5">
            <ArrowRightLeft size={13} className="text-indigo-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg px-2 py-0.5">
                <Building2 size={10} className="text-slate-400" />
                {orgName(entry.from_org_id)}
              </span>
              <ArrowRightLeft size={11} className="text-slate-400 flex-shrink-0" />
              <span className="inline-flex items-center gap-1 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg px-2 py-0.5">
                <Building2 size={10} className="text-indigo-400" />
                {orgName(entry.to_org_id)}
              </span>
            </div>
            {entry.reason && (
              <p className="text-xs text-slate-500 mt-1.5 italic">"{entry.reason}"</p>
            )}
            <p className="text-xs text-slate-400 mt-1">{formatDate(entry.mutated_at)}</p>
          </div>
        </li>
      ))}
    </ol>
  )
}

// ---------------------------------------------------------------------------
// Main modal
// ---------------------------------------------------------------------------
interface Props {
  employee: Employee | null
  onClose: () => void
  onEdit?: (e: Employee) => void
  /** Pass true when the current user is an admin to show the Muter button */
  isAdmin?: boolean
}

export default function EmployeeDetailModal({
  employee,
  onClose,
  onEdit,
  isAdmin = false,
}: Props) {
  const [mutationModalOpen, setMutationModalOpen] = useState(false)

  if (!employee) return null

  return (
    <>
      <Modal open={!!employee} onClose={onClose} title="Fiche employé" size="lg">
        <div className="space-y-5">
          {/* Header */}
          <div className="flex items-start gap-4 pb-4 border-b border-slate-100">
            <Avatar name={employee.name} size="xl" status="online" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-xl font-bold text-slate-800">{employee.name}</h2>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${ROLE_COLORS[employee.role]}`}
                >
                  {employee.role}
                </span>
                <StatusBadge status={employee.status} />
              </div>
              <p className="text-sm text-slate-400 mt-0.5">@{employee.username}</p>
              {employee.manager && (
                <p className="text-xs text-slate-400 mt-1">
                  Manager :{' '}
                  <span className="text-slate-600 font-medium">{employee.manager}</span>
                </p>
              )}
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {isAdmin && (
                <button
                  onClick={() => setMutationModalOpen(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-amber-700 border border-amber-200 bg-amber-50 rounded-lg hover:bg-amber-100 transition-colors"
                  title="Muter vers une autre organisation"
                >
                  <ArrowRightLeft size={13} />
                  Muter
                </button>
              )}
              {onEdit && (
                <button
                  onClick={() => onEdit(employee)}
                  className="px-3 py-1.5 text-sm font-medium text-indigo-600 border border-indigo-200 rounded-lg hover:bg-indigo-50 transition-colors"
                >
                  Modifier
                </button>
              )}
            </div>
          </div>

          {/* KPI row */}
          <div className="grid grid-cols-3 gap-3">
            {[
              {
                icon: <Clock size={16} className="text-indigo-500" />,
                label: 'Heures ce mois',
                value: `${employee.hoursThisMonth ?? 0}h`,
                bg: 'bg-indigo-50',
              },
              {
                icon: <CheckSquare size={16} className="text-amber-500" />,
                label: 'Validations en attente',
                value: employee.pendingApprovals ?? 0,
                bg: 'bg-amber-50',
              },
              {
                icon: <TrendingUp size={16} className="text-emerald-500" />,
                label: 'Congés restants',
                value: `${employee.absenceDaysLeft ?? 0}j`,
                bg: 'bg-emerald-50',
              },
            ].map(kpi => (
              <div key={kpi.label} className={`${kpi.bg} rounded-xl p-3`}>
                <div className="flex items-center gap-2 mb-1">
                  {kpi.icon}
                  <span className="text-xs text-slate-500">{kpi.label}</span>
                </div>
                <p className="text-xl font-bold text-slate-800">{kpi.value}</p>
              </div>
            ))}
          </div>

          {/* Info grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
              <Mail size={15} className="text-slate-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs text-slate-400 mb-0.5">Email</p>
                <p className="text-sm font-medium text-slate-700">{employee.email}</p>
              </div>
            </div>
            {employee.phone && (
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
                <Phone size={15} className="text-slate-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs text-slate-400 mb-0.5">Téléphone</p>
                  <p className="text-sm font-medium text-slate-700">{employee.phone}</p>
                </div>
              </div>
            )}
            {employee.birthDate && (
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
                <Calendar size={15} className="text-slate-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs text-slate-400 mb-0.5">Date de naissance</p>
                  <p className="text-sm font-medium text-slate-700">{employee.birthDate}</p>
                </div>
              </div>
            )}
            {employee.address && (
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
                <MapPin size={15} className="text-slate-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs text-slate-400 mb-0.5">Adresse</p>
                  <p className="text-sm font-medium text-slate-700">{employee.address}</p>
                </div>
              </div>
            )}
            <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
              <Shield size={15} className="text-slate-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs text-slate-400 mb-0.5">Membre depuis</p>
                <p className="text-sm font-medium text-slate-700">{employee.created}</p>
              </div>
            </div>
          </div>

          {/* Skills section */}
          <div className="border border-slate-100 rounded-xl p-4">
            <EmployeeSkillsPanel employeeId={employee.id} />
          </div>

          {/* Mutation history — visible to admins */}
          {isAdmin && (
            <div className="border border-slate-100 rounded-xl p-4 space-y-3">
              <div className="flex items-center gap-2">
                <History size={14} className="text-slate-400" />
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  Historique des mutations
                </h3>
              </div>
              <MutationHistory employeeId={employee.id} />
            </div>
          )}
        </div>
      </Modal>

      {/* Mutation modal — rendered outside the detail modal to avoid z-index stacking */}
      {mutationModalOpen && (
        <MutationModal
          employeeId={employee.id}
          employeeName={employee.name}
          onClose={() => setMutationModalOpen(false)}
        />
      )}
    </>
  )
}

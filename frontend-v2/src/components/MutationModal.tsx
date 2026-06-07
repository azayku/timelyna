import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowRightLeft, AlertTriangle, Loader2, Building2 } from 'lucide-react'
import Modal from './ui/Modal'
import Button from './ui/Button'
import { apiClient, ApiError } from '../lib/apiClient'
import { fetchOrganizations } from '../features/organizations/api'

interface MutatePayload {
  target_org_id: number
  reason?: string
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

function muteEmployee(employeeId: number, payload: MutatePayload): Promise<MutationLogEntry> {
  return apiClient.post<MutationLogEntry>(`/admin/employees/${employeeId}/mutate`, payload)
}

const ERROR_MESSAGES: Record<string, string> = {
  employee_is_org_manager:
    'Cet employé est manager d\'une organisation. Réassignez d\'abord le management avant de le muter.',
  invalid_target_organization:
    'L\'organisation cible est invalide ou a été désactivée.',
}

interface Props {
  employeeId: number
  employeeName: string
  onClose: () => void
}

export default function MutationModal({ employeeId, employeeName, onClose }: Props) {
  const [targetOrgId, setTargetOrgId] = useState<number | ''>('')
  const [reason, setReason] = useState('')
  const [apiError, setApiError] = useState<string | null>(null)

  const { data: orgs = [], isLoading: loadingOrgs } = useQuery({
    queryKey: ['organizations'],
    queryFn: fetchOrganizations,
  })

  const mutation = useMutation({
    mutationFn: (payload: MutatePayload) => muteEmployee(employeeId, payload),
    onSuccess: () => {
      onClose()
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        setApiError(ERROR_MESSAGES[err.code] ?? err.message)
      } else {
        setApiError('Une erreur inattendue est survenue.')
      }
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (targetOrgId === '') return
    setApiError(null)
    mutation.mutate({
      target_org_id: Number(targetOrgId),
      reason: reason.trim() || undefined,
    })
  }

  const remainingChars = 500 - reason.length

  return (
    <Modal open onClose={onClose} title="Muter un employé" size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Info banner */}
        <div className="flex items-start gap-3 p-3 bg-indigo-50 border border-indigo-100 rounded-xl">
          <ArrowRightLeft size={15} className="text-indigo-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-indigo-800">
            <p className="font-semibold mb-0.5">Mutation d'organisation</p>
            <p>
              <strong>{employeeName}</strong> sera transféré(e) vers l'organisation
              sélectionnée. Son manager sera automatiquement mis à jour.
            </p>
          </div>
        </div>

        {/* Target org selector */}
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1.5">
            Organisation cible *
          </label>
          {loadingOrgs ? (
            <div className="flex items-center gap-2 text-slate-400 text-xs py-2">
              <Loader2 size={13} className="animate-spin" />
              Chargement des organisations…
            </div>
          ) : (
            <select
              value={targetOrgId}
              onChange={e =>
                setTargetOrgId(e.target.value === '' ? '' : Number(e.target.value))
              }
              required
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">— Choisir une organisation —</option>
              {orgs.map(org => (
                <option key={org.org_id} value={org.org_id}>
                  {org.org_name} ({org.employee_count} employé
                  {org.employee_count !== 1 ? 's' : ''})
                </option>
              ))}
            </select>
          )}
          {targetOrgId !== '' && (
            <div className="flex items-center gap-1.5 mt-1.5 text-xs text-slate-500">
              <Building2 size={11} />
              {orgs.find(o => o.org_id === targetOrgId)?.org_name}
            </div>
          )}
        </div>

        {/* Reason */}
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1.5">
            Motif{' '}
            <span className="font-normal text-slate-400">(optionnel)</span>
          </label>
          <textarea
            value={reason}
            onChange={e => setReason(e.target.value.slice(0, 500))}
            rows={3}
            placeholder="Ex: Réorganisation d'équipe, renfort sur un projet…"
            className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <p
            className={`text-right text-[11px] mt-0.5 ${
              remainingChars < 50 ? 'text-amber-500' : 'text-slate-400'
            }`}
          >
            {remainingChars} caractère{remainingChars !== 1 ? 's' : ''} restant
            {remainingChars !== 1 ? 's' : ''}
          </p>
        </div>

        {/* API error */}
        {apiError && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertTriangle size={15} className="flex-shrink-0 mt-0.5" />
            {apiError}
          </div>
        )}

        <div className="flex gap-3 justify-end pt-2">
          <Button variant="secondary" type="button" onClick={onClose}>
            Annuler
          </Button>
          <Button
            type="submit"
            loading={mutation.isPending}
            disabled={targetOrgId === ''}
            icon={<ArrowRightLeft size={14} />}
          >
            Confirmer la mutation
          </Button>
        </div>
      </form>
    </Modal>
  )
}

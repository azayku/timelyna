import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, AlertTriangle, Loader2, Check, Calendar, Save } from 'lucide-react'
import Modal from '../ui/Modal'
import Avatar from '../ui/Avatar'
import Button from '../ui/Button'
import { apiClient } from '../../lib/apiClient'

// ── Types ──────────────────────────────────────────────────────────────────

interface Employee {
  id: number
  first_name: string
  last_name: string
  role: string
  email: string
}

interface EmployeeAvailability {
  employee_id: number
  full_name: string
  role: string
  logged_hours: number
  max_hours: number
  occupation_pct: number
  has_absence: boolean
  conflicting_projects: string[]
}

interface SkillRate {
  id: number
  skill_name: string
  billing_rate: string
  description?: string | null
}

interface Props {
  open: boolean
  projectId: number
  projectName: string
  startDate?: string
  endDate?: string
  onClose: () => void
  onSave: (teamMemberIds: number[]) => void
}

// ── Helpers ────────────────────────────────────────────────────────────────

function occupationBarColor(pct: number): string {
  if (pct > 90) return 'bg-red-500'
  if (pct >= 70) return 'bg-orange-500'
  return 'bg-emerald-500'
}

function occupationTextColor(pct: number): string {
  if (pct > 90) return 'text-red-600'
  if (pct >= 70) return 'text-orange-500'
  return 'text-emerald-600'
}

function occupationBgColor(pct: number): string {
  if (pct > 90) return 'bg-red-50'
  if (pct >= 70) return 'bg-orange-50'
  return 'bg-emerald-50'
}

// ── Component ──────────────────────────────────────────────────────────────

export default function TeamAssignmentModal({
  open,
  projectId,
  projectName,
  startDate,
  endDate,
  onClose,
  onSave,
}: Props) {
  const queryClient = useQueryClient()

  // Selected employee IDs
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  // Per-employee skill selection: employeeId → skillRateId
  const [skillSelections, setSkillSelections] = useState<Record<number, number>>({})

  // ── Queries ────────────────────────────────────────────────────────────

  const { data: employees = [], isLoading: loadingEmployees } = useQuery<Employee[]>({
    queryKey: ['employees'],
    queryFn: () => apiClient.get<{ items: Employee[] }>('/admin/employees?page_size=2000').then(data => data.items),
    enabled: open,
    staleTime: 5 * 60 * 1000,
  })

  const availabilityParams = useMemo(() => {
    const params = new URLSearchParams()
    if (startDate) params.set('start_date', startDate)
    if (endDate) params.set('end_date', endDate)
    return params.toString()
  }, [startDate, endDate])

  const { data: availability = [], isLoading: loadingAvailability } = useQuery<EmployeeAvailability[]>({
    queryKey: ['team-availability', projectId, startDate, endDate],
    queryFn: () =>
      apiClient.get<EmployeeAvailability[]>(
        `/admin/projects/${projectId}/team-availability${availabilityParams ? `?${availabilityParams}` : ''}`,
      ),
    enabled: open && projectId > 0,
    staleTime: 2 * 60 * 1000,
  })

  const { data: skillRates = [], isLoading: loadingSkills } = useQuery<SkillRate[]>({
    queryKey: ['skill-rates'],
    queryFn: () => apiClient.get<SkillRate[]>('/admin/skill-rates'),
    enabled: open,
    staleTime: 5 * 60 * 1000,
  })

  // ── Mutation: save team ────────────────────────────────────────────────

  const saveMutation = useMutation({
    mutationFn: (memberIds: number[]) =>
      apiClient.put(`/admin/projects/${projectId}/team`, { member_ids: memberIds }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['team-availability', projectId] })
      onSave(Array.from(selectedIds))
      handleClose()
    },
  })

  // ── Helpers ────────────────────────────────────────────────────────────

  const isLoading = loadingEmployees || loadingAvailability || loadingSkills

  // Build a lookup map: employee_id → availability data
  const availabilityMap = useMemo(() => {
    const map = new Map<number, EmployeeAvailability>()
    for (const a of availability) map.set(a.employee_id, a)
    return map
  }, [availability])

  const toggleEmployee = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
        setSkillSelections(s => {
          const copy = { ...s }
          delete copy[id]
          return copy
        })
      } else {
        next.add(id)
      }
      return next
    })
  }

  const setSkillForEmployee = (employeeId: number, skillRateId: number) => {
    setSkillSelections(prev => ({ ...prev, [employeeId]: skillRateId }))
  }

  const handleSave = () => {
    saveMutation.mutate(Array.from(selectedIds))
  }

  const handleClose = () => {
    setSelectedIds(new Set())
    setSkillSelections({})
    saveMutation.reset()
    onClose()
  }

  // ── Render ─────────────────────────────────────────────────────────────

  return (
    <Modal open={open} onClose={handleClose} title={`Gérer l'équipe — ${projectName}`} size="xl">
      <div className="space-y-4">

        {/* Period info */}
        {(startDate || endDate) && (
          <div className="flex items-center gap-2 px-3 py-2 bg-indigo-50 border border-indigo-100 rounded-xl text-xs text-indigo-700">
            <Calendar size={13} className="flex-shrink-0" />
            <span>
              Disponibilité analysée sur la période :{' '}
              <strong>{startDate ?? '—'}</strong>
              {' → '}
              <strong>{endDate ?? '—'}</strong>
            </span>
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center gap-2 py-12 text-slate-400 text-sm">
            <Loader2 size={16} className="animate-spin" />
            Chargement des disponibilités…
          </div>
        )}

        {/* Employee list */}
        {!isLoading && employees.length === 0 && (
          <div className="flex flex-col items-center gap-2 py-10 text-center">
            <Users size={24} className="text-slate-300" />
            <p className="text-sm text-slate-400">Aucun employé disponible.</p>
          </div>
        )}

        {!isLoading && employees.length > 0 && (
          <div className="space-y-2 max-h-[52vh] overflow-y-auto pr-1">
            {/* Selection summary */}
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Employés — {employees.length} au total
              </p>
              {selectedIds.size > 0 && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700">
                  <Users size={11} />
                  {selectedIds.size} sélectionné{selectedIds.size > 1 ? 's' : ''}
                </span>
              )}
            </div>

            {employees.map(emp => {
              const avail = availabilityMap.get(emp.id)
              const pct = avail?.occupation_pct ?? 0
              const isSelected = selectedIds.has(emp.id)
              const fullName = `${emp.first_name} ${emp.last_name}`
              const displayName = avail?.full_name ?? fullName
              const displayRole = avail?.role ?? emp.role
              const showWarning = pct > 80

              return (
                <div
                  key={emp.id}
                  className={`flex items-start gap-3 p-3 rounded-xl border-2 transition-all ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  {/* Checkbox */}
                  <button
                    onClick={() => toggleEmployee(emp.id)}
                    className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors ${
                      isSelected
                        ? 'border-indigo-500 bg-indigo-500'
                        : 'border-slate-300 hover:border-indigo-400'
                    }`}
                    aria-label={isSelected ? `Désélectionner ${displayName}` : `Sélectionner ${displayName}`}
                  >
                    {isSelected && <Check size={11} className="text-white" />}
                  </button>

                  {/* Avatar */}
                  <Avatar name={displayName} size="sm" />

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    {/* Name + role + warning */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-slate-800">{displayName}</span>
                      <span className="text-xs text-slate-400 capitalize">{displayRole}</span>
                      {showWarning && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-medium text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full">
                          <AlertTriangle size={10} />
                          Occupation élevée
                        </span>
                      )}
                    </div>

                    {/* Occupation bar */}
                    {avail && (
                      <div className="mt-2">
                        <div className="flex items-center justify-between text-[10px] mb-1">
                          <span className="text-slate-400">
                            Occupation : {avail.logged_hours}h / {avail.max_hours}h
                          </span>
                          <span
                            className={`font-bold px-1.5 py-0.5 rounded ${occupationTextColor(pct)} ${occupationBgColor(pct)}`}
                          >
                            {pct}%
                          </span>
                        </div>
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${occupationBarColor(pct)}`}
                            style={{ width: `${Math.min(pct, 100)}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Conflicts */}
                    {avail && avail.conflicting_projects.length > 0 && (
                      <div className="flex items-center gap-1 mt-1.5 text-[10px] text-slate-500">
                        <AlertTriangle size={10} className="text-orange-400 flex-shrink-0" />
                        <span>
                          Déjà sur :{' '}
                          <span className="font-medium">{avail.conflicting_projects.join(', ')}</span>
                        </span>
                      </div>
                    )}

                    {/* Absence indicator */}
                    {avail?.has_absence && (
                      <div className="flex items-center gap-1 mt-1 text-[10px] text-red-500">
                        <AlertTriangle size={10} className="flex-shrink-0" />
                        Absence prévue sur cette période
                      </div>
                    )}

                    {/* Skill selector — only when selected */}
                    {isSelected && (
                      <div className="mt-2.5">
                        <label className="block text-[10px] font-semibold text-slate-500 mb-1">
                          Compétence pour ce projet
                        </label>
                        {loadingSkills ? (
                          <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
                            <Loader2 size={10} className="animate-spin" />
                            Chargement…
                          </div>
                        ) : (
                          <select
                            value={skillSelections[emp.id] ?? ''}
                            onChange={e =>
                              setSkillForEmployee(emp.id, Number(e.target.value))
                            }
                            onClick={e => e.stopPropagation()}
                            className="w-full border border-indigo-300 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                          >
                            <option value="">— Choisir une compétence —</option>
                            {skillRates.map(sr => (
                              <option key={sr.id} value={sr.id}>
                                {sr.skill_name}
                                {sr.billing_rate ? ` — ${sr.billing_rate} €/h` : ''}
                              </option>
                            ))}
                          </select>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* API error */}
        {saveMutation.isError && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
            <AlertTriangle size={14} className="flex-shrink-0" />
            Erreur lors de l'enregistrement de l'équipe. Veuillez réessayer.
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-100">
          <button
            onClick={handleClose}
            disabled={saveMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50"
          >
            Annuler
          </button>

          <Button
            onClick={handleSave}
            disabled={saveMutation.isPending || selectedIds.size === 0}
            icon={
              saveMutation.isPending
                ? <Loader2 size={14} className="animate-spin" />
                : <Save size={14} />
            }
          >
            {saveMutation.isPending
              ? 'Enregistrement…'
              : `Enregistrer l'équipe${selectedIds.size > 0 ? ` (${selectedIds.size})` : ''}`}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

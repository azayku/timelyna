import { useState, useMemo } from 'react'
import { Plus, Check, AlertTriangle, Users, Star, Calendar, ChevronRight, Loader2 } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Modal from '../ui/Modal'
import Avatar from '../ui/Avatar'
import Button from '../ui/Button'
import { apiClient } from '../../lib/apiClient'
import { suggestEmployees, type SuggestedEmployee } from '../../data/mockData'
import { useClients } from '../../features/clients/hooks'

// ── Types ──────────────────────────────────────────────────────────────────

interface SkillRate {
  id: number
  skill_name: string
  billing_rate: string
  description?: string | null
}

interface RequiredSkill {
  skill_rate_id: number
  quantity: number
}

interface Props {
  open: boolean
  onClose: () => void
}

const STEPS = ['Informations', 'Compétences', 'Équipe suggérée'] as const
type Step = 0 | 1 | 2

const STATUSES = [
  { value: 'draft', label: 'Brouillon' },
  { value: 'planning', label: 'Planification' },
  { value: 'active', label: 'Actif' },
]

// Stable badge colors cycling by skill name hash (same palette as EmployeeSuggestionsPanel)
const SKILL_COLORS = [
  'bg-blue-100 text-blue-700',
  'bg-green-100 text-green-700',
  'bg-yellow-100 text-yellow-700',
  'bg-pink-100 text-pink-700',
  'bg-orange-100 text-orange-700',
  'bg-purple-100 text-purple-700',
  'bg-indigo-100 text-indigo-700',
  'bg-red-100 text-red-700',
]

function colorForSkill(name: string) {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0
  return SKILL_COLORS[hash % SKILL_COLORS.length]
}

// ── Component ──────────────────────────────────────────────────────────────

export default function CreateProjectModal({ open, onClose }: Props) {
  const queryClient = useQueryClient()
  const [step, setStep] = useState<Step>(0)

  // Step 0 — project info
  const [name, setName] = useState('')
  const [clientId, setClientId] = useState('')
  const [managerId, setManagerId] = useState('')
  const [status, setStatus] = useState('planning')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [budget, setBudget] = useState('')
  const [rate, setRate] = useState('')

  // Step 1 — required skills (skill_rate_id → quantity)
  const [requiredSkills, setRequiredSkills] = useState<RequiredSkill[]>([])

  // Step 2 — selected team (mock suggestions, kept for UX)
  const [selectedTeam, setSelectedTeam] = useState<number[]>([])

  // ── API: fetch skill rates ──────────────────────────────────────────────
  const { data: skillRates = [], isLoading: loadingSkills } = useQuery<SkillRate[]>({
    queryKey: ['skill-rates'],
    queryFn: () => apiClient.get<SkillRate[]>('/admin/skill-rates'),
    enabled: open,
    staleTime: 5 * 60 * 1000,
  })

  // ── API: fetch clients ──────────────────────────────────────────────────
  const { data: clients = [] } = useClients()

  // ── API: fetch employees (for manager selection) ────────────────────────
  const { data: employees = [], isLoading: loadingEmployees } = useQuery<{ employee_id: number; first_name: string; last_name: string; role: string }[]>({
    queryKey: ['employees'],
    queryFn: () => apiClient.get<{ employee_id: number; first_name: string; last_name: string; role: string }[]>('/admin/employees'),
    enabled: open,
    staleTime: 5 * 60 * 1000,
  })

  const managers = useMemo(() => 
    employees.filter(e => e.role === 'manager' || e.role === 'admin'),
    [employees]
  )

  // ── API: create project with skills ────────────────────────────────────
  const createMutation = useMutation({
    mutationFn: (payload: object) =>
      apiClient.post('/admin/projects/with-skills', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  // ── Mock suggestions (step 2) ──────────────────────────────────────────
  // We keep mock suggestions for the team-picker UX; real suggestions are
  // shown in ProjectDetailModal via EmployeeSuggestionsPanel once the project
  // is created and has a real ID.
  const mockSkillIds = useMemo(
    () => requiredSkills.map(rs => rs.skill_rate_id),
    [requiredSkills],
  )

  const suggestions = useMemo<SuggestedEmployee[]>(() => {
    if (step < 2 || requiredSkills.length === 0 || !startDate || !endDate) return []
    // Map skill_rate_ids to mock skill ids for the mock suggestion engine
    return suggestEmployees(mockSkillIds, startDate, endDate)
  }, [step, requiredSkills, startDate, endDate, mockSkillIds])

  // ── Helpers ────────────────────────────────────────────────────────────

  const isSkillSelected = (id: number) => requiredSkills.some(rs => rs.skill_rate_id === id)

  const toggleSkill = (id: number) => {
    setRequiredSkills(prev =>
      prev.some(rs => rs.skill_rate_id === id)
        ? prev.filter(rs => rs.skill_rate_id !== id)
        : [...prev, { skill_rate_id: id, quantity: 1 }],
    )
  }

  const setQuantity = (id: number, qty: number) => {
    setRequiredSkills(prev =>
      prev.map(rs => rs.skill_rate_id === id ? { ...rs, quantity: Math.max(1, qty) } : rs),
    )
  }

  const toggleTeam = (id: number) =>
    setSelectedTeam(prev => prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id])

  const canNext = () => {
    if (step === 0) return name.trim() && clientId && managerId && startDate && endDate
    if (step === 1) return requiredSkills.length > 0
    return true
  }

  const handleNext = () => {
    if (step < 2) setStep((step + 1) as Step)
  }

  const handleCreate = async () => {
    try {
      await createMutation.mutateAsync({
        project_name: name.trim(),
        client_id: Number(clientId),
        status,
        start_date: startDate,
        end_date: endDate || null,
        budget_hours: budget ? Number(budget) : null,
        billing_rate: Number(rate) || 0,
        manager_id: Number(managerId),
        required_skills: requiredSkills,
      })
      handleClose()
    } catch {
      // Error is accessible via createMutation.error if needed
    }
  }

  const handleClose = () => {
    onClose()
    setStep(0)
    setName(''); setClientId(''); setManagerId(''); setStartDate(''); setEndDate('')
    setBudget(''); setRate(''); setRequiredSkills([]); setSelectedTeam([])
    createMutation.reset()
  }

  const occupationColor = (pct: number) => {
    if (pct >= 90) return 'text-red-600 bg-red-50'
    if (pct >= 70) return 'text-amber-600 bg-amber-50'
    return 'text-emerald-600 bg-emerald-50'
  }

  const occupationBar = (pct: number) => {
    if (pct >= 90) return 'bg-red-500'
    if (pct >= 70) return 'bg-amber-500'
    return 'bg-emerald-500'
  }

  // ── Render ─────────────────────────────────────────────────────────────

  return (
    <Modal open={open} onClose={handleClose} title="Nouveau projet" size="xl">
      {/* Stepper */}
      <div className="flex items-center gap-0 mb-6 -mt-1">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center flex-1">
            <div className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                i < step ? 'bg-indigo-600 text-white' :
                i === step ? 'bg-indigo-600 text-white ring-4 ring-indigo-100' :
                'bg-slate-200 text-slate-500'
              }`}>
                {i < step ? <Check size={13} /> : i + 1}
              </div>
              <span className={`text-xs font-medium hidden sm:block ${i === step ? 'text-indigo-700' : i < step ? 'text-slate-600' : 'text-slate-400'}`}>
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 mx-3 ${i < step ? 'bg-indigo-600' : 'bg-slate-200'}`} />
            )}
          </div>
        ))}
      </div>

      {/* ── Step 0: Informations ── */}
      {step === 0 && (
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Nom du projet *</label>
            <input value={name} onChange={e => setName(e.target.value)}
              placeholder="Ex: Refonte site web"
              className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Client *</label>
              {loadingEmployees ? (
                <div className="flex items-center gap-2 text-slate-400 text-xs py-2">
                  <Loader2 size={12} className="animate-spin" /> Chargement…
                </div>
              ) : (
                <select value={clientId} onChange={e => setClientId(e.target.value)}
                  className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                  <option value="">— Choisir —</option>
                  {clients.map(c => <option key={c.client_id} value={c.client_id}>{c.client_name}</option>)}
                </select>
              )}
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Manager *</label>
              {loadingEmployees ? (
                <div className="flex items-center gap-2 text-slate-400 text-xs py-2">
                  <Loader2 size={12} className="animate-spin" /> Chargement…
                </div>
              ) : (
                <select value={managerId} onChange={e => setManagerId(e.target.value)}
                  className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                  <option value="">— Choisir —</option>
                  {managers.map(m => <option key={m.employee_id} value={m.employee_id}>{m.first_name} {m.last_name}</option>)}
                </select>
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Statut</label>
              <select value={status} onChange={e => setStatus(e.target.value)}
                className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                {STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </div>
            <div />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Date de début *</label>
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Date de fin *</label>
              <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} min={startDate}
                className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Budget (heures)</label>
              <input type="number" value={budget} onChange={e => setBudget(e.target.value)} placeholder="Ex: 500"
                className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">Taux horaire (€)</label>
              <input type="number" value={rate} onChange={e => setRate(e.target.value)} placeholder="Ex: 120"
                className="w-full border border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
          </div>
        </div>
      )}

      {/* ── Step 1: Compétences requises ── */}
      {step === 1 && (
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-3 bg-indigo-50 border border-indigo-100 rounded-xl">
            <Star size={16} className="text-indigo-500 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-indigo-700">
              Sélectionnez les compétences requises pour ce projet. Le système proposera ensuite les employés disponibles qui correspondent.
            </p>
          </div>

          {loadingSkills ? (
            <div className="flex items-center justify-center gap-2 py-8 text-slate-400 text-sm">
              <Loader2 size={16} className="animate-spin" />
              Chargement des compétences…
            </div>
          ) : skillRates.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              Aucune compétence disponible. Créez des skill rates dans les paramètres.
            </div>
          ) : (
            <div>
              <p className="text-xs font-semibold text-slate-500 mb-3">
                Compétences disponibles — {requiredSkills.length} sélectionnée{requiredSkills.length > 1 ? 's' : ''}
              </p>
              <div className="grid grid-cols-2 gap-2">
                {skillRates.map(skill => {
                  const selected = isSkillSelected(skill.id)
                  const rs = requiredSkills.find(r => r.skill_rate_id === skill.id)
                  return (
                    <div
                      key={skill.id}
                      className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl border-2 text-sm font-medium transition-all ${
                        selected
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-slate-200 bg-white hover:border-slate-300'
                      }`}
                    >
                      {/* Toggle checkbox */}
                      <button
                        onClick={() => toggleSkill(skill.id)}
                        className="flex items-center gap-2 flex-1 text-left"
                      >
                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                          selected ? 'border-indigo-500 bg-indigo-500' : 'border-slate-300'
                        }`}>
                          {selected && <Check size={11} className="text-white" />}
                        </div>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colorForSkill(skill.skill_name)}`}>
                          {skill.skill_name}
                        </span>
                      </button>

                      {/* Quantity input when selected */}
                      {selected && rs && (
                        <input
                          type="number"
                          min={1}
                          value={rs.quantity}
                          onChange={e => setQuantity(skill.id, Number(e.target.value))}
                          onClick={e => e.stopPropagation()}
                          className="w-12 border border-indigo-300 rounded px-1.5 py-0.5 text-xs text-center focus:outline-none focus:ring-1 focus:ring-indigo-500"
                          title="Quantité requise"
                        />
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {requiredSkills.length === 0 && !loadingSkills && skillRates.length > 0 && (
            <p className="text-xs text-amber-600 flex items-center gap-1.5">
              <AlertTriangle size={13} /> Sélectionnez au moins une compétence pour continuer
            </p>
          )}
        </div>
      )}

      {/* ── Step 2: Équipe suggérée (mock) ── */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-3 bg-emerald-50 border border-emerald-100 rounded-xl">
            <Users size={16} className="text-emerald-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-emerald-800">
                {suggestions.filter(s => s.available).length} employé{suggestions.filter(s => s.available).length > 1 ? 's' : ''} disponible{suggestions.filter(s => s.available).length > 1 ? 's' : ''} sur {suggestions.length} correspondant{suggestions.length > 1 ? 's' : ''}
              </p>
              <p className="text-xs text-emerald-600 mt-0.5">
                Triés par compétences correspondantes · Absences et projets actifs pris en compte
              </p>
            </div>
          </div>

          {/* Period reminder */}
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Calendar size={13} />
            <span>Période analysée : <strong>{startDate}</strong> → <strong>{endDate}</strong></span>
          </div>

          {/* Suggestions list */}
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {suggestions.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-sm">
                Aucun employé avec ces compétences trouvé
              </div>
            ) : (
              suggestions.map(({ employee, matchingSkills, matchCount, available, unavailableReason, occupation }) => {
                const isSelected = selectedTeam.includes(employee.id)
                return (
                  <div
                    key={employee.id}
                    onClick={() => available && toggleTeam(employee.id)}
                    className={`flex items-start gap-3 p-3 rounded-xl border-2 transition-all ${
                      !available ? 'opacity-60 cursor-not-allowed border-slate-100 bg-slate-50' :
                      isSelected ? 'border-indigo-500 bg-indigo-50 cursor-pointer' :
                      'border-slate-200 bg-white hover:border-slate-300 cursor-pointer'
                    }`}
                  >
                    {/* Checkbox */}
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-0.5 ${
                      isSelected ? 'border-indigo-500 bg-indigo-500' :
                      !available ? 'border-slate-300 bg-slate-100' :
                      'border-slate-300'
                    }`}>
                      {isSelected && <Check size={11} className="text-white" />}
                    </div>

                    {/* Avatar */}
                    <Avatar name={employee.name} size="sm" />

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-semibold text-slate-800">{employee.name}</span>
                        <span className="text-xs text-slate-400 capitalize">{employee.role}</span>
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700">
                          <Star size={9} /> {matchCount}/{requiredSkills.length}
                        </span>
                      </div>

                      {/* Matching skill names */}
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {matchingSkills.map(sid => {
                          const sr = skillRates.find(r => r.id === sid)
                          const label = sr?.skill_name ?? `Skill #${sid}`
                          return (
                            <span key={sid} className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${colorForSkill(label)}`}>
                              {label}
                            </span>
                          )
                        })}
                      </div>

                      {/* Occupation bar */}
                      <div className="mt-2">
                        <div className="flex justify-between text-[10px] mb-0.5">
                          <span className="text-slate-400">Occupation actuelle</span>
                          <span className={`font-bold px-1 rounded ${occupationColor(occupation)}`}>{occupation}%</span>
                        </div>
                        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div className={`h-full ${occupationBar(occupation)} rounded-full`} style={{ width: `${occupation}%` }} />
                        </div>
                      </div>

                      {unavailableReason && (
                        <div className="flex items-center gap-1 mt-1.5 text-[10px] text-amber-600">
                          <AlertTriangle size={10} />
                          {unavailableReason}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>

          {selectedTeam.length > 0 && (
            <div className="flex items-center gap-2 p-2.5 bg-indigo-50 rounded-lg">
              <Users size={14} className="text-indigo-600" />
              <span className="text-sm text-indigo-700 font-medium">
                {selectedTeam.length} membre{selectedTeam.length > 1 ? 's' : ''} sélectionné{selectedTeam.length > 1 ? 's' : ''}
              </span>
            </div>
          )}

          {/* API error */}
          {createMutation.isError && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              <AlertTriangle size={14} />
              Erreur lors de la création du projet. Veuillez réessayer.
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-100">
        <button
          onClick={() => step > 0 ? setStep((step - 1) as Step) : handleClose()}
          className="px-4 py-2 text-sm font-medium text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50"
          disabled={createMutation.isPending}
        >
          {step === 0 ? 'Annuler' : '← Retour'}
        </button>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">Étape {step + 1} / {STEPS.length}</span>
          {step < 2 ? (
            <Button onClick={handleNext} disabled={!canNext()} icon={<ChevronRight size={14} />}>
              Suivant
            </Button>
          ) : (
            <Button
              onClick={handleCreate}
              disabled={createMutation.isPending}
              icon={createMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
            >
              {createMutation.isPending ? 'Création…' : 'Créer le projet'}
            </Button>
          )}
        </div>
      </div>
    </Modal>
  )
}

import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Filter, AlertCircle, Check, X, Clock, ChevronDown, ChevronRight } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Swal from 'sweetalert2'
import { swalDark, swalConfirm } from '../lib/swalConfig'
import { apiClient } from '../lib/apiClient'

interface Approval {
  approval_id: number
  employee_id: number
  employee_name: string
  organization_name: string
  week_start: string
  total_hours: number
  status: string
  submitted_at: string | null
  decided_at: string | null
  updated_at: string | null
  rejection_reason: string | null
  notes: string | null
}

interface ApprovalEntry {
  timesheet_entry_id: number
  work_date: string
  project_name: string
  client_name: string
  entry_type: string
  hours_worked: number
  description: string
  notes: string | null
  billable_flag: boolean
  status: string
  approved_at: string | null
  updated_at: string | null
}

const STATUS_BADGE: Record<string, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  approved: { label: 'Approuvé', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
  rejected: { label: 'Rejeté', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  cancelled: { label: 'Annulé', color: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300' },
}

const ENTRY_TYPE_LABELS: Record<string, string> = {
  normal: 'Normal',
  overtime: 'Heures sup.',
  travel: 'Trajet',
  night: 'Nuit',
}

function weekLabel(weekStart: string): string {
  const monday = new Date(weekStart + 'T12:00:00')
  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)
  
  const weekNum = getWeekNumber(monday)
  
  return `Semaine ${weekNum} — ${monday.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })} → ${sunday.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })}`
}

function getWeekNumber(date: Date): number {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7))
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
}

export default function ManagerApprovalsPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const currentYear = new Date().getFullYear()
  
  // Filters
  const [selectedYear, setSelectedYear] = useState<number>(currentYear)
  const [selectedStatus, setSelectedStatus] = useState<string>('pending')
  const [selectedOrg, setSelectedOrg] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [collapsedWeeks, setCollapsedWeeks] = useState<Set<string>>(new Set())

  // Fetch approvals
  const { data: approvals = [], isLoading } = useQuery({
    queryKey: ['manager-approvals', selectedStatus, selectedYear],
    queryFn: () => apiClient.get<Approval[]>(`/manager/approvals?status=${selectedStatus}&year=${selectedYear}`),
  })

  // Mutations
  const approveMutation = useMutation({
    mutationFn: (id: number) => apiClient.post(`/manager/approvals/${id}/approve`, { notes: null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['manager-approvals'] })
      swalDark({
        icon: 'success',
        title: 'Approuvé',
        text: 'Le pointage a été approuvé avec succès',
        confirmButtonColor: '#10B981',
        timer: 2000,
      })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      apiClient.post(`/manager/approvals/${id}/reject`, { rejection_reason: reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['manager-approvals'] })
      swalDark({
        icon: 'success',
        title: 'Rejeté',
        text: 'Le pointage a été rejeté',
        confirmButtonColor: '#EF4444',
        timer: 2000,
      })
    },
  })

  // Get unique organizations
  const organizations = useMemo(() => {
    const orgs = new Set(approvals.map(a => a.organization_name))
    return Array.from(orgs).sort()
  }, [approvals])

  // Filter and search
  const filteredApprovals = useMemo(() => {
    return approvals.filter(approval => {
      const matchesOrg = selectedOrg === 'all' || approval.organization_name === selectedOrg
      const matchesSearch = searchQuery === '' || 
        approval.employee_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        approval.organization_name.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesOrg && matchesSearch
    })
  }, [approvals, selectedOrg, searchQuery])

  // Group by week
  const byWeek = useMemo(() => {
    const map: Record<string, Approval[]> = {}
    for (const approval of filteredApprovals) {
      const week = approval.week_start
      if (!map[week]) map[week] = []
      map[week].push(approval)
    }
    return Object.entries(map).sort(([a], [b]) => b.localeCompare(a))
  }, [filteredApprovals])

  const toggleWeek = (week: string) => {
    setCollapsedWeeks(prev => {
      const n = new Set(prev)
      n.has(week) ? n.delete(week) : n.add(week)
      return n
    })
  }

  const handleApprove = async (approval: Approval) => {
    const result = await swalConfirm({
      title: 'Approuver ce pointage ?',
      html: `Voulez-vous approuver le pointage de <strong>${approval.employee_name}</strong> pour la semaine du ${new Date(approval.week_start).toLocaleDateString('fr-FR')} ?<br><br><strong>${approval.total_hours}h</strong> au total`,
      icon: 'question',
      confirmButtonColor: '#10B981',
      cancelButtonColor: '#6B7280',
      confirmButtonText: 'Oui, approuver',
      cancelButtonText: 'Annuler',
    })
    if (result.isConfirmed) {
      approveMutation.mutate(approval.approval_id)
    }
  }

  const handleReject = async (approval: Approval) => {
    const result = await swalConfirm({
      title: 'Rejeter ce pointage',
      html: `Vous êtes sur le point de rejeter le pointage de <strong>${approval.employee_name}</strong> pour la semaine du ${new Date(approval.week_start).toLocaleDateString('fr-FR')}`,
      input: 'textarea',
      inputLabel: 'Motif du rejet',
      inputPlaceholder: t('approvals.rejectPlaceholder', 'Indiquez la raison du rejet...'),
      inputAttributes: {
        'aria-label': 'Motif du rejet',
        'rows': '4',
      },
      icon: 'warning',
      confirmButtonColor: '#EF4444',
      cancelButtonColor: '#6B7280',
      confirmButtonText: 'Rejeter',
      cancelButtonText: 'Annuler',
      inputValidator: (value) => {
        if (!value || value.trim().length < 10) {
          return 'Le motif doit contenir au moins 10 caractères'
        }
      },
    })
    if (result.isConfirmed && result.value) {
      rejectMutation.mutate({ id: approval.approval_id, reason: result.value })
    }
  }

  const handleViewDetails = async (approval: Approval) => {
    try {
      // Force fresh data by adding cache-busting timestamp
      const entries = await apiClient.get<ApprovalEntry[]>(`/manager/approvals/${approval.approval_id}/entries?_t=${Date.now()}`)
      
      // Group by date
      const byDate: Record<string, ApprovalEntry[]> = {}
      entries.forEach(e => {
        if (!byDate[e.work_date]) byDate[e.work_date] = []
        byDate[e.work_date].push(e)
      })
      
      const sortedDates = Object.keys(byDate).sort()
      
      // Build HTML with actions for each entry
      const entriesHtml = sortedDates.map(date => {
        const dateEntries = byDate[date]
        const dateTotal = dateEntries.reduce((sum, e) => sum + e.hours_worked, 0)
        
        const entriesRows = dateEntries.map(e => {
          const statusBadge = e.status === 'approved' 
            ? '<span class="px-2 py-0.5 rounded-full text-xs bg-emerald-100 text-emerald-700">✓ Approuvé</span>'
            : e.status === 'rejected'
            ? '<span class="px-2 py-0.5 rounded-full text-xs bg-red-100 text-red-700">✗ Rejeté</span>'
            : '<span class="px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-700">En attente</span>'
          
          const rejectionInfo = e.status === 'rejected' && e.notes
            ? `
              <div class="text-xs text-red-600 mt-1 flex items-start gap-1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="flex-shrink-0 mt-0.5">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <div>
                  <div class="font-semibold">Motif: ${e.notes}</div>
                  ${e.updated_at ? `<div class="text-slate-500 text-[10px] mt-0.5">Rejeté le ${new Date(e.updated_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}</div>` : ''}
                </div>
              </div>
            `
            : ''
          
          const approvalInfo = e.status === 'approved' && e.approved_at
            ? `<div class="text-xs text-emerald-600 mt-1">Approuvé le ${new Date(e.approved_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}</div>`
            : ''
          
          const actions = e.status === 'submitted' 
            ? `
              <button class="approve-entry-btn p-1 rounded hover:bg-emerald-50 text-emerald-600" data-entry-id="${e.timesheet_entry_id}" data-action="approve" title="Approuver" aria-label="Approuver">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
              </button>
              <button class="reject-entry-btn p-1 rounded hover:bg-red-50 text-red-600" data-entry-id="${e.timesheet_entry_id}" data-action="reject" title="Rejeter" aria-label="Rejeter">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            `
            : `
              <button class="pending-entry-btn p-1 rounded hover:bg-blue-50 text-blue-600" data-entry-id="${e.timesheet_entry_id}" data-action="pending" title="Remettre en attente" aria-label="Remettre en attente">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
              </button>
            `
          
          return `
            <tr class="border-b border-slate-100 hover:bg-slate-50">
              <td class="py-2 pl-4 text-xs text-slate-600">${e.client_name}</td>
              <td class="py-2 text-xs text-slate-700">${e.project_name}</td>
              <td class="py-2 text-xs text-slate-600">${ENTRY_TYPE_LABELS[e.entry_type] || e.entry_type}</td>
              <td class="py-2 text-xs text-slate-700 font-mono text-right">${e.hours_worked}h</td>
              <td class="py-2 text-xs">
                ${statusBadge}
                ${rejectionInfo}
                ${approvalInfo}
              </td>
              <td class="py-2 text-center">
                <div class="flex items-center justify-center gap-1">
                  ${actions}
                </div>
              </td>
            </tr>
          `
        }).join('')
        
        return `
          <tr class="bg-slate-100 border-b-2 border-slate-300">
            <td colspan="3" class="py-2 px-2 text-sm font-semibold text-slate-700">
              ${new Date(date + 'T12:00:00').toLocaleDateString('fr-FR', { weekday: 'long', day: '2-digit', month: 'long' })}
            </td>
            <td class="py-2 text-sm font-bold text-slate-800 text-right">${dateTotal}h</td>
            <td colspan="2"></td>
          </tr>
          ${entriesRows}
        `
      }).join('')
      
      // Show "Revert All" button if approval is approved or rejected
      const revertAllButton = approval.status !== 'pending' 
        ? `
          <button id="revert-all-btn" class="w-full px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="1 4 1 10 7 10"></polyline>
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
            </svg>
            Remettre toute la semaine en attente
          </button>
        `
        : ''

      await swalDark({
        title: `Détails — ${approval.employee_name}`,
        html: `
          <div class="text-left space-y-4">
            <div class="grid grid-cols-3 gap-3">
              <div class="bg-slate-50 rounded-lg p-3">
                <p class="text-xs text-slate-500 mb-1">Semaine</p>
                <p class="text-sm font-semibold">${new Date(approval.week_start).toLocaleDateString('fr-FR')}</p>
              </div>
              <div class="bg-slate-50 rounded-lg p-3">
                <p class="text-xs text-slate-500 mb-1">Total</p>
                <p class="text-sm font-semibold">${approval.total_hours}h</p>
              </div>
              <div class="bg-slate-50 rounded-lg p-3">
                <p class="text-xs text-slate-500 mb-1">Organisation</p>
                <p class="text-sm font-semibold">${approval.organization_name}</p>
              </div>
            </div>
            ${revertAllButton}
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700">
              <strong>💡 Astuce :</strong> Vous pouvez approuver ou rejeter chaque entrée individuellement
            </div>
            <div>
              <p class="text-xs font-semibold text-slate-500 uppercase mb-2">Entrées de temps</p>
              <div class="overflow-x-auto max-h-96 overflow-y-auto">
                <table class="w-full">
                  <thead class="sticky top-0 bg-white">
                    <tr class="border-b-2 border-slate-300">
                      <th class="py-2 text-left text-xs text-slate-500 font-semibold">Client</th>
                      <th class="py-2 text-left text-xs text-slate-500 font-semibold">Projet</th>
                      <th class="py-2 text-left text-xs text-slate-500 font-semibold">Type</th>
                      <th class="py-2 text-right text-xs text-slate-500 font-semibold">Heures</th>
                      <th class="py-2 text-left text-xs text-slate-500 font-semibold">Statut</th>
                      <th class="py-2 text-center text-xs text-slate-500 font-semibold">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${entriesHtml}
                  </tbody>
                </table>
              </div>
            </div>
            ${approval.rejection_reason ? `
              <div class="bg-red-50 border border-red-200 rounded-lg p-3">
                <p class="text-xs font-semibold text-red-700 mb-1">Motif du rejet (semaine complète)</p>
                <p class="text-sm text-red-600">${approval.rejection_reason}</p>
              </div>
            ` : ''}
          </div>
        `,
        width: '900px',
        confirmButtonColor: '#4F46E5',
        confirmButtonText: 'Fermer',
        didOpen: () => {
          const modal = Swal.getPopup()
          if (!modal) return
          
          // Handle "Revert All" button
          const revertAllBtn = modal.querySelector('#revert-all-btn')
          if (revertAllBtn) {
            revertAllBtn.addEventListener('click', async () => {
              const result = await swalConfirm({
                title: 'Remettre toute la semaine en attente ?',
                html: `Toutes les entrées de cette semaine seront remises en attente.<br><br>L'employé devra soumettre à nouveau son pointage.`,
                icon: 'warning',
                confirmButtonColor: '#F59E0B',
                cancelButtonColor: '#6B7280',
                confirmButtonText: 'Oui, remettre en attente',
                cancelButtonText: 'Annuler',
              })
              
              if (result.isConfirmed) {
                try {
                  await apiClient.post(`/manager/approvals/${approval.approval_id}/revert-all`, {})
                  await queryClient.invalidateQueries({ queryKey: ['manager-approvals'] })
                  Swal.close()
                  await swalDark({
                    icon: 'success',
                    title: 'Semaine remise en attente',
                    text: 'Toutes les entrées ont été remises en attente',
                    timer: 2000,
                    showConfirmButton: false,
                  })
                  // Reopen modal with fresh data
                  handleViewDetails(approval)
                } catch (error: any) {
                  swalDark({
                    icon: 'error',
                    title: error.response?.status === 402 ? 'Licence requise' : 'Erreur',
                    text: error.response?.status === 402 
                      ? 'La remise en attente globale nécessite le module "Advanced Approvals". Contactez votre administrateur.'
                      : error.message || 'Impossible de remettre en attente',
                  })
                }
              }
            })
          }
          
          // Use event delegation on the modal container
          modal.addEventListener('click', async (e) => {
            const target = e.target as HTMLElement
            const button = target.closest('button[data-entry-id]') as HTMLButtonElement
            if (!button) return
            
            e.preventDefault()
            e.stopPropagation()
            
            const entryId = button.dataset.entryId
            const action = button.dataset.action
            
            if (!entryId || !action) return
            
            try {
              if (action === 'approve') {
                await apiClient.post(`/manager/approvals/${approval.approval_id}/entries/${entryId}/approve`, {})
                await queryClient.invalidateQueries({ queryKey: ['manager-approvals'] })
                Swal.close()
                await swalDark({
                  icon: 'success',
                  title: 'Entrée approuvée',
                  timer: 1500,
                  showConfirmButton: false,
                })
                // Reopen modal with fresh data
                handleViewDetails(approval)
              } else if (action === 'reject') {
                const result = await swalConfirm({
                  title: 'Rejeter cette entrée',
                  input: 'textarea',
                  inputLabel: 'Motif du rejet',
                  inputPlaceholder: t('approvals.rejectPlaceholder', 'Indiquez la raison...'),
                  confirmButtonColor: '#EF4444',
                  cancelButtonColor: '#6B7280',
                  confirmButtonText: 'Rejeter',
                  cancelButtonText: 'Annuler',
                  inputValidator: (value) => {
                    if (!value || value.trim().length < 5) {
                      return 'Le motif doit contenir au moins 5 caractères'
                    }
                  },
                })
                
                if (result.isConfirmed && result.value) {
                  await apiClient.post(`/manager/approvals/${approval.approval_id}/entries/${entryId}/reject`, {
                    rejection_reason: result.value
                  })
                  await queryClient.invalidateQueries({ queryKey: ['manager-approvals'] })
                  Swal.close()
                  await swalDark({
                    icon: 'success',
                    title: 'Entrée rejetée',
                    timer: 1500,
                    showConfirmButton: false,
                  })
                  // Reopen modal with fresh data
                  handleViewDetails(approval)
                }
              } else if (action === 'pending') {
                await apiClient.post(`/manager/approvals/${approval.approval_id}/entries/${entryId}/pending`, {})
                await queryClient.invalidateQueries({ queryKey: ['manager-approvals'] })
                Swal.close()
                await swalDark({
                  icon: 'success',
                  title: 'Entrée remise en attente',
                  timer: 1500,
                  showConfirmButton: false,
                })
                // Reopen modal with fresh data
                handleViewDetails(approval)
              }
            } catch (error: any) {
              swalDark({
                icon: 'error',
                title: error.response?.status === 402 ? 'Licence requise' : 'Erreur',
                text: error.response?.status === 402 
                  ? 'La validation ligne par ligne nécessite le module "Advanced Approvals". Contactez votre administrateur.'
                  : error.message || 'Impossible d\'effectuer cette action',
              })
            }
          })
        },
      })
    } catch (error) {
      swalDark({
        icon: 'error',
        title: 'Erreur',
        text: 'Impossible de charger les détails',
        confirmButtonColor: '#EF4444',
      })
    }
  }

  const years = Array.from({ length: 5 }, (_, i) => currentYear - 2 + i)

  const pendingCount = approvals.filter(a => a.status === 'pending').length
  const approvedCount = approvals.filter(a => a.status === 'approved').length
  const rejectedCount = approvals.filter(a => a.status === 'rejected').length

  return (
    <div className="max-w-5xl space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white">Validations</h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          {filteredApprovals.length} pointage{filteredApprovals.length > 1 ? 's' : ''} trouvé{filteredApprovals.length > 1 ? 's' : ''}
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-3 sm:p-4">
        <div className="flex flex-col gap-4">
          {/* Search */}
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder={t('common.search', 'Rechercher par nom, organisation...')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-3 py-2 text-sm border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Year filter */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              <Filter size={16} />
              <span className="font-medium">Année:</span>
            </div>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {years.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          {/* Status filter */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              <span className="font-medium">Statut:</span>
            </div>
            <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
              {[
                { value: 'all', label: 'Tous', count: approvals.length },
                { value: 'pending', label: 'En attente', count: pendingCount },
                { value: 'approved', label: 'Approuvés', count: approvedCount },
                { value: 'rejected', label: 'Rejetés', count: rejectedCount },
              ].map(({ value, label, count }) => (
                <button
                  key={value}
                  onClick={() => setSelectedStatus(value)}
                  className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                    selectedStatus === value
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-600'
                  }`}
                >
                  {label} <span className="ml-1 opacity-70">({count})</span>
                </button>
              ))}
            </div>
          </div>

          {/* Organization filter */}
          {organizations.length > 0 && (
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
              <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                <span className="font-medium">Organisation:</span>
              </div>
              <select
                value={selectedOrg}
                onChange={(e) => setSelectedOrg(e.target.value)}
                className="px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="all">Toutes les organisations</option>
                {organizations.map(org => (
                  <option key={org} value={org}>{org}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Results count */}
      <div className="text-sm text-slate-500 dark:text-slate-400">
        {filteredApprovals.length} résultat{filteredApprovals.length > 1 ? 's' : ''}
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && filteredApprovals.length === 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <AlertCircle size={40} className="mx-auto mb-3 text-slate-300 dark:text-slate-600" />
          <p className="text-slate-500 dark:text-slate-400 text-sm">Aucun pointage trouvé</p>
          <p className="text-slate-400 dark:text-slate-500 text-xs mt-1">
            Essayez de modifier les filtres
          </p>
        </div>
      )}

      {/* Weeks list */}
      {!isLoading && byWeek.length > 0 && (
        <div className="space-y-4">
          {byWeek.map(([week, weekApprovals]) => {
            const collapsed = collapsedWeeks.has(week)
            const totalHours = weekApprovals.reduce((s, a) => s + Number(a.total_hours), 0)
            const pendingInWeek = weekApprovals.filter(a => a.status === 'pending').length

            return (
              <div key={week} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
                {/* Week header */}
                <div className="px-3 sm:px-4 py-3 bg-slate-50 dark:bg-slate-700 border-b border-slate-200 dark:border-slate-600">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <button
                      onClick={() => toggleWeek(week)}
                      className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-800 dark:text-slate-200 hover:text-indigo-600 dark:hover:text-indigo-400 text-left flex-1 min-w-0"
                    >
                      {collapsed ? <ChevronRight size={16} className="flex-shrink-0" /> : <ChevronDown size={16} className="flex-shrink-0" />}
                      <span className="truncate">{weekLabel(week)}</span>
                    </button>
                    {pendingInWeek > 0 && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap flex-shrink-0 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                        {pendingInWeek} en attente
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 sm:gap-3 text-xs sm:text-sm text-slate-500 dark:text-slate-400 pl-6">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{totalHours.toFixed(1)}h</span>
                    <span className="hidden sm:inline">·</span>
                    <span className="hidden sm:inline">{weekApprovals.length} employé{weekApprovals.length > 1 ? 's' : ''}</span>
                    <span className="sm:hidden text-slate-400">({weekApprovals.length})</span>
                  </div>
                </div>

                {/* Approvals table */}
                {!collapsed && (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide border-b border-slate-100 dark:border-slate-700">
                          <th className="px-3 py-2 text-left">Employé</th>
                          <th className="px-3 py-2 text-left hidden sm:table-cell">Organisation</th>
                          <th className="px-3 py-2 text-center">Heures</th>
                          <th className="px-3 py-2 text-left hidden sm:table-cell">Soumis le</th>
                          <th className="px-3 py-2 text-left hidden lg:table-cell">Dernière modif.</th>
                          <th className="px-3 py-2 text-left">Statut</th>
                          <th className="px-3 py-2 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {weekApprovals
                          .sort((a, b) => a.employee_name.localeCompare(b.employee_name))
                          .map(approval => (
                            <tr key={approval.approval_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 border-b border-slate-100 dark:border-slate-700">
                              <td className="px-3 py-2.5 text-xs sm:text-sm text-slate-800 dark:text-slate-200 font-medium">
                                {approval.employee_name}
                                <span className="block sm:hidden text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                                  {approval.organization_name}
                                </span>
                              </td>
                              <td className="px-3 py-2.5 text-xs sm:text-sm text-slate-600 dark:text-slate-400 hidden sm:table-cell">
                                {approval.organization_name}
                              </td>
                              <td className="px-3 py-2.5 text-center">
                                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
                                  {approval.total_hours}h
                                </span>
                              </td>
                              <td className="px-3 py-2.5 text-xs sm:text-sm text-slate-600 dark:text-slate-400 hidden sm:table-cell">
                                {approval.submitted_at ? new Date(approval.submitted_at).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }) : '—'}
                              </td>
                              <td className="px-3 py-2.5 text-xs text-slate-600 dark:text-slate-400 hidden lg:table-cell">
                                {approval.updated_at 
                                  ? new Date(approval.updated_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
                                  : approval.decided_at
                                  ? new Date(approval.decided_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
                                  : approval.submitted_at
                                  ? new Date(approval.submitted_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
                                  : '—'}
                              </td>
                              <td className="px-3 py-2.5">
                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[approval.status]?.color || 'bg-slate-100 text-slate-600'}`}>
                                  {STATUS_BADGE[approval.status]?.label || approval.status}
                                </span>
                              </td>
                              <td className="px-3 py-2.5">
                                <div className="flex items-center justify-end gap-1">
                                  <button
                                    onClick={() => handleViewDetails(approval)}
                                    className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-600 text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                                    title="Voir détails"
                                  >
                                    <Clock size={16} />
                                  </button>
                                  {approval.status === 'pending' && (
                                    <>
                                      <button
                                        onClick={() => handleApprove(approval)}
                                        disabled={approveMutation.isPending}
                                        className="p-1.5 rounded-lg hover:bg-emerald-50 dark:hover:bg-emerald-900/30 text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors disabled:opacity-50"
                                        title="Approuver"
                                      >
                                        <Check size={16} />
                                      </button>
                                      <button
                                        onClick={() => handleReject(approval)}
                                        disabled={rejectMutation.isPending}
                                        className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors disabled:opacity-50"
                                        title="Rejeter"
                                      >
                                        <X size={16} />
                                      </button>
                                    </>
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

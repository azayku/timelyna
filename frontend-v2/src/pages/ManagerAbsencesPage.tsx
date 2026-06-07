import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Filter, Calendar, AlertCircle, Check, X, RotateCcw, Trash2 } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { swalDark, swalConfirm } from '../lib/swalConfig'
import { fetchTeamAbsences, approveAbsence, rejectAbsence, revertAbsenceToPending, deleteAbsence } from '../features/absences/api'
import type { Absence } from '../features/absences/types'
import Pagination from '../components/ui/Pagination'

const TYPE_LABELS: Record<string, string> = {
  cp: 'Congé payé',
  maladie: 'Maladie',
  autre: 'Autre',
}

const TYPE_COLORS: Record<string, string> = {
  cp: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  maladie: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  autre: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
}

const STATUS_BADGE: Record<string, { label: string; color: string }> = {
  approved: { label: 'Approuvé', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
  rejected: { label: 'Rejeté', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  pending: { label: 'En attente', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
}

function daysBetween(start: string, end: string): number {
  const ms = new Date(end).getTime() - new Date(start).getTime()
  return Math.max(1, Math.round(ms / 86400000) + 1)
}

export default function ManagerAbsencesPage() {
  const { t } = useTranslation()
  const qc = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all')
  const [typeFilter, setTypeFilter] = useState<'all' | 'cp' | 'maladie' | 'autre'>('all')
  const [orgFilter, setOrgFilter] = useState<string>('all')
  const [yearFilter, setYearFilter] = useState<number>(new Date().getFullYear())
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(15)

  // Fetch absences with year filter
  const { data: absences = [], isLoading } = useQuery({
    queryKey: ['manager-absences', yearFilter],
    queryFn: () => fetchTeamAbsences(undefined, yearFilter),
  })

  // Get unique organizations from absences
  const organizations = useMemo(() => {
    const orgs = new Set<string>()
    absences.forEach(a => {
      if (a.org_name && a.org_name !== '—') {
        orgs.add(a.org_name)
      }
    })
    return Array.from(orgs).sort()
  }, [absences])

  const refresh = () => qc.invalidateQueries({ queryKey: ['manager-absences'] })

  // Mutations
  const approveMutation = useMutation({
    mutationFn: (id: number) => approveAbsence(id),
    onSuccess: () => refresh(),
    onError: (error: any) => {
      swalDark({
        icon: 'error',
        title: 'Erreur',
        text: error.message || 'Impossible d\'approuver cette absence',
        confirmButtonColor: '#4F46E5',
      })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => rejectAbsence(id, reason),
    onSuccess: () => {
      refresh()
      swalDark({
        icon: 'success',
        title: 'Absence rejetée',
        text: 'L\'absence a été rejetée avec succès',
        confirmButtonColor: '#4F46E5',
        timer: 2000,
      })
    },
    onError: (error: any) => {
      swalDark({
        icon: 'error',
        title: 'Erreur',
        text: error.message || 'Impossible de rejeter cette absence',
        confirmButtonColor: '#4F46E5',
      })
    },
  })

  const revertMutation = useMutation({
    mutationFn: (id: number) => revertAbsenceToPending(id),
    onSuccess: () => refresh(),
    onError: (error: any) => {
      swalDark({
        icon: 'error',
        title: 'Erreur',
        text: error.message || 'Impossible de remettre en attente',
        confirmButtonColor: '#4F46E5',
      })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteAbsence(id),
    onSuccess: () => refresh(),
    onError: (error: any) => {
      swalDark({
        icon: 'error',
        title: 'Erreur',
        text: error.message || 'Impossible de supprimer cette absence',
        confirmButtonColor: '#4F46E5',
      })
    },
  })

  // Filter absences
  const filteredAbsences = useMemo(() => {
    let items = absences

    if (statusFilter !== 'all') {
      items = items.filter(a => a.status === statusFilter)
    }

    if (typeFilter !== 'all') {
      items = items.filter(a => a.absence_type === typeFilter)
    }

    if (orgFilter !== 'all') {
      items = items.filter(a => a.org_name === orgFilter)
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      items = items.filter(a => 
        a.employee_name.toLowerCase().includes(q) ||
        a.org_name.toLowerCase().includes(q) ||
        (a.notes && a.notes.toLowerCase().includes(q))
      )
    }

    return items.sort((a, b) => b.start_date.localeCompare(a.start_date))
  }, [absences, statusFilter, typeFilter, orgFilter, searchQuery])

  useMemo(() => { setPage(1) }, [statusFilter, typeFilter, orgFilter, searchQuery, pageSize, yearFilter])

  const totalPages = Math.max(1, Math.ceil(filteredAbsences.length / pageSize))
  const safePage = Math.min(page, totalPages)
  const pageStart = (safePage - 1) * pageSize
  const pageEnd = pageStart + pageSize
  const pagedAbsences = filteredAbsences.slice(pageStart, pageEnd)

  const pendingCount = absences.filter(a => a.status === 'pending').length
  const approvedCount = absences.filter(a => a.status === 'approved').length
  const rejectedCount = absences.filter(a => a.status === 'rejected').length

  // Get available years
  const availableYears = useMemo(() => {
    const years = new Set<number>()
    const currentYear = new Date().getFullYear()
    for (let i = currentYear - 2; i <= currentYear + 1; i++) {
      years.add(i)
    }
    return Array.from(years).sort((a, b) => b - a)
  }, [])

  const handleApprove = async (absence: Absence) => {
    const result = await swalConfirm({
      title: 'Approuver l\'absence',
      html: `Voulez-vous approuver l'absence de <strong>${absence.employee_name}</strong> ?<br><small class="text-slate-500">Du ${new Date(absence.start_date + 'T12:00:00').toLocaleDateString('fr-FR')} au ${new Date(absence.end_date + 'T12:00:00').toLocaleDateString('fr-FR')}</small>`,
      icon: 'question',
      confirmButtonColor: '#10B981',
      cancelButtonColor: '#6B7280',
      confirmButtonText: 'Oui, approuver',
      cancelButtonText: 'Annuler',
    })
    
    if (result.isConfirmed) {
      approveMutation.mutate(absence.absence_id)
    }
  }

  const handleReject = async (absence: Absence) => {
    const result = await swalConfirm({
      title: 'Rejeter l\'absence',
      html: `
        <div class="text-left">
          <p class="text-sm text-slate-600 mb-2">
            Vous êtes sur le point de rejeter l'absence de <strong>${absence.employee_name}</strong>
          </p>
          <p class="text-xs text-slate-500 mb-4">
            Du ${new Date(absence.start_date + 'T12:00:00').toLocaleDateString('fr-FR')} 
            au ${new Date(absence.end_date + 'T12:00:00').toLocaleDateString('fr-FR')}
          </p>
        </div>
      `,
      input: 'textarea',
      inputLabel: 'Motif du rejet',
      inputPlaceholder: t('approvals.rejectPlaceholder', 'Indiquez la raison du rejet...'),
      inputAttributes: {
        'aria-label': 'Motif du rejet',
        'rows': '4',
      },
      inputValidator: (value) => {
        if (!value || !value.trim()) {
          return 'Veuillez indiquer un motif de rejet'
        }
      },
      confirmButtonColor: '#EF4444',
      cancelButtonColor: '#6B7280',
      confirmButtonText: 'Confirmer le rejet',
      cancelButtonText: 'Annuler',
      customClass: {
        input: 'text-sm',
      },
    })
    
    if (result.isConfirmed && result.value) {
      rejectMutation.mutate({ id: absence.absence_id, reason: result.value })
    }
  }

  const handleRevertToPending = async (absence: Absence) => {
    const result = await swalConfirm({
      title: 'Remettre en attente',
      html: `Voulez-vous remettre en attente l'absence de <strong>${absence.employee_name}</strong> ?`,
      icon: 'question',
      confirmButtonColor: '#3B82F6',
      cancelButtonColor: '#6B7280',
      confirmButtonText: 'Oui, remettre en attente',
      cancelButtonText: 'Annuler',
    })
    
    if (result.isConfirmed) {
      revertMutation.mutate(absence.absence_id)
    }
  }

  const handleDelete = async (absence: Absence) => {
    const result = await swalConfirm({
      title: 'Supprimer l\'absence',
      html: `Voulez-vous supprimer définitivement l'absence de <strong>${absence.employee_name}</strong> ?<br><br><small class="text-red-600">⚠️ Cette action est irréversible</small>`,
      icon: 'warning',
      confirmButtonColor: '#EF4444',
      cancelButtonColor: '#6B7280',
      confirmButtonText: 'Oui, supprimer',
      cancelButtonText: 'Annuler',
    })
    
    if (result.isConfirmed) {
      deleteMutation.mutate(absence.absence_id)
    }
  }

  return (
    <div className="max-w-7xl space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white">
            Absences équipe
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {pendingCount} en attente · {approvedCount} approuvé{approvedCount > 1 ? 's' : ''} · {rejectedCount} rejeté{rejectedCount > 1 ? 's' : ''}
          </p>
        </div>
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
              value={yearFilter}
              onChange={(e) => setYearFilter(Number(e.target.value))}
              className="px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {availableYears.map(year => (
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
                { value: 'all', label: 'Tous', count: absences.length },
                { value: 'pending', label: 'En attente', count: pendingCount },
                { value: 'approved', label: 'Approuvés', count: approvedCount },
                { value: 'rejected', label: 'Rejetés', count: rejectedCount },
              ].map(({ value, label, count }) => (
                <button key={value}
                  onClick={() => setStatusFilter(value as typeof statusFilter)}
                  className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                    statusFilter === value
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-600'
                  }`}>
                  {label} <span className="ml-1 opacity-70">({count})</span>
                </button>
              ))}
            </div>
          </div>

          {/* Type filter */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              <span className="font-medium">Type:</span>
            </div>
            <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
              {[
                { value: 'all', label: 'Tous' },
                { value: 'cp', label: 'Congés payés' },
                { value: 'maladie', label: 'Maladie' },
                { value: 'autre', label: 'Autre' },
              ].map(({ value, label }) => (
                <button key={value}
                  onClick={() => setTypeFilter(value as typeof typeFilter)}
                  className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                    typeFilter === value
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-600'
                  }`}>
                  {label}
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
                value={orgFilter}
                onChange={(e) => setOrgFilter(e.target.value)}
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
        {filteredAbsences.length} résultat{filteredAbsences.length > 1 ? 's' : ''}
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <div className="text-slate-400 text-sm">Chargement…</div>
        </div>
      ) : filteredAbsences.length === 0 ? (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <Calendar size={40} className="mx-auto mb-3 text-slate-300 dark:text-slate-600" />
          <p className="text-slate-500 dark:text-slate-400 text-sm">Aucune absence trouvée</p>
          <p className="text-slate-400 dark:text-slate-500 text-xs mt-1">Essayez de modifier les filtres</p>
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden lg:block bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-full">
                <thead>
                  <tr className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/50">
                    <th className="px-3 py-3 text-left">Employé</th>
                    <th className="px-3 py-3 text-left">Organisation</th>
                    <th className="px-3 py-3 text-left">Type</th>
                    <th className="px-3 py-3 text-left">Début</th>
                    <th className="px-3 py-3 text-left">Fin</th>
                    <th className="px-3 py-3 text-center">Durée</th>
                    <th className="px-3 py-3 text-left">Description</th>
                    <th className="px-3 py-3 text-center">Solde CP</th>
                    <th className="px-3 py-3 text-left">Dernier congé</th>
                    <th className="px-3 py-3 text-left">Statut</th>
                    <th className="px-3 py-3 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {pagedAbsences.map(absence => {
                    const typeColor = TYPE_COLORS[absence.absence_type]
                    const typeLabel = TYPE_LABELS[absence.absence_type]
                    const statusBadge = STATUS_BADGE[absence.status]
                    const days = daysBetween(absence.start_date, absence.end_date)

                    return (
                      <tr key={absence.absence_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                        <td className="px-3 py-3 text-sm text-slate-700 dark:text-slate-300 font-medium whitespace-nowrap">
                          {absence.employee_name}
                        </td>
                        <td className="px-3 py-3 text-xs text-slate-600 dark:text-slate-400 whitespace-nowrap">
                          {absence.org_name}
                        </td>
                        <td className="px-3 py-3">
                          <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${typeColor}`}>
                            <Calendar size={10} />
                            {typeLabel}
                          </span>
                        </td>
                        <td className="px-3 py-3 text-xs text-slate-600 dark:text-slate-400 whitespace-nowrap">
                          {new Date(absence.start_date + 'T12:00:00').toLocaleDateString('fr-FR', { 
                            day: '2-digit', month: 'short'
                          })}
                        </td>
                        <td className="px-3 py-3 text-xs text-slate-600 dark:text-slate-400 whitespace-nowrap">
                          {new Date(absence.end_date + 'T12:00:00').toLocaleDateString('fr-FR', { 
                            day: '2-digit', month: 'short'
                          })}
                        </td>
                        <td className="px-3 py-3 text-center">
                          <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                            {days}j
                          </span>
                        </td>
                        <td className="px-3 py-3 text-xs text-slate-600 dark:text-slate-400 max-w-xs">
                          {absence.notes ? (
                            <div className="line-clamp-1">{absence.notes}</div>
                          ) : (
                            <span className="text-slate-400 italic">—</span>
                          )}
                          {absence.status === 'rejected' && absence.rejection_reason && (
                            <div className="mt-1 flex items-start gap-1 text-xs text-red-600 dark:text-red-400">
                              <AlertCircle size={10} className="flex-shrink-0 mt-0.5" />
                              <span className="line-clamp-1">{absence.rejection_reason}</span>
                            </div>
                          )}
                        </td>
                        <td className="px-3 py-3 text-center">
                          <div className="text-xs">
                            <div className="font-semibold text-slate-700 dark:text-slate-300">
                              {absence.days_remaining}j
                            </div>
                            <div className="text-slate-400 text-[10px]">
                              /{absence.annual_leave_days}j
                            </div>
                          </div>
                        </td>
                        <td className="px-3 py-3 text-xs text-slate-600 dark:text-slate-400">
                          {absence.last_leave_date ? (
                            <div>
                              <div className="whitespace-nowrap">
                                {new Date(absence.last_leave_date + 'T12:00:00').toLocaleDateString('fr-FR', { 
                                  day: '2-digit', month: 'short'
                                })}
                              </div>
                              <div className="text-slate-400 text-[10px]">
                                ({absence.last_leave_days}j)
                              </div>
                            </div>
                          ) : (
                            <span className="text-slate-400 italic">—</span>
                          )}
                        </td>
                        <td className="px-3 py-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${statusBadge.color}`}>
                            {statusBadge.label}
                          </span>
                        </td>
                        <td className="px-3 py-3">
                          <div className="flex items-center justify-center gap-1">
                            {absence.status === 'pending' ? (
                              <>
                                <button
                                  onClick={() => handleApprove(absence)}
                                  disabled={approveMutation.isPending}
                                  className="p-1 rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 transition-colors disabled:opacity-50"
                                  title="Approuver"
                                >
                                  <Check size={14} />
                                </button>
                                <button
                                  onClick={() => handleReject(absence)}
                                  disabled={rejectMutation.isPending}
                                  className="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 transition-colors disabled:opacity-50"
                                  title="Rejeter"
                                >
                                  <X size={14} />
                                </button>
                              </>
                            ) : (
                              <button
                                onClick={() => handleRevertToPending(absence)}
                                disabled={revertMutation.isPending}
                                className="p-1 rounded hover:bg-blue-50 dark:hover:bg-blue-900/30 text-blue-600 dark:text-blue-400 transition-colors disabled:opacity-50"
                                title="Remettre en attente"
                              >
                                <RotateCcw size={14} />
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(absence)}
                              disabled={deleteMutation.isPending}
                              className="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 transition-colors disabled:opacity-50"
                              title="Supprimer"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mobile/Tablet cards */}
          <div className="lg:hidden space-y-3">
            {pagedAbsences.map(absence => {
              const typeColor = TYPE_COLORS[absence.absence_type]
              const typeLabel = TYPE_LABELS[absence.absence_type]
              const statusBadge = STATUS_BADGE[absence.status]
              const days = daysBetween(absence.start_date, absence.end_date)

              return (
                <div key={absence.absence_id} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 space-y-3">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                        {absence.employee_name}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        {absence.org_name}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${typeColor}`}>
                          <Calendar size={12} />
                          {typeLabel}
                        </span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${statusBadge.color}`}>
                          {statusBadge.label}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Dates */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-slate-500 dark:text-slate-400">Début:</span>
                      <p className="text-slate-700 dark:text-slate-300 font-medium">
                        {new Date(absence.start_date + 'T12:00:00').toLocaleDateString('fr-FR', { 
                          day: '2-digit', month: 'short', year: 'numeric' 
                        })}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500 dark:text-slate-400">Fin:</span>
                      <p className="text-slate-700 dark:text-slate-300 font-medium">
                        {new Date(absence.end_date + 'T12:00:00').toLocaleDateString('fr-FR', { 
                          day: '2-digit', month: 'short', year: 'numeric' 
                        })}
                      </p>
                    </div>
                  </div>

                  {/* CP Balance & Last leave */}
                  <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 dark:bg-slate-700/50 p-2 rounded-lg">
                    <div>
                      <span className="text-slate-500 dark:text-slate-400">Solde CP:</span>
                      <p className="text-slate-700 dark:text-slate-300 font-semibold">
                        {absence.days_remaining}j / {absence.annual_leave_days}j
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500 dark:text-slate-400">Dernier congé:</span>
                      <p className="text-slate-700 dark:text-slate-300 font-medium">
                        {absence.last_leave_date ? (
                          <>
                            {new Date(absence.last_leave_date + 'T12:00:00').toLocaleDateString('fr-FR', { 
                              day: '2-digit', month: 'short'
                            })} ({absence.last_leave_days}j)
                          </>
                        ) : '—'}
                      </p>
                    </div>
                  </div>

                  {/* Description */}
                  {absence.notes && (
                    <div className="text-xs">
                      <span className="text-slate-500 dark:text-slate-400">Description:</span>
                      <p className="text-slate-600 dark:text-slate-400 line-clamp-2 mt-0.5">
                        {absence.notes}
                      </p>
                    </div>
                  )}

                  {/* Rejection reason */}
                  {absence.status === 'rejected' && absence.rejection_reason && (
                    <div className="flex items-start gap-1 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                      <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium">Motif du rejet:</span>
                        <p className="line-clamp-2 mt-0.5">{absence.rejection_reason}</p>
                      </div>
                    </div>
                  )}

                  {/* Duration */}
                  <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-700">
                    <span>Durée</span>
                    <span className="font-semibold text-slate-700 dark:text-slate-300">
                      {days} jour{days > 1 ? 's' : ''}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-2 border-t border-slate-100 dark:border-slate-700">
                    {absence.status === 'pending' ? (
                      <>
                        <button
                          onClick={() => handleApprove(absence)}
                          disabled={approveMutation.isPending}
                          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
                        >
                          <Check size={14} />
                          Approuver
                        </button>
                        <button
                          onClick={() => handleReject(absence)}
                          disabled={rejectMutation.isPending}
                          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
                        >
                          <X size={14} />
                          Rejeter
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => handleRevertToPending(absence)}
                        disabled={revertMutation.isPending}
                        className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
                      >
                        <RotateCcw size={14} />
                        Remettre en attente
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(absence)}
                      disabled={deleteMutation.isPending}
                      className="px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-red-50 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 text-sm font-medium transition-colors disabled:opacity-50"
                      title="Supprimer"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Pagination */}
          <Pagination
            page={safePage}
            totalPages={totalPages}
            totalItems={filteredAbsences.length}
            itemsPerPage={pageSize}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
          />
        </>
      )}
    </div>
  )
}

import { useState, useMemo } from 'react'
import { X, Download, Search, CheckSquare, Square, Loader2, AlertTriangle, FileText } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../lib/apiClient'
import { downloadTimesheetPdf, downloadHoursReportPdf } from '../../features/exports/api'
import { swalDark } from '../../lib/swalConfig'

export type PdfExportMode = 'timesheet' | 'hours-report'

interface Project {
  project_id: number
  project_name: string
}

interface PdfExportModalProps {
  open: boolean
  onClose: () => void
  mode: PdfExportMode
  defaultDateFrom: string
  defaultDateTo: string
}

export default function PdfExportModal({
  open,
  onClose,
  mode,
  defaultDateFrom,
  defaultDateTo,
}: PdfExportModalProps) {
  const today = new Date().toISOString().split('T')[0]

  const [dateFrom, setDateFrom] = useState(defaultDateFrom)
  const [dateTo, setDateTo] = useState(defaultDateTo)
  const [search, setSearch] = useState('')
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [exporting, setExporting] = useState(false)

  // Fetch projects depending on mode
  const { data: projects = [], isLoading: loadingProjects } = useQuery({
    queryKey: ['pdf-export-projects', mode],
    queryFn: () =>
      mode === 'hours-report'
        ? apiClient.get<Project[]>('/admin/projects?limit=500')
        : apiClient.get<Project[]>('/projects?active=true'),
    enabled: open,
    staleTime: 5 * 60 * 1000,
  })

  const filtered = useMemo(
    () =>
      projects.filter(p =>
        p.project_name.toLowerCase().includes(search.toLowerCase())
      ),
    [projects, search]
  )

  const allFilteredSelected =
    filtered.length > 0 && filtered.every(p => selectedIds.has(p.project_id))

  function toggleProject(id: number) {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (allFilteredSelected) {
      setSelectedIds(prev => {
        const next = new Set(prev)
        filtered.forEach(p => next.delete(p.project_id))
        return next
      })
    } else {
      setSelectedIds(prev => {
        const next = new Set(prev)
        filtered.forEach(p => next.add(p.project_id))
        return next
      })
    }
  }

  async function handleExport() {
    if (!dateFrom || !dateTo) return
    setExporting(true)
    try {
      const projectIds = selectedIds.size > 0 ? Array.from(selectedIds) : undefined
      if (mode === 'hours-report') {
        await downloadHoursReportPdf(dateFrom, dateTo, projectIds)
      } else {
        await downloadTimesheetPdf(dateFrom, dateTo, projectIds)
      }
      onClose()
    } catch (err) {
      await swalDark({
        icon: 'error',
        title: 'Erreur',
        text: err instanceof Error ? err.message : 'Erreur lors de la génération du PDF',
      })
    } finally {
      setExporting(false)
    }
  }

  if (!open) return null

  const modeLabel = mode === 'hours-report' ? 'Rapport heures' : 'Mes pointages'
  const selCount = selectedIds.size

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-lg flex flex-col max-h-[90dvh]">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center shrink-0">
              <FileText size={18} className="text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-800 dark:text-white leading-tight">
                Export PDF
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">{modeLabel}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">

          {/* Date range */}
          <div>
            <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
              Période *
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-500 dark:text-slate-400 mb-1">Du</label>
                <input
                  type="date"
                  value={dateFrom}
                  max={dateTo || today}
                  onChange={e => setDateFrom(e.target.value)}
                  className="w-full border border-slate-300 dark:border-slate-600 rounded-xl px-3 py-2.5 text-sm text-slate-800 dark:text-slate-200 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-500 dark:text-slate-400 mb-1">Au</label>
                <input
                  type="date"
                  value={dateTo}
                  min={dateFrom}
                  max={today}
                  onChange={e => setDateTo(e.target.value)}
                  className="w-full border border-slate-300 dark:border-slate-600 rounded-xl px-3 py-2.5 text-sm text-slate-800 dark:text-slate-200 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
            <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              Projets
            </span>
            <div className="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
          </div>

          {/* Projects section */}
          {loadingProjects ? (
            <div className="flex items-center justify-center gap-2 py-6 text-slate-400 text-sm">
              <Loader2 size={16} className="animate-spin" /> Chargement des projets…
            </div>
          ) : projects.length === 0 ? (
            <div className="flex items-center gap-2 py-4 text-slate-400 text-sm">
              <AlertTriangle size={15} />
              Aucun projet disponible
            </div>
          ) : (
            <div className="space-y-3">
              {/* Info */}
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {selCount === 0
                  ? 'Tous les projets seront inclus par défaut.'
                  : `${selCount} projet${selCount > 1 ? 's' : ''} sélectionné${selCount > 1 ? 's' : ''}`}
              </p>

              {/* Search */}
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                <input
                  type="text"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Rechercher un projet…"
                  className="w-full pl-8 pr-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-xl dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Select all row */}
              <button
                type="button"
                onClick={toggleAll}
                className="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-left"
              >
                {allFilteredSelected
                  ? <CheckSquare size={16} className="text-indigo-600 dark:text-indigo-400 shrink-0" />
                  : <Square size={16} className="text-slate-400 shrink-0" />
                }
                <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                  {allFilteredSelected ? 'Tout désélectionner' : 'Tout sélectionner'}
                </span>
                <span className="ml-auto text-xs text-slate-400">{filtered.length}</span>
              </button>

              <div className="border-t border-slate-100 dark:border-slate-800" />

              {/* Project list */}
              <div className="space-y-0.5 max-h-52 overflow-y-auto -mx-1 px-1">
                {filtered.length === 0 ? (
                  <p className="text-sm text-slate-400 text-center py-4">Aucun résultat</p>
                ) : (
                  filtered.map(p => {
                    const checked = selectedIds.has(p.project_id)
                    return (
                      <button
                        key={p.project_id}
                        type="button"
                        onClick={() => toggleProject(p.project_id)}
                        className={`flex items-center gap-2.5 w-full px-3 py-2 rounded-lg transition-colors text-left ${
                          checked
                            ? 'bg-indigo-50 dark:bg-indigo-900/20'
                            : 'hover:bg-slate-50 dark:hover:bg-slate-800'
                        }`}
                      >
                        {checked
                          ? <CheckSquare size={15} className="text-indigo-600 dark:text-indigo-400 shrink-0" />
                          : <Square size={15} className="text-slate-400 shrink-0" />
                        }
                        <span className={`text-sm ${checked ? 'font-medium text-indigo-700 dark:text-indigo-300' : 'text-slate-700 dark:text-slate-300'}`}>
                          {p.project_name}
                        </span>
                      </button>
                    )
                  })
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 px-5 py-4 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-b-2xl shrink-0">
          {/* Selection summary */}
          <div className="text-xs text-slate-500 dark:text-slate-400">
            {selCount > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-lg font-medium">
                {selCount} projet{selCount > 1 ? 's' : ''}
              </span>
            )}
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-xl transition-colors"
            >
              Annuler
            </button>
            <button
              type="button"
              onClick={handleExport}
              disabled={!dateFrom || !dateTo || exporting}
              className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-colors shadow-sm"
            >
              {exporting
                ? <Loader2 size={14} className="animate-spin" />
                : <Download size={14} />
              }
              {exporting ? 'Génération…' : 'Exporter PDF'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

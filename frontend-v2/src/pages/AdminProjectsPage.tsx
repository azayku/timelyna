import { useState, useMemo } from 'react'
import { Plus, Search, Upload, X, AlertTriangle, Loader2, Users, Trash2 } from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import PaginatedTable from '../components/ui/PaginatedTable'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import { useTranslation } from 'react-i18next'
import CreateProjectModal from '../components/modals/CreateProjectModal'
import ProjectDetailModal from '../components/modals/ProjectDetailModal'
import type { Project as ProjectModalShape } from '../components/modals/ProjectDetailModal'
import ImportModal from '../components/modals/ImportModal'
import TeamAssignmentModal from '../components/modals/TeamAssignmentModal'
import { useProjects, useDeleteProject } from '../features/projects/hooks'
import type { Project } from '../features/projects/types'
import { importProjectsCSV } from '../features/imports/api'
import { swalDark } from '../lib/swalConfig'
import { useQueryClient } from '@tanstack/react-query'

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-700',
  planning: 'bg-blue-100 text-blue-700',
  completed: 'bg-slate-100 text-slate-600',
  draft: 'bg-amber-100 text-amber-700',
  paused: 'bg-orange-100 text-orange-700',
  cancelled: 'bg-red-100 text-red-700',
}

const STATUS_LABELS: Record<string, string> = {
  active: 'Actif', planning: 'Planification', completed: 'Terminé',
  draft: 'Brouillon', paused: 'En pause', cancelled: 'Annulé',
}

function toModalShape(p: Project): ProjectModalShape {
  return {
    id: p.project_id,
    code: p.project_code,
    name: p.project_name,
    client: String(p.client_id),
    status: p.status,
    budget: Number(p.budget_hours ?? 0),
    billingRate: Number(p.billing_rate),
    team: Array.isArray(p.team_members) ? p.team_members.length : 0,
    teamMembers: [], // TODO: Fetch detailed team member info from API
    start: p.start_date,
    end: p.end_date,
    description: p.description ?? undefined,
  }
}

export default function AdminProjectsPage() {
  const { t } = useTranslation()
  const { data: projects = [], isLoading, isError } = useProjects()
  const deleteMutation = useDeleteProject()
  const queryClient = useQueryClient()

  const [search, setSearch] = useState('')
  const [createModal, setCreateModal] = useState(false)
  const [detailProject, setDetailProject] = useState<ProjectModalShape | null>(null)
  const [importModal, setImportModal] = useState(false)
  const [teamProject, setTeamProject] = useState<Project | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)
  const [isImporting, setIsImporting] = useState(false)
  const [fileInputRef, setFileInputRef] = useState<HTMLInputElement | null>(null)

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return projects.filter(p =>
      p.project_name.toLowerCase().includes(q) || p.project_code.toLowerCase().includes(q)
    )
  }, [projects, search])

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setIsImporting(true)
    try {
      const result = await importProjectsCSV(file)
      await swalDark({
        icon: result.errors.length === 0 ? 'success' : 'warning',
        title: 'Import terminé',
        html: `<p>${result.message}</p>${result.errors.length > 0 ? `<ul class="text-left text-sm mt-2">${result.errors.slice(0, 5).map(err => `<li>• ${err}</li>`).join('')}</ul>` : ''}`,
      })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Import échoué'
      await swalDark({ icon: 'error', title: 'Erreur', text: message })
    } finally {
      setIsImporting(false)
      if (fileInputRef) fileInputRef.value = ''
    }
  }

  const columns = useMemo(() => [
    {
      key: 'project_name',
      header: t('common.name', 'Nom'),
      render: (p: Project) => (
        <div>
          <p className="font-medium text-slate-800 dark:text-slate-200">{p.project_name}</p>
          <p className="text-xs text-slate-400 font-mono mt-0.5">{p.project_code}</p>
        </div>
      ),
    },
    {
      key: 'status',
      header: t('common.status', 'Statut'),
      width: '120px',
      render: (p: Project) => (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[p.status] ?? 'bg-slate-100 text-slate-600'}`}>
          {STATUS_LABELS[p.status] ?? p.status}
        </span>
      ),
    },
    {
      key: 'start_date',
      header: 'Début',
      width: '110px',
      render: (p: Project) => <span className="text-slate-500 text-xs">{p.start_date ? new Date(p.start_date).toLocaleDateString('fr-FR') : '—'}</span>,
    },
    {
      key: 'end_date',
      header: 'Fin',
      width: '110px',
      render: (p: Project) => <span className="text-slate-500 text-xs">{p.end_date ? new Date(p.end_date).toLocaleDateString('fr-FR') : '—'}</span>,
    },
    {
      key: 'budget_hours',
      header: 'Budget',
      width: '90px',
      render: (p: Project) => <span className="text-slate-600 text-sm">{p.budget_hours ? `${p.budget_hours}h` : '—'}</span>,
    },
    {
      key: 'billing_rate',
      header: 'Taux',
      width: '90px',
      render: (p: Project) => <span className="font-mono text-sm">{Number(p.billing_rate).toFixed(0)} €/h</span>,
    },
    {
      key: 'actions',
      header: '',
      width: '90px',
      sortable: false,
      render: (p: Project) => (
        <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
          <button onClick={() => setTeamProject(p)} aria-label="Gérer l'équipe" className="p-1.5 rounded-lg hover:bg-emerald-50 text-slate-400 hover:text-emerald-600">
            <Users size={13} />
          </button>
          <button onClick={() => setDeleteConfirm(p.project_id)} aria-label="Supprimer" className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-600">
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
          <input
            ref={(ref) => setFileInputRef(ref)}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleImport}
          />
          <Button
            variant="secondary"
            icon={<Upload size={14} />}
            onClick={() => fileInputRef?.click()}
            disabled={isImporting}
          >
            {isImporting ? 'Import...' : 'CSV'}
          </Button>
          <Button icon={<Plus size={14} />} onClick={() => setCreateModal(true)}>{t('projects.new', 'Nouveau projet')}</Button>
        </div>
      </div>

      <Card padding={false}>
        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
            <Loader2 size={16} className="animate-spin" /> Chargement…
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center gap-2 py-16 text-red-500 text-sm">
            <AlertTriangle size={16} /> Impossible de charger les projets.
          </div>
        ) : (
          <PaginatedTable
            data={filtered}
            columns={columns}
            pageSize={25}
            emptyMessage="Aucun projet trouvé."
            onRowClick={(p) => setDetailProject(toModalShape(p))}
          />
        )}
      </Card>

      <CreateProjectModal open={createModal} onClose={() => setCreateModal(false)} />
      <ProjectDetailModal project={detailProject} onClose={() => setDetailProject(null)} />
      <ImportModal open={importModal} onClose={() => setImportModal(false)} entity="projects" />
      {teamProject && (
        <TeamAssignmentModal
          open
          projectId={teamProject.project_id}
          projectName={teamProject.project_name}
          startDate={teamProject.start_date}
          endDate={teamProject.end_date ?? undefined}
          onClose={() => setTeamProject(null)}
          onSave={() => setTeamProject(null)}
        />
      )}
      
      <ConfirmDialog
        open={deleteConfirm !== null}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => {
          if (deleteConfirm !== null) {
            deleteMutation.mutate(deleteConfirm)
            setDeleteConfirm(null)
          }
        }}
        title="Supprimer le projet"
        message="Êtes-vous sûr de vouloir supprimer ce projet ? Cette action est irréversible et supprimera toutes les données associées."
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  )
}

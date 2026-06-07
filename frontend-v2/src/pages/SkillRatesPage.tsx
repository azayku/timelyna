import { useState } from 'react'
import { Plus, Pencil, Trash2, Search, AlertTriangle, Loader2 } from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import Table from '../components/ui/Table'
import { useTranslation } from 'react-i18next'
import { useSkillRates, useCreateSkillRate, useUpdateSkillRate, useDeleteSkillRate } from '../features/skillRates/hooks'
import type { SkillRate } from '../features/skillRates/types'
import { ApiError } from '../lib/apiClient'

const EMPTY_FORM = { skill_name: '', billing_rate: '', description: '' }

export default function SkillRatesPage() {
  const { t } = useTranslation()
  const { data = [], isLoading, isError } = useSkillRates()
  const createMutation = useCreateSkillRate()
  const updateMutation = useUpdateSkillRate()
  const deleteMutation = useDeleteSkillRate()

  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState(EMPTY_FORM)
  const [createError, setCreateError] = useState('')
  const [editTarget, setEditTarget] = useState<SkillRate | null>(null)
  const [editForm, setEditForm] = useState(EMPTY_FORM)
  const [editError, setEditError] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<SkillRate | null>(null)

  const filtered = data.filter(sr =>
    sr.skill_name.toLowerCase().includes(search.toLowerCase()) ||
    (sr.description ?? '').toLowerCase().includes(search.toLowerCase())
  )

  const handleCreate = async () => {
    if (!createForm.skill_name.trim()) { setCreateError('Le nom est obligatoire.'); return }
    const rate = parseFloat(createForm.billing_rate)
    if (isNaN(rate) || rate <= 0) { setCreateError('Le taux doit être un nombre positif.'); return }
    try {
      await createMutation.mutateAsync({
        skill_name: createForm.skill_name.trim(),
        billing_rate: rate,
        description: createForm.description.trim() || undefined,
      })
      setCreateOpen(false)
      setCreateForm(EMPTY_FORM)
      setCreateError('')
    } catch (err) {
      setCreateError(err instanceof ApiError ? err.message : 'Erreur inattendue.')
    }
  }

  const openEdit = (sr: SkillRate) => {
    setEditTarget(sr)
    setEditForm({ skill_name: sr.skill_name, billing_rate: String(sr.billing_rate), description: sr.description ?? '' })
    setEditError('')
  }

  const handleEdit = async () => {
    if (!editTarget) return
    if (!editForm.skill_name.trim()) { setEditError('Le nom est obligatoire.'); return }
    const rate = parseFloat(editForm.billing_rate)
    if (isNaN(rate) || rate <= 0) { setEditError('Le taux doit être un nombre positif.'); return }
    try {
      await updateMutation.mutateAsync({
        id: editTarget.id,
        payload: { skill_name: editForm.skill_name.trim(), billing_rate: rate, description: editForm.description.trim() || undefined },
      })
      setEditTarget(null)
    } catch (err) {
      setEditError(err instanceof ApiError ? err.message : 'Erreur inattendue.')
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    await deleteMutation.mutateAsync(deleteTarget.id)
    setDeleteTarget(null)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 bg-white border border-slate-300 rounded-lg px-3 py-2 w-72">
          <Search size={14} className="text-slate-400" />
          <input type="text" placeholder={t('common.search') + '…'} value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-transparent text-sm text-slate-700 outline-none w-full placeholder-slate-400" />
        </div>
        <Button icon={<Plus size={14} />} onClick={() => { setCreateForm(EMPTY_FORM); setCreateError(''); setCreateOpen(true) }}>
          Nouvelle compétence
        </Button>
      </div>

      <Card padding={false}>
        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
            <Loader2 size={16} className="animate-spin" /> Chargement…
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center gap-2 py-16 text-red-500 text-sm">
            <AlertTriangle size={16} /> Impossible de charger les compétences.
          </div>
        ) : (
          <Table
            columns={[
              { key: 'skill_name', header: 'Compétence', render: (r: SkillRate) => <span className="font-medium text-slate-800">{r.skill_name}</span> },
              { key: 'billing_rate', header: 'Taux horaire', render: (r: SkillRate) => <span className="font-semibold text-indigo-600">{Number(r.billing_rate).toFixed(0)} €/h</span> },
              { key: 'description', header: 'Description', render: (r: SkillRate) => <span className="text-slate-500 text-sm">{r.description ?? <span className="text-slate-300">—</span>}</span> },
              { key: 'created_at', header: t('common.createdAt', 'Créé le'), render: (r: SkillRate) => <span className="text-slate-400 text-xs">{r.created_at ? new Date(r.created_at).toLocaleDateString('fr-FR') : '—'}</span> },
              { key: 'actions', header: '', width: '90px', render: (r: SkillRate) => (
                <div className="flex items-center gap-1">
                  <button onClick={() => openEdit(r)} aria-label="Modifier" className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500" title="Modifier"><Pencil size={13} /></button>
                  <button onClick={() => setDeleteTarget(r)} aria-label="Supprimer" className="p-1.5 rounded-lg hover:bg-red-50 text-red-400" title="Supprimer"><Trash2 size={13} /></button>
                </div>
              )},
            ]}
            data={filtered}
          />
        )}
      </Card>

      {/* Create modal */}
      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Nouvelle compétence" size="md">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Nom *</label>
            <input className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Ex : Frontend React" value={createForm.skill_name}
              onChange={e => setCreateForm(f => ({ ...f, skill_name: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Taux horaire (€) *</label>
            <input type="number" min={0} step={0.01} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Ex : 95" value={createForm.billing_rate}
              onChange={e => setCreateForm(f => ({ ...f, billing_rate: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Description</label>
            <textarea rows={2} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              value={createForm.description} onChange={e => setCreateForm(f => ({ ...f, description: e.target.value }))} />
          </div>
          {createError && <p className="text-xs text-red-500">{createError}</p>}
          <div className="flex gap-3 justify-end pt-2">
            <Button variant="secondary" onClick={() => setCreateOpen(false)}>{t('common.cancel')}</Button>
            <Button onClick={handleCreate} loading={createMutation.isPending}>{t('common.create')}</Button>
          </div>
        </div>
      </Modal>

      {/* Edit modal */}
      <Modal open={!!editTarget} onClose={() => setEditTarget(null)} title="Modifier la compétence" size="md">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Nom *</label>
            <input className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={editForm.skill_name} onChange={e => setEditForm(f => ({ ...f, skill_name: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Taux horaire (€) *</label>
            <input type="number" min={0} step={0.01} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={editForm.billing_rate} onChange={e => setEditForm(f => ({ ...f, billing_rate: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">Description</label>
            <textarea rows={2} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              value={editForm.description} onChange={e => setEditForm(f => ({ ...f, description: e.target.value }))} />
          </div>
          {editError && <p className="text-xs text-red-500">{editError}</p>}
          <div className="flex gap-3 justify-end pt-2">
            <Button variant="secondary" onClick={() => setEditTarget(null)}>{t('common.cancel')}</Button>
            <Button onClick={handleEdit} loading={updateMutation.isPending}>{t('common.save')}</Button>
          </div>
        </div>
      </Modal>

      {/* Delete modal */}
      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Supprimer la compétence" size="sm">
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            Supprimer <span className="font-semibold text-slate-800">{deleteTarget?.skill_name}</span> ? Cette action est irréversible.
          </p>
          <div className="flex gap-3 justify-end pt-2">
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>{t('common.cancel')}</Button>
            <Button variant="danger" onClick={handleDelete} loading={deleteMutation.isPending}>{t('common.delete')}</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

import { useState, useMemo } from 'react'
import { Plus, Search } from 'lucide-react'
import type { ColDef } from 'ag-grid-community'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import DataGrid from '../components/DataGrid'
import { useTranslation } from 'react-i18next'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'
import InvoiceDetailModal from '../components/modals/InvoiceDetailModal'
import { useInvoices, useMarkInvoicePaid } from '../features/invoicing/hooks'
import { useClients } from '../features/clients/hooks'
import type { Invoice } from '../features/invoicing/types'

const fmt = (n: number) =>
  new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n)

const fmtDate = (d: string | null) => {
  if (!d) return null
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

const STATUS_TABS = ['all', 'draft', 'sent', 'overdue', 'paid'] as const
type StatusTab = typeof STATUS_TABS[number]

export default function InvoicesPage() {
  const { t } = useTranslation()
  const [search, setSearch] = useState('')
  const [activeTab, setActiveTab] = useState<StatusTab>('all')
  const [createModal, setCreateModal] = useState(false)
  const [detailInvoice, setDetailInvoice] = useState<Invoice | null>(null)
  
  // Create draft form state
  const [selectedClient, setSelectedClient] = useState('')
  const [period, setPeriod] = useState('')
  const [taxRate, setTaxRate] = useState(20)

  // Fetch data from backend
  const params = activeTab !== 'all' ? { status: activeTab } : undefined
  const { data: invoices = [], isLoading } = useInvoices(params)
  const { data: clients = [] } = useClients()
  const markPaidMutation = useMarkInvoicePaid()

  // Create draft mutation
  const queryClient = useQueryClient()
  const createDraftMutation = useMutation({
    mutationFn: (data: { client_id: number; period_start: string; period_end: string; tax_rate: number }) =>
      apiClient.post('/finance/invoices/draft', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] })
      setCreateModal(false)
      setSelectedClient('')
      setPeriod('')
      setTaxRate(20)
    },
  })

  const handleCreateDraft = () => {
    if (!selectedClient || !period) return
    const [year, month] = period.split('-')
    const periodStart = `${year}-${month}-01`
    const periodEnd = new Date(Number(year), Number(month), 0).toISOString().split('T')[0]
    
    createDraftMutation.mutate({
      client_id: Number(selectedClient),
      period_start: periodStart,
      period_end: periodEnd,
      tax_rate: taxRate,
    })
  }

  // Client map for display
  const clientMap = useMemo(() => {
    const map = new Map<number, string>()
    clients.forEach(c => map.set(c.client_id, c.client_name))
    return map
  }, [clients])

  // Enrich invoices with client names
  const enrichedInvoices = useMemo(() =>
    invoices.map(inv => ({
      ...inv,
      client_name: clientMap.get(inv.client_id) || `Client #${inv.client_id}`,
    })),
    [invoices, clientMap]
  )

  const filtered = enrichedInvoices.filter(i => {
    const matchSearch =
      i.invoice_number.toLowerCase().includes(search.toLowerCase()) ||
      (i.client_name && i.client_name.toLowerCase().includes(search.toLowerCase()))
    return matchSearch
  })

  const handleMarkPaid = (id: number) => {
    markPaidMutation.mutate({ id })
  }

  const handleDownloadPDF = (id: number) => {
    window.open(`/api/v1/finance/invoices/${id}/pdf`, '_blank')
  }

  // Calculate KPIs correctly
  const currentMonth = new Date().getMonth()
  const currentYear = new Date().getFullYear()
  const paidThisMonth = enrichedInvoices
    .filter(i => {
      if (i.status !== 'paid' || !i.paid_at) return false
      const paidDate = new Date(i.paid_at)
      return paidDate.getMonth() === currentMonth && paidDate.getFullYear() === currentYear
    })
    .reduce((s, i) => s + i.total_ttc, 0)

  // Actions cell renderer component
  const ActionsCellRenderer = (props: { data: Invoice & { client_name?: string } }) => {
    return (
      <div className="flex items-center gap-1">
        <button 
          onClick={() => setDetailInvoice(props.data)}
          aria-label="Voir les détails"
          className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500"
          title={t('common.actions')}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
        <button 
          onClick={() => handleDownloadPDF(props.data.invoice_id)}
          aria-label="Télécharger PDF"
          className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500"
          title="Télécharger PDF"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
        </button>
        {(props.data.status === 'sent' || props.data.status === 'overdue') && (
          <button 
            onClick={() => handleMarkPaid(props.data.invoice_id)}
            aria-label="Marquer payée"
            className="p-1.5 rounded-lg hover:bg-emerald-50 text-emerald-600"
            title="Marquer payée"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </button>
        )}
      </div>
    )
  }

  const tabLabel: Record<StatusTab, string> = {
    all: t('common.all'),
    draft: t('common.draft'),
    sent: t('common.sent'),
    overdue: t('common.overdue'),
    paid: t('common.paid'),
  }

  const tabCount = (tab: StatusTab) =>
    tab === 'all' ? enrichedInvoices.length : enrichedInvoices.filter(i => i.status === tab).length

  return (
    <div className="space-y-5">
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: t('invoices.totalBilled'), value: fmt(enrichedInvoices.reduce((s, i) => s + i.total_ttc, 0)), color: 'text-indigo-600' },
          { label: t('invoices.pending'), value: fmt(enrichedInvoices.filter(i => i.status === 'sent').reduce((s, i) => s + i.total_ttc, 0)), color: 'text-amber-600' },
          { label: t('invoices.overdue'), value: fmt(enrichedInvoices.filter(i => i.status === 'overdue').reduce((s, i) => s + i.total_ttc, 0)), color: 'text-red-600' },
          { label: t('invoices.paidThisMonth'), value: fmt(paidThisMonth), color: 'text-emerald-600' },
        ].map(kpi => (
          <Card key={kpi.label}>
            <p className="text-xs text-slate-400 mb-1">{kpi.label}</p>
            <p className={`text-xl font-bold ${kpi.color}`}>{kpi.value}</p>
          </Card>
        ))}
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2 bg-white border border-slate-300 rounded-lg px-3 py-2 w-72">
          <Search size={14} className="text-slate-400" />
          <input
            type="text"
            placeholder={t('common.search') + '…'}
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="bg-transparent text-sm text-slate-700 outline-none w-full placeholder-slate-400"
          />
        </div>
        <Button icon={<Plus size={14} />} onClick={() => setCreateModal(true)}>
          {t('invoices.new')}
        </Button>
      </div>

      {/* Status tabs */}
      <div className="flex gap-1 bg-slate-100 rounded-lg p-1 w-fit">
        {STATUS_TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === tab
                ? 'bg-white text-slate-800 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tabLabel[tab]}
            <span className={`inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-semibold ${
              activeTab === tab ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-200 text-slate-500'
            }`}>
              {tabCount(tab)}
            </span>
          </button>
        ))}
      </div>

      {/* Table */}
      <Card padding={false}>
        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
            <span className="animate-spin">⏳</span> Chargement…
          </div>
        ) : (
        <DataGrid
          rowData={filtered}
          columnDefs={useMemo((): ColDef[] => [
            { field: 'invoice_number', headerName: t('invoices.number'), cellRenderer: (p: { data: Invoice & { client_name?: string } }) => `<span class="font-mono text-sm font-semibold text-slate-800">${p.data.invoice_number}</span>` },
            { field: 'client_name', headerName: t('common.client') },
            { 
              field: 'period_start', 
              headerName: t('common.period'),
              valueFormatter: (p: { data: Invoice }) => {
                const start = new Date(p.data.period_start)
                return `${start.toLocaleDateString('fr-FR', { month: 'short', year: 'numeric' })}`
              }
            },
            { field: 'subtotal_ht', headerName: t('invoices.amount'), valueFormatter: (p: { value: number }) => fmt(p.value) },
            { field: 'total_ttc', headerName: t('invoices.total'), valueFormatter: (p: { value: number }) => fmt(p.value) },
            { field: 'due_date', headerName: t('invoices.dueDate'), valueFormatter: (p: { value: string | null }) => fmtDate(p.value) ?? '' },
            { field: 'status', headerName: t('common.status'), cellRenderer: (p: { data: Invoice }) => `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${p.data.status === 'paid' ? 'bg-emerald-100 text-emerald-700' : p.data.status === 'overdue' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'}">${p.data.status}</span>` },
            { 
              headerName: '', 
              width: 120, 
              sortable: false, 
              filter: false, 
              cellRenderer: ActionsCellRenderer
            },
          ], [t])}
          onRowClicked={(row) => setDetailInvoice(row)}
          />
        )}
      </Card>

      {/* Create modal */}
      <Modal open={createModal} onClose={() => setCreateModal(false)} title={t('invoices.new')} size="md">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1.5">{t('common.client')} *</label>
            <select 
              value={selectedClient}
              onChange={e => setSelectedClient(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">— {t('common.select')} —</option>
              {clients.map(c => (
                <option key={c.client_id} value={c.client_id}>{c.client_name}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1.5">{t('common.period')} *</label>
              <input
                type="month"
                value={period}
                onChange={e => setPeriod(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1.5">{t('invoices.taxRate')}</label>
              <input
                type="number"
                value={taxRate}
                onChange={e => setTaxRate(Number(e.target.value))}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <Button variant="secondary" onClick={() => setCreateModal(false)} disabled={createDraftMutation.isPending}>
              {t('common.cancel')}
            </Button>
            <Button 
              onClick={handleCreateDraft} 
              disabled={!selectedClient || !period || createDraftMutation.isPending}
              loading={createDraftMutation.isPending}
            >
              {t('invoices.createDraft')}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Detail modal */}
      {detailInvoice && (
        <InvoiceDetailModal
          invoice={{
            id: detailInvoice.invoice_id,
            number: detailInvoice.invoice_number,
            client: detailInvoice.client_name ?? `Client #${detailInvoice.client_id}`,
            period: `${new Date(detailInvoice.period_start).toLocaleDateString('fr-FR', { month: 'short', year: 'numeric' })} – ${new Date(detailInvoice.period_end).toLocaleDateString('fr-FR', { month: 'short', year: 'numeric' })}`,
            subtotal_ht: detailInvoice.subtotal_ht,
            tax_amount: detailInvoice.tax_amount,
            total_ttc: detailInvoice.total_ttc,
            status: detailInvoice.status,
            due: detailInvoice.due_date,
            created: detailInvoice.created_at,
          }}
          open={!!detailInvoice}
          onClose={() => setDetailInvoice(null)}
          onMarkPaid={id => { handleMarkPaid(id); setDetailInvoice(null) }}
        />
      )}
    </div>
  )
}

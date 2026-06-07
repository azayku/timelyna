import { useState, useMemo } from 'react'
import { Download, Search, Clock, TrendingUp, Car, Moon, Loader2, AlertTriangle } from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Table from '../components/ui/Table'
import { useTranslation } from 'react-i18next'
import { useHoursReport } from '../features/reporting/hooks'
import { useEmployees } from '../features/employees/hooks'
import { useProjects } from '../features/projects/hooks'
import type { HoursReportParams } from '../features/reporting/types'
import { useAuthStore } from '../lib/authStore'
import PdfExportModal from '../components/modals/PdfExportModal'

export default function HoursReportPage() {
  const { t } = useTranslation()
  const isAdmin = useAuthStore(s => s.user?.role === 'admin')
  const today = new Date().toISOString().split('T')[0]
  const firstOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0]

  const [dateFrom, setDateFrom] = useState(firstOfMonth)
  const [dateTo, setDateTo] = useState(today)
  const [employeeId, setEmployeeId] = useState<string>('')
  const [projectId, setProjectId] = useState<string>('')
  const [showPdfModal, setShowPdfModal] = useState(false)
  const [appliedParams, setAppliedParams] = useState<HoursReportParams>({
    date_from: firstOfMonth,
    date_to: today,
  })

  const { data: rows = [], isLoading, isError } = useHoursReport(appliedParams)
  const { data: employees = [] } = useEmployees({ enabled: isAdmin })
  const { data: projects = [] } = useProjects({ enabled: isAdmin })

  const TYPE_ICONS: Record<string, React.ReactNode> = {
    normal: <Clock size={12} className="text-slate-500" />,
    overtime: <TrendingUp size={12} className="text-amber-500" />,
    travel: <Car size={12} className="text-blue-500" />,
    night: <Moon size={12} className="text-purple-500" />,
  }

  const TYPE_LABELS: Record<string, string> = {
    normal: t('hoursReport.normal'),
    overtime: t('hoursReport.overtime'),
    travel: t('hoursReport.travel'),
    night: t('hoursReport.night'),
  }

  const filteredRows = useMemo(() => {
    let result = rows
    if (employeeId) {
      result = result.filter(r => String(r.employee_id) === employeeId)
    }
    if (projectId) {
      result = result.filter(r => String(r.project_id) === projectId)
    }
    return result
  }, [rows, employeeId, projectId])

  const totals = useMemo(() => ({
    normal: filteredRows.reduce((s, r) => s + Number(r.normal_hours), 0),
    overtime: filteredRows.reduce((s, r) => s + Number(r.overtime_hours), 0),
    travel: filteredRows.reduce((s, r) => s + Number(r.travel_hours), 0),
    night: filteredRows.reduce((s, r) => s + Number(r.night_hours), 0),
    total: filteredRows.reduce((s, r) => s + Number(r.total_hours), 0),
  }), [filteredRows])

  function handleApply() {
    setAppliedParams({ date_from: dateFrom, date_to: dateTo })
  }

  function handleExport() {
    const csv = [
      ['Date', 'Employé', 'Projet', 'Type', 'Heures normales', 'Heures sup.', 'Heures déplacement', 'Heures nuit', 'Total'],
      ...filteredRows.map(row => [
        row.work_date,
        row.employee_name,
        row.project_name,
        TYPE_LABELS[row.entry_type] ?? row.entry_type,
        row.normal_hours,
        row.overtime_hours,
        row.travel_hours,
        row.night_hours,
        row.total_hours,
      ]),
    ].map(row => row.join(',')).join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `rapport-heures-${dateFrom}-${dateTo}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-5">
      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { label: t('hoursReport.normal'), value: totals.normal, icon: <Clock size={18} />, bg: 'bg-slate-100 dark:bg-slate-700', text: 'text-slate-700 dark:text-slate-200' },
          { label: t('hoursReport.overtime'), value: totals.overtime, icon: <TrendingUp size={18} />, bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-400' },
          { label: t('hoursReport.travel'), value: totals.travel, icon: <Car size={18} />, bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-400' },
          { label: t('hoursReport.night'), value: totals.night, icon: <Moon size={18} />, bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-400' },
          { label: t('common.total'), value: totals.total, icon: <Clock size={18} />, bg: 'bg-indigo-100 dark:bg-indigo-900/30', text: 'text-indigo-700 dark:text-indigo-400' },
        ].map(kpi => (
          <Card key={kpi.label}>
            <div className={`w-9 h-9 rounded-lg ${kpi.bg} ${kpi.text} flex items-center justify-center mb-3`}>{kpi.icon}</div>
            <p className="text-xs text-slate-400 dark:text-slate-500 mb-1">{kpi.label}</p>
            <p className={`text-2xl font-bold ${kpi.text}`}>
              {isLoading ? '…' : Number(kpi.value).toFixed(1)}
              <span className="text-sm font-normal text-slate-400 dark:text-slate-500 ml-1">h</span>
            </p>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <Card>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">{t('common.from')}</label>
            <input
              type="date"
              value={dateFrom}
              onChange={e => setDateFrom(e.target.value)}
              className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">{t('common.to')}</label>
            <input
              type="date"
              value={dateTo}
              onChange={e => setDateTo(e.target.value)}
              className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">{t('common.employee')}</label>
            <select
              value={employeeId}
              onChange={e => setEmployeeId(e.target.value)}
              className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Tous</option>
              {employees.map(e => (
                <option key={e.employee_id} value={e.employee_id}>
                  {e.first_name} {e.last_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">{t('common.project')}</label>
            <select
              value={projectId}
              onChange={e => setProjectId(e.target.value)}
              className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Tous</option>
              {projects.map(p => (
                <option key={p.project_id} value={p.project_id}>
                  {p.project_name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <Button className="w-full justify-center" icon={<Search size={14} />} onClick={handleApply}>
              {t('common.apply')}
            </Button>
          </div>
        </div>
      </Card>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={28} className="animate-spin text-indigo-500" />
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400">
          <AlertTriangle size={20} className="flex-shrink-0" />
          <span className="text-sm">{t('common.error')}</span>
        </div>
      )}

      {/* Table */}
      {!isLoading && !isError && (
        <Card padding={false}>
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-700">
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
              {filteredRows.length} {t('hoursReport.entries')}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                icon={<Download size={13} />}
                onClick={() => setShowPdfModal(true)}
                disabled={filteredRows.length === 0}
              >
                PDF
              </Button>
              <Button
                variant="secondary"
                size="sm"
                icon={<Download size={13} />}
                onClick={handleExport}
                disabled={filteredRows.length === 0}
              >
                CSV
              </Button>
            </div>
          </div>

          {filteredRows.length === 0 ? (
            <p className="text-sm text-slate-400 dark:text-slate-500 text-center py-10">{t('common.noData')}</p>
          ) : (
            <Table
              columns={[
                { key: 'work_date', header: t('common.date'), render: row => row.work_date },
                {
                  key: 'employee_name',
                  header: t('common.employee'),
                  render: row => <span className="font-medium text-slate-800 dark:text-slate-100">{row.employee_name}</span>,
                },
                {
                  key: 'project_name',
                  header: t('common.project'),
                  render: row => <span className="text-slate-500 dark:text-slate-400">{row.project_name}</span>,
                },
                {
                  key: 'entry_type',
                  header: t('common.type'),
                  render: row => (
                    <span className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300">
                      {TYPE_ICONS[row.entry_type]} {TYPE_LABELS[row.entry_type] ?? row.entry_type}
                    </span>
                  ),
                },
                {
                  key: 'normal_hours',
                  header: t('hoursReport.normal'),
                  render: row => row.normal_hours ? `${row.normal_hours}h` : <span className="text-slate-300 dark:text-slate-600">—</span>,
                },
                {
                  key: 'overtime_hours',
                  header: t('hoursReport.overtime'),
                  render: row => row.overtime_hours
                    ? <span className="text-amber-600 dark:text-amber-400 font-medium">{row.overtime_hours}h</span>
                    : <span className="text-slate-300 dark:text-slate-600">—</span>,
                },
                {
                  key: 'travel_hours',
                  header: t('hoursReport.travel'),
                  render: row => row.travel_hours
                    ? <span className="text-blue-600 dark:text-blue-400 font-medium">{row.travel_hours}h</span>
                    : <span className="text-slate-300 dark:text-slate-600">—</span>,
                },
                {
                  key: 'night_hours',
                  header: t('hoursReport.night'),
                  render: row => row.night_hours
                    ? <span className="text-purple-600 dark:text-purple-400 font-medium">{row.night_hours}h</span>
                    : <span className="text-slate-300 dark:text-slate-600">—</span>,
                },
                {
                  key: 'total_hours',
                  header: t('common.total'),
                  render: row => <span className="font-bold text-slate-800 dark:text-slate-100">{row.total_hours}h</span>,
                },
              ]}
              data={filteredRows}
            />
          )}

          {filteredRows.length > 0 && (
            <div className="flex items-center gap-8 px-5 py-3 bg-slate-50 dark:bg-slate-700/50 border-t border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-600 dark:text-slate-300 flex-wrap">
              <span>Total ({filteredRows.length})</span>
              <span>{totals.normal.toFixed(1)}h {t('hoursReport.normal').toLowerCase()}</span>
              <span className="text-amber-600 dark:text-amber-400">{totals.overtime.toFixed(1)}h {t('hoursReport.overtime').toLowerCase()}</span>
              <span className="text-blue-600 dark:text-blue-400">{totals.travel.toFixed(1)}h {t('hoursReport.travel').toLowerCase()}</span>
              <span className="text-purple-600 dark:text-purple-400">{totals.night.toFixed(1)}h {t('hoursReport.night').toLowerCase()}</span>
              <span className="ml-auto text-slate-800 dark:text-slate-100 text-sm">{totals.total.toFixed(1)}h {t('common.total').toLowerCase()}</span>
            </div>
          )}
        </Card>
      )}
      <PdfExportModal
        open={showPdfModal}
        onClose={() => setShowPdfModal(false)}
        mode="hours-report"
        defaultDateFrom={appliedParams.date_from}
        defaultDateTo={appliedParams.date_to}
      />
    </div>
  )
}

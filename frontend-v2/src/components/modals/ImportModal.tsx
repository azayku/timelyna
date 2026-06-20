import { useState, useRef, useCallback } from 'react'
import * as XLSX from 'xlsx'
import { Upload, Download, CheckCircle, XCircle, AlertTriangle, FileSpreadsheet, RefreshCw } from 'lucide-react'
import Modal from '../ui/Modal'
import Button from '../ui/Button'

// ── Column definitions per entity ──────────────────────────────────────────

type EntityType = 'users' | 'clients' | 'projects'

interface ColDef {
  key: string
  label: string
  required: boolean
  example: string
  validate?: (v: string) => string | null // returns error message or null
}

const COLUMNS: Record<EntityType, ColDef[]> = {
  users: [
    { key: 'first_name', label: 'Prénom', required: true, example: 'Sophie' },
    { key: 'last_name', label: 'Nom', required: true, example: 'Martin' },
    { key: 'email', label: 'Email', required: true, example: 'sophie.martin@company.com',
      validate: v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? null : 'Email invalide' },
    { key: 'role', label: 'Rôle', required: true, example: 'employee',
      validate: v => ['employee', 'manager', 'admin', 'finance'].includes(v.toLowerCase()) ? null : 'Rôle invalide (employee/manager/admin/finance)' },
    { key: 'birth_date', label: 'Date de naissance', required: true, example: '1992-03-15',
      validate: v => /^\d{4}-\d{2}-\d{2}$/.test(v) ? null : 'Format YYYY-MM-DD requis' },
    { key: 'address', label: 'Adresse', required: true, example: '12 Rue de la Paix, Paris' },
    { key: 'phone', label: 'Téléphone', required: false, example: '+33 6 12 34 56 78' },
  ],
  clients: [
    { key: 'name', label: 'Nom du client', required: true, example: 'Acme Corp' },
    { key: 'email', label: 'Email facturation', required: true, example: 'billing@acme.com',
      validate: v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? null : 'Email invalide' },
    { key: 'hourly_rate', label: 'Taux horaire (€)', required: true, example: '120',
      validate: v => !isNaN(Number(v)) && Number(v) > 0 ? null : 'Nombre positif requis' },
    { key: 'currency', label: 'Devise', required: false, example: 'EUR',
      validate: v => !v || ['EUR', 'USD', 'GBP', 'CHF', 'MAD'].includes(v.toUpperCase()) ? null : 'Devise non reconnue' },
  ],
  projects: [
    { key: 'name', label: 'Nom du projet', required: true, example: 'Website Redesign' },
    { key: 'client', label: 'Client', required: true, example: 'Acme Corp' },
    { key: 'start_date', label: 'Date début', required: true, example: '2026-01-01',
      validate: v => /^\d{4}-\d{2}-\d{2}$/.test(v) ? null : 'Format YYYY-MM-DD requis' },
    { key: 'end_date', label: 'Date fin', required: false, example: '2026-06-30',
      validate: v => !v || /^\d{4}-\d{2}-\d{2}$/.test(v) ? null : 'Format YYYY-MM-DD requis' },
    { key: 'budget_hours', label: 'Budget (heures)', required: false, example: '500',
      validate: v => !v || (!isNaN(Number(v)) && Number(v) >= 0) ? null : 'Nombre positif requis' },
    { key: 'billing_rate', label: 'Taux horaire (€)', required: false, example: '120',
      validate: v => !v || (!isNaN(Number(v)) && Number(v) >= 0) ? null : 'Nombre positif requis' },
    { key: 'status', label: 'Statut', required: false, example: 'planning',
      validate: v => !v || ['draft', 'planning', 'active'].includes(v.toLowerCase()) ? null : 'Statut invalide (draft/planning/active)' },
  ],
}

const ENTITY_LABELS: Record<EntityType, string> = {
  users: 'Employés',
  clients: 'Clients',
  projects: 'Projets',
}

// ── Row validation ──────────────────────────────────────────────────────────

interface ParsedRow {
  index: number
  data: Record<string, string>
  errors: string[]
  valid: boolean
}

function validateRows(rows: Record<string, string>[], cols: ColDef[]): ParsedRow[] {
  return rows.map((row, i) => {
    const errors: string[] = []
    for (const col of cols) {
      const val = (row[col.key] ?? '').toString().trim()
      if (col.required && !val) {
        errors.push(`"${col.label}" est requis`)
      } else if (val && col.validate) {
        const err = col.validate(val)
        if (err) errors.push(`"${col.label}" : ${err}`)
      }
    }
    return { index: i + 1, data: row, errors, valid: errors.length === 0 }
  })
}

// ── Template generator ──────────────────────────────────────────────────────

function downloadTemplate(entity: EntityType) {
  const cols = COLUMNS[entity]
  const headers = cols.map(c => c.label + (c.required ? ' *' : ''))
  const example = cols.map(c => c.example)
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.aoa_to_sheet([headers, example])
  ws['!cols'] = cols.map(() => ({ wch: 22 }))
  // Style header row
  const headerStyle = { font: { bold: true, color: { rgb: 'FFFFFF' } }, fill: { fgColor: { rgb: '4F46E5' } } }
  for (let c = 0; c < cols.length; c++) {
    const cell = XLSX.utils.encode_cell({ r: 0, c })
    if (ws[cell]) ws[cell].s = headerStyle
  }
  XLSX.utils.book_append_sheet(wb, ws, ENTITY_LABELS[entity])
  XLSX.writeFile(wb, `template_${entity}_timelyna.xlsx`, { bookType: 'xlsx', cellStyles: true })
}

// ── Main component ──────────────────────────────────────────────────────────

interface Props {
  open: boolean
  onClose: () => void
  entity: EntityType
}

type Step = 'upload' | 'preview' | 'done'

export default function ImportModal({ open, onClose, entity }: Props) {
  const [step, setStep] = useState<Step>('upload')
  const [dragging, setDragging] = useState(false)
  const [fileName, setFileName] = useState('')
  const [rows, setRows] = useState<ParsedRow[]>([])
  const [importing, setImporting] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const cols = COLUMNS[entity]

  const reset = () => { setStep('upload'); setRows([]); setFileName('') }

  const parseFile = (file: File) => {
    setFileName(file.name)
    const reader = new FileReader()
    reader.onload = (e) => {
      const data = new Uint8Array(e.target?.result as ArrayBuffer)
      const wb = XLSX.read(data, { type: 'array' })
      const ws = wb.Sheets[wb.SheetNames[0]]
      const raw: string[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' }) as string[][]
      if (raw.length < 2) return

      // Map header row to column keys
      const headerRow = raw[0].map(h => String(h).replace(' *', '').trim())
      const colKeyMap: Record<string, string> = {}
      for (const col of cols) {
        const idx = headerRow.findIndex(h => h.toLowerCase() === col.label.toLowerCase())
        if (idx >= 0) colKeyMap[idx] = col.key
      }

      const parsed = raw.slice(1).filter(r => r.some(c => c !== '')).map(r => {
        const obj: Record<string, string> = {}
        for (const [idxStr, key] of Object.entries(colKeyMap)) {
          obj[key] = String(r[Number(idxStr)] ?? '').trim()
        }
        return obj
      })

      setRows(validateRows(parsed, cols))
      setStep('preview')
    }
    reader.readAsArrayBuffer(file)
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls') || file.name.endsWith('.csv'))) {
      parseFile(file)
    }
  }, [cols])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) parseFile(file)
  }

  const handleImport = async () => {
    setImporting(true)
    // Simulate API call
    await new Promise(r => setTimeout(r, 1500))
    setImporting(false)
    setStep('done')
  }

  const validRows = rows.filter(r => r.valid)
  const invalidRows = rows.filter(r => !r.valid)

  return (
    <Modal open={open} onClose={() => { onClose(); reset() }} title={`Importer des ${ENTITY_LABELS[entity].toLowerCase()}`} size="xl">
      <div className="space-y-5">

        {/* ── Step: Upload ── */}
        {step === 'upload' && (
          <>
            {/* Template download */}
            <div className="flex items-start gap-3 p-4 bg-indigo-50 border border-indigo-100 rounded-xl">
              <FileSpreadsheet size={18} className="text-indigo-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-indigo-800">Téléchargez d'abord le modèle Excel</p>
                <p className="text-xs text-indigo-600 mt-0.5">
                  Le fichier contient les colonnes requises avec des exemples. Les colonnes marquées * sont obligatoires.
                </p>
              </div>
              <button
                onClick={() => downloadTemplate(entity)}
                className="flex items-center gap-2 px-3 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 flex-shrink-0"
              >
                <Download size={13} /> Télécharger le modèle
              </button>
            </div>

            {/* Columns info */}
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Colonnes attendues</p>
              <div className="flex flex-wrap gap-2">
                {cols.map(col => (
                  <span key={col.key} className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                    col.required ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-600'
                  }`}>
                    {col.label}
                    {col.required && <span className="text-red-500 font-bold">*</span>}
                  </span>
                ))}
              </div>
            </div>

            {/* Drop zone */}
            <div
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${
                dragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 hover:border-indigo-400 hover:bg-slate-50'
              }`}
            >
              <Upload size={32} className={`mx-auto mb-3 ${dragging ? 'text-indigo-500' : 'text-slate-400'}`} />
              <p className="text-sm font-semibold text-slate-700">
                {dragging ? 'Déposez le fichier ici' : 'Glissez-déposez votre fichier Excel'}
              </p>
              <p className="text-xs text-slate-400 mt-1">ou cliquez pour parcourir · .xlsx, .xls, .csv</p>
              <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" className="hidden" onChange={handleFileChange} />
            </div>
          </>
        )}

        {/* ── Step: Preview ── */}
        {step === 'preview' && (
          <>
            {/* Summary */}
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2 px-3 py-2 bg-slate-100 rounded-lg text-sm">
                <FileSpreadsheet size={14} className="text-slate-500" />
                <span className="font-medium text-slate-700">{fileName}</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-2 bg-emerald-100 rounded-lg text-sm text-emerald-700 font-medium">
                <CheckCircle size={14} /> {validRows.length} ligne{validRows.length > 1 ? 's' : ''} valide{validRows.length > 1 ? 's' : ''}
              </div>
              {invalidRows.length > 0 && (
                <div className="flex items-center gap-2 px-3 py-2 bg-red-100 rounded-lg text-sm text-red-700 font-medium">
                  <XCircle size={14} /> {invalidRows.length} erreur{invalidRows.length > 1 ? 's' : ''}
                </div>
              )}
              <button onClick={reset} className="ml-auto flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700">
                <RefreshCw size={12} /> Changer de fichier
              </button>
            </div>

            {/* Errors summary */}
            {invalidRows.length > 0 && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl space-y-1.5 max-h-32 overflow-y-auto">
                {invalidRows.map(row => (
                  <div key={row.index} className="text-xs text-red-700">
                    <span className="font-semibold">Ligne {row.index} :</span> {row.errors.join(' · ')}
                  </div>
                ))}
              </div>
            )}

            {/* Data preview table */}
            <div className="overflow-x-auto max-h-72 overflow-y-auto border border-slate-200 rounded-xl">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-3 py-2.5 text-left text-slate-500 font-semibold w-10">#</th>
                    {cols.map(col => (
                      <th key={col.key} className="px-3 py-2.5 text-left text-slate-500 font-semibold whitespace-nowrap">
                        {col.label}
                      </th>
                    ))}
                    <th className="px-3 py-2.5 text-center text-slate-500 font-semibold">Statut</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {rows.map(row => (
                    <tr key={row.index} className={row.valid ? 'hover:bg-slate-50' : 'bg-red-50/60'}>
                      <td className="px-3 py-2 text-slate-400">{row.index}</td>
                      {cols.map(col => (
                        <td key={col.key} className="px-3 py-2 text-slate-700 max-w-[160px] truncate" title={row.data[col.key]}>
                          {row.data[col.key] || <span className="text-slate-300">—</span>}
                        </td>
                      ))}
                      <td className="px-3 py-2 text-center">
                        {row.valid ? (
                          <CheckCircle size={14} className="text-emerald-500 mx-auto" />
                        ) : (
                          <div className="flex items-center justify-center gap-1">
                            <XCircle size={14} className="text-red-500" />
                            <span className="text-red-600 text-[10px]">{row.errors.length} err.</span>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {invalidRows.length > 0 && (
              <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-700">
                <AlertTriangle size={14} className="mt-0.5 flex-shrink-0" />
                Seules les {validRows.length} lignes valides seront importées. Les {invalidRows.length} lignes en erreur seront ignorées.
              </div>
            )}
          </>
        )}

        {/* ── Step: Done ── */}
        {step === 'done' && (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle size={32} className="text-emerald-600" />
            </div>
            <h3 className="text-lg font-bold text-slate-800 mb-1">Import réussi !</h3>
            <p className="text-sm text-slate-500">
              <span className="font-semibold text-emerald-600">{validRows.length} {ENTITY_LABELS[entity].toLowerCase()}</span> ont été importé{validRows.length > 1 ? 's' : ''} avec succès.
            </p>
            {invalidRows.length > 0 && (
              <p className="text-xs text-amber-600 mt-1">{invalidRows.length} ligne{invalidRows.length > 1 ? 's' : ''} ignorée{invalidRows.length > 1 ? 's' : ''} (erreurs de validation)</p>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-100">
          <button onClick={() => { onClose(); reset() }} className="px-4 py-2 text-sm font-medium text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50">
            {step === 'done' ? 'Fermer' : 'Annuler'}
          </button>

          {step === 'preview' && validRows.length > 0 && (
            <Button onClick={handleImport} loading={importing} icon={<Upload size={14} />}>
              {importing ? 'Import en cours…' : `Importer ${validRows.length} ligne${validRows.length > 1 ? 's' : ''}`}
            </Button>
          )}

          {step === 'done' && (
            <Button onClick={() => { onClose(); reset() }} icon={<CheckCircle size={14} />}>
              Terminé
            </Button>
          )}
        </div>
      </div>
    </Modal>
  )
}

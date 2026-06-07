import { useCallback, useRef } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import type {
  ColDef,
  GridReadyEvent,
  FilterChangedEvent,
  CellClickedEvent,
} from 'ag-grid-community'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-quartz.css'
import { useThemeStore } from '../lib/themeStore'

ModuleRegistry.registerModules([AllCommunityModule])

export interface DataGridProps<T> {
  rowData: T[]
  columnDefs: ColDef<T>[]
  storageKey?: string
  darkMode?: boolean
  height?: string | number
  onRowClicked?: (row: T) => void
  onCellClicked?: (params: CellClickedEvent<T>) => void
  pagination?: boolean
  pageSize?: number
}

const defaultColDef: ColDef = {
  sortable: true,
  filter: true,
  resizable: true,
  floatingFilter: false,
  minWidth: 80,
}

export default function DataGrid<T>({
  rowData,
  columnDefs,
  storageKey,
  darkMode,
  height = 520,
  onRowClicked,
  onCellClicked,
  pagination = true,
  pageSize = 25,
}: DataGridProps<T>) {
  const gridRef = useRef<AgGridReact<T>>(null)
  const storeDark = useThemeStore((s) => s.dark)
  const isDark = darkMode ?? storeDark

  const onGridReady = useCallback((params: GridReadyEvent) => {
    if (storageKey) {
      const saved = localStorage.getItem(`ag-filter-${storageKey}`)
      if (saved) {
        try { params.api.setFilterModel(JSON.parse(saved)) } catch { /* ignore */ }
      }
    }
    params.api.sizeColumnsToFit()
  }, [storageKey])

  const onFilterChanged = useCallback((params: FilterChangedEvent) => {
    if (!storageKey) return
    localStorage.setItem(`ag-filter-${storageKey}`, JSON.stringify(params.api.getFilterModel()))
  }, [storageKey])

  const heightPx = typeof height === 'number' ? `${height}px` : height
  const themeClass = isDark ? 'ag-theme-quartz-dark' : 'ag-theme-quartz'

  return (
    <div className={themeClass} style={{ height: heightPx, width: '100%' }}>
      <AgGridReact<T>
        ref={gridRef}
        rowData={rowData}
        columnDefs={columnDefs}
        defaultColDef={defaultColDef}
        pagination={pagination}
        paginationPageSize={pageSize}
        paginationPageSizeSelector={[10, 25, 50, 100]}
        onGridReady={onGridReady}
        onFilterChanged={onFilterChanged}
        onRowClicked={onRowClicked ? (e) => e.data && onRowClicked(e.data) : undefined}
        onCellClicked={onCellClicked}
        suppressCellFocus
      />
    </div>
  )
}

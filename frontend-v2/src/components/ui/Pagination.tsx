import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  page: number
  totalPages: number
  totalItems: number
  itemsPerPage: number
  onPageChange: (page: number) => void
  onPageSizeChange?: (size: number) => void
  pageSizeOptions?: number[]
  itemLabel?: string
}

export default function Pagination({
  page,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 15, 20, 50],
  itemLabel = 'résultat',
}: PaginationProps) {
  const safePage = Math.min(Math.max(1, page), Math.max(1, totalPages))
  const start = totalItems === 0 ? 0 : (safePage - 1) * itemsPerPage + 1
  const end = Math.min(safePage * itemsPerPage, totalItems)

  return (
    <div className="flex items-center justify-between bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 px-4 py-3">
      <div className="flex items-center gap-3 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
        <span>
          {totalItems === 0
            ? `0 ${itemLabel}`
            : `${start}–${end} sur ${totalItems}`}
        </span>
        {onPageSizeChange && (
          <label className="flex items-center gap-1.5">
            <span>Par page :</span>
            <select
              value={itemsPerPage}
              onChange={e => { onPageSizeChange(Number(e.target.value)); onPageChange(1) }}
              className="border border-slate-200 dark:border-slate-600 rounded-md px-2 py-1 text-xs sm:text-sm bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {pageSizeOptions.map(n => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </label>
        )}
      </div>

      <div className="flex items-center gap-1.5">
        <button
          onClick={() => onPageChange(Math.max(1, safePage - 1))}
          disabled={safePage <= 1}
          className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          aria-label="Page précédente"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="px-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400 whitespace-nowrap">
          Page {safePage} / {Math.max(1, totalPages)}
        </span>
        <button
          onClick={() => onPageChange(Math.min(totalPages, safePage + 1))}
          disabled={safePage >= totalPages}
          className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          aria-label="Page suivante"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}

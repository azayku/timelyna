/**
 * Format a date using Intl.DateTimeFormat.
 * @param d - ISO string or Date object
 * @param locale - BCP 47 locale tag (default: 'fr-FR')
 */
export function formatDate(d: string | Date, locale = 'fr-FR'): string {
  return new Intl.DateTimeFormat(locale, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(d))
}

/**
 * Format a number as currency using Intl.NumberFormat.
 * @param n - numeric value
 * @param currency - ISO 4217 currency code (default: 'EUR')
 * @param locale - BCP 47 locale tag (default: 'fr-FR')
 */
export function formatCurrency(n: number, currency = 'EUR', locale = 'fr-FR'): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(n)
}

/** Format decimal hours to "Xh" or "Xh30" */
export function formatHours(h: number): string {
  const hours = Math.floor(h)
  const mins = Math.round((h - hours) * 60)
  if (mins === 0) return `${hours}h`
  return `${hours}h${String(mins).padStart(2, '0')}`
}

/** Get current ISO week string like "2025-W12" */
export function getCurrentWeek(): string {
  return getWeekFromDate(new Date())
}

/** Get ISO week string from a specific date */
export function getWeekFromDate(date: Date): string {
  const jan4 = new Date(date.getFullYear(), 0, 4)
  const dayOfYear = Math.floor((date.getTime() - new Date(date.getFullYear(), 0, 0).getTime()) / 86400000)
  const weekNum = Math.ceil((dayOfYear + jan4.getDay()) / 7)
  return `${date.getFullYear()}-W${String(weekNum).padStart(2, '0')}`
}

/** Get Monday date from ISO week string */
export function weekToMonday(week: string): Date {
  const [year, w] = week.split('-W').map(Number)
  const jan4 = new Date(year, 0, 4)
  const monday = new Date(jan4)
  monday.setDate(jan4.getDate() - jan4.getDay() + 1 + (w - 1) * 7)
  return monday
}

/** Get array of 7 dates (Mon–Sun) for a week string */
export function weekDates(week: string): Date[] {
  const monday = weekToMonday(week)
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    return d
  })
}

/** Format Date to YYYY-MM-DD */
export function toISODate(d: Date): string {
  return d.toISOString().split('T')[0]
}

/** Navigate week: direction +1 or -1 */
export function shiftWeek(week: string, direction: 1 | -1): string {
  const monday = weekToMonday(week)
  monday.setDate(monday.getDate() + direction * 7)
  const jan4 = new Date(monday.getFullYear(), 0, 4)
  const dayOfYear = Math.floor((monday.getTime() - new Date(monday.getFullYear(), 0, 0).getTime()) / 86400000)
  const weekNum = Math.ceil((dayOfYear + jan4.getDay()) / 7)
  return `${monday.getFullYear()}-W${String(weekNum).padStart(2, '0')}`
}

/** Map status to Tailwind color classes */
export function statusColor(status: string): string {
  const map: Record<string, string> = {
    draft: 'bg-slate-100 text-slate-700',
    submitted: 'bg-amber-100 text-amber-800',
    approved: 'bg-emerald-100 text-emerald-800',
    rejected: 'bg-red-100 text-red-800',
    invoiced: 'bg-blue-100 text-blue-800',
    pending: 'bg-amber-100 text-amber-800',
    ready: 'bg-emerald-100 text-emerald-800',
    sent: 'bg-blue-100 text-blue-800',
    paid: 'bg-purple-100 text-purple-800',
    planning: 'bg-sky-100 text-sky-700',
    active: 'bg-emerald-100 text-emerald-800',
    paused: 'bg-orange-100 text-orange-700',
    completed: 'bg-indigo-100 text-indigo-700',
    cancelled: 'bg-red-100 text-red-700',
    inactive: 'bg-slate-100 text-slate-500',
  }
  return map[status] ?? 'bg-slate-100 text-slate-700'
}

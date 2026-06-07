import { useState, useMemo, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Loader2, AlertTriangle, LayoutGrid, List, Briefcase, Plane, HeartPulse, CalendarOff } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'
import { useMyAbsences } from '../features/absences/hooks'

interface CalendarEvent {
  id: string
  title: string
  subtitle?: string
  date: string
  colorClass: string
  type: 'project' | 'absence'
  absenceType?: string
}

const ABSENCE_TYPE_COLORS: Record<string, string> = {
  cp: 'bg-emerald-500',
  sick: 'bg-red-500',
  other: 'bg-slate-500',
}

// Absence type labels moved to component for translation support

interface Project {
  project_id: number
  project_name: string
  client_name?: string | null
  start_date: string
  end_date?: string | null
}

// Stable color palette indexed by project_id, so each project keeps the same color.
const PROJECT_COLORS = [
  'bg-indigo-500',
  'bg-purple-500',
  'bg-blue-500',
  'bg-teal-500',
  'bg-amber-500',
  'bg-rose-500',
  'bg-cyan-500',
  'bg-emerald-500',
]

function projectColor(projectId: number): string {
  return PROJECT_COLORS[projectId % PROJECT_COLORS.length]
}

export default function CalendarPage() {
  const { t } = useTranslation()
  const today = new Date()

  const [current, setCurrent] = useState(new Date(today.getFullYear(), today.getMonth(), 1))

  const year = current.getFullYear()
  const month = current.getMonth()

  const months: string[] = t('calendar.months', { returnObjects: true }) as string[]
  const days: string[] = t('calendar.days', { returnObjects: true }) as string[]

  // Map absence types to translated labels
  const absenceTypeLabels: Record<string, string> = {
    cp: t('calendar.paidLeave', 'Congé payé'),
    sick: t('calendar.sickLeave', 'Maladie'),
    other: t('calendar.other', 'Autre'),
  }

  const { data: absences, isLoading: absLoading, isError: absError } = useMyAbsences()

  // Fetch all assigned active projects (no date filter — we filter by range in projectEvents below).
  const { data: projects = [], isLoading: projLoading, isError: projError } = useQuery({
    queryKey: ['projects-assigned'],
    queryFn: () => apiClient.get<Project[]>(`/projects?active=true`),
  })

  const isLoading = absLoading || projLoading
  const isError = absError || projError

  // Absence events — expand each absence range to per-day events inside the visible month.
  const absenceEvents = useMemo((): CalendarEvent[] => {
    if (!absences) return []
    const result: CalendarEvent[] = []
    absences.forEach((abs) => {
      if (abs.status === 'rejected') return
      const start = new Date(abs.start_date)
      const end = new Date(abs.end_date)
      const cur = new Date(start)
      while (cur <= end) {
        if (cur.getMonth() === month && cur.getFullYear() === year) {
          const dateStr = `${cur.getFullYear()}-${String(cur.getMonth() + 1).padStart(2, '0')}-${String(cur.getDate()).padStart(2, '0')}`
          result.push({
            id: `abs-${abs.absence_id}-${dateStr}`,
            title: absenceTypeLabels[abs.absence_type] ?? abs.absence_type,
            date: dateStr,
            colorClass: ABSENCE_TYPE_COLORS[abs.absence_type] ?? 'bg-slate-400',
            type: 'absence',
            absenceType: abs.absence_type,
          })
        }
        cur.setDate(cur.getDate() + 1)
      }
    })
    return result
  }, [absences, year, month])

  // Project events — show assigned projects for each weekday inside their date range.
  // Skip weekends (Sat=6, Sun=0) since they are not work days.
  const projectEvents = useMemo((): CalendarEvent[] => {
    if (!projects) return []
    const result: CalendarEvent[] = []
    projects.forEach((proj) => {
      const start = new Date(proj.start_date)
      const end = proj.end_date ? new Date(proj.end_date) : new Date(year, month + 1, 0)
      const cur = new Date(start)
      while (cur <= end) {
        const dow = cur.getDay()
        if (cur.getMonth() === month && cur.getFullYear() === year && dow !== 0 && dow !== 6) {
          const dateStr = `${cur.getFullYear()}-${String(cur.getMonth() + 1).padStart(2, '0')}-${String(cur.getDate()).padStart(2, '0')}`
          result.push({
            id: `proj-${proj.project_id}-${dateStr}`,
            title: proj.project_name,
            subtitle: proj.client_name ?? undefined,
            date: dateStr,
            colorClass: projectColor(proj.project_id),
            type: 'project',
          })
        }
        cur.setDate(cur.getDate() + 1)
      }
    })
    return result
  }, [projects, year, month])

  const allEvents = useMemo(
    () => [...projectEvents, ...absenceEvents],
    [projectEvents, absenceEvents],
  )

  const firstDow = new Date(year, month, 1).getDay()
  const startOffset = firstDow === 0 ? 6 : firstDow - 1
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const totalCells = Math.ceil((startOffset + daysInMonth) / 7) * 7

  const cells: (number | null)[] = []
  for (let i = 0; i < totalCells; i++) {
    const dayNum = i - startOffset + 1
    cells.push(dayNum >= 1 && dayNum <= daysInMonth ? dayNum : null)
  }

  const eventsForDay = (day: number) => {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    return allEvents.filter(e => e.date === dateStr)
  }

  const isToday = (day: number) =>
    day === today.getDate() && month === today.getMonth() && year === today.getFullYear()

  const isWeekend = (cellIndex: number) => {
    const dow = cellIndex % 7
    return dow === 5 || dow === 6
  }

  const goToToday = () => setCurrent(new Date(today.getFullYear(), today.getMonth(), 1))
  const prevMonth = () => setCurrent(new Date(year, month - 1, 1))
  const nextMonth = () => setCurrent(new Date(year, month + 1, 1))

  // View mode: 'month' (grid) or 'list'. Default: list on mobile, month on tablet/desktop.
  const [viewMode, setViewMode] = useState<'month' | 'list'>(() =>
    typeof window !== 'undefined' && window.innerWidth < 768 ? 'list' : 'month'
  )

  // Force list mode on small screens, restore on resize
  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth < 640 && viewMode === 'month') setViewMode('list')
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [viewMode])

  // List view: build day-by-day rows for the current month, only days having events
  const listDays = useMemo(() => {
    const out: { dateStr: string; day: number; dow: number; events: CalendarEvent[] }[] = []
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
      const dayEvents = allEvents.filter((e) => e.date === dateStr)
      if (dayEvents.length === 0) continue
      const dow = new Date(year, month, d).getDay()
      out.push({ dateStr, day: d, dow, events: dayEvents })
    }
    return out
  }, [allEvents, year, month, daysInMonth])

  const eventIcon = (event: CalendarEvent, size = 12) => {
    if (event.type === 'project') return <Briefcase size={size} />
    if (event.absenceType === 'sick') return <HeartPulse size={size} />
    if (event.absenceType === 'cp') return <Plane size={size} />
    return <CalendarOff size={size} />
  }

  return (
    <div className="space-y-4">
      {/* Page Title */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white">
          {t('calendar.title', 'Planning')}
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          Vue mensuelle de vos projets et absences
        </p>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-3">
        <div className="flex items-center justify-between sm:justify-start gap-3 flex-1 min-w-0">
          <div className="flex items-center gap-2 min-w-0">
            <h2 className="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-100 capitalize truncate">
              {months[month]} {year}
            </h2>
            {isLoading && <Loader2 size={14} className="animate-spin text-indigo-400 flex-shrink-0" />}
          </div>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <button
              onClick={prevMonth}
              className="w-8 h-8 flex items-center justify-center rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors"
              aria-label={t('calendar.prev')}
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={goToToday}
              className="px-2.5 py-1.5 text-xs sm:text-sm font-medium text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-700 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/30 transition-colors"
            >
              {t('calendar.today')}
            </button>
            <button
              onClick={nextMonth}
              className="w-8 h-8 flex items-center justify-center rounded-lg border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors"
              aria-label={t('calendar.next')}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

        {/* View mode toggle (hidden on smallest mobile, visible from sm:) */}
        <div className="hidden sm:flex items-center gap-1 bg-slate-100 dark:bg-slate-700 rounded-lg p-1">
          <button
            onClick={() => setViewMode('month')}
            aria-pressed={viewMode === 'month'}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
              viewMode === 'month'
                ? 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 shadow-sm'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
            }`}
          >
            <LayoutGrid size={13} /> Mois
          </button>
          <button
            onClick={() => setViewMode('list')}
            aria-pressed={viewMode === 'list'}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
              viewMode === 'list'
                ? 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 shadow-sm'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
            }`}
          >
            <List size={13} /> Liste
          </button>
        </div>
      </div>

      {/* Error state */}
      {isError && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400">
          <AlertTriangle size={20} className="flex-shrink-0" />
          <span className="text-sm">{t('common.error')}</span>
        </div>
      )}

      {/* MONTH VIEW (desktop / tablet) — hidden on mobile */}
      {viewMode === 'month' && (
        <div className="hidden sm:block bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
          {/* Day headers */}
          <div className="grid grid-cols-7 border-b border-slate-200 dark:border-slate-700">
            {days.map((day, i) => (
              <div
                key={day}
                className={`py-2 sm:py-3 text-center text-[10px] sm:text-xs font-semibold uppercase tracking-wide ${
                  i >= 5 ? 'text-slate-400 dark:text-slate-500' : 'text-slate-500 dark:text-slate-400'
                }`}
              >
                {day}
              </div>
            ))}
          </div>

          {/* Day cells */}
          <div className="grid grid-cols-7">
            {cells.map((day, i) => {
              const weekend = isWeekend(i)
              const events = day ? eventsForDay(day) : []
              const todayCell = day ? isToday(day) : false
              const isLastRow = i >= cells.length - 7

              return (
                <div
                  key={i}
                  className={`min-h-[90px] md:min-h-[120px] p-1.5 md:p-2 border-b border-r border-slate-100 dark:border-slate-700 ${
                    isLastRow ? 'border-b-0' : ''
                  } ${i % 7 === 6 ? 'border-r-0' : ''} ${
                    !day
                      ? 'bg-slate-50/40 dark:bg-slate-900/20'
                      : weekend
                      ? 'bg-slate-50/60 dark:bg-slate-800/60'
                      : 'bg-white dark:bg-slate-800'
                  }`}
                >
                  {day && (
                    <>
                      <div className="flex items-center justify-between mb-1 md:mb-1.5">
                        <span
                          className={`inline-flex items-center justify-center w-6 h-6 md:w-7 md:h-7 rounded-full text-xs md:text-sm font-medium ${
                            todayCell
                              ? 'bg-indigo-600 text-white font-bold shadow-sm'
                              : weekend
                              ? 'text-slate-400 dark:text-slate-500'
                              : 'text-slate-700 dark:text-slate-200'
                          }`}
                        >
                          {day}
                        </span>
                        {events.length > 0 && (
                          <span className="text-[10px] text-slate-400 dark:text-slate-500 font-medium">
                            {events.length}
                          </span>
                        )}
                      </div>

                      <div className="space-y-0.5 md:space-y-1">
                        {events.slice(0, 3).map((event) => (
                          <span
                            key={event.id}
                            title={event.subtitle ? `${event.title} — ${event.subtitle}` : event.title}
                            className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] md:text-[11px] font-medium text-white truncate ${event.colorClass}`}
                          >
                            <span className="flex-shrink-0">{eventIcon(event)}</span>
                            <span className="truncate flex-1">{event.title}</span>
                          </span>
                        ))}
                        {events.length > 3 && (
                          <p className="text-[10px] text-slate-400 dark:text-slate-500 pl-1">
                            +{events.length - 3}
                          </p>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* LIST VIEW (always available, default on mobile) */}
      {(viewMode === 'list' || true) && (
        <div className={`${viewMode === 'list' ? 'block' : 'block sm:hidden'} space-y-2`}>
          {listDays.length === 0 ? (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-10 text-center">
              <p className="text-sm text-slate-500 dark:text-slate-400">Aucun événement ce mois-ci</p>
            </div>
          ) : (
            listDays.map((d) => {
              const date = new Date(year, month, d.day)
              const isTodayItem = isToday(d.day)
              const isWeekendItem = d.dow === 0 || d.dow === 6
              return (
                <div
                  key={d.dateStr}
                  className={`bg-white dark:bg-slate-800 rounded-xl border ${
                    isTodayItem ? 'border-indigo-300 dark:border-indigo-700 ring-1 ring-indigo-200 dark:ring-indigo-800' : 'border-slate-200 dark:border-slate-700'
                  } overflow-hidden`}
                >
                  <div className="flex items-stretch">
                    <div
                      className={`flex flex-col items-center justify-center w-16 sm:w-20 py-2.5 px-2 flex-shrink-0 ${
                        isTodayItem
                          ? 'bg-indigo-600 text-white'
                          : isWeekendItem
                          ? 'bg-slate-50 dark:bg-slate-700 text-slate-400 dark:text-slate-500'
                          : 'bg-slate-50 dark:bg-slate-700/50 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <span className="text-[10px] uppercase font-semibold tracking-wide opacity-80">
                        {date.toLocaleDateString('fr-FR', { weekday: 'short' })}
                      </span>
                      <span className="text-2xl font-bold leading-tight">{d.day}</span>
                    </div>
                    <div className="flex-1 min-w-0 p-2.5 space-y-1.5">
                      {d.events.map((event) => (
                        <div
                          key={event.id}
                          className="flex items-center gap-2 p-1.5 -m-1.5 rounded-lg"
                        >
                          <span className={`flex items-center justify-center w-6 h-6 rounded-md text-white flex-shrink-0 ${event.colorClass}`}>
                            {eventIcon(event)}
                          </span>
                          <span className="flex-1 min-w-0">
                            <span className="block text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                              {event.title}
                            </span>
                            {event.subtitle && (
                              <span className="block text-xs text-slate-500 dark:text-slate-400 truncate">
                                {event.subtitle}
                              </span>
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-3 sm:gap-4 flex-wrap bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 px-3 py-2">
        <div className="flex items-center gap-1.5">
          <span className="inline-flex items-center justify-center w-4 h-4 rounded bg-indigo-500 text-white">
            <Briefcase size={9} />
          </span>
          <span className="text-xs text-slate-600 dark:text-slate-400">Projet assigné</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="inline-flex items-center justify-center w-4 h-4 rounded bg-emerald-500 text-white">
            <Plane size={9} />
          </span>
          <span className="text-xs text-slate-600 dark:text-slate-400">Absence</span>
        </div>
      </div>
    </div>
  )
}

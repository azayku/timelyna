import { useState, useEffect } from 'react'
import { Play, Square, Timer } from 'lucide-react'
import { useActiveTimer, useStartTimer, useStopTimer } from '../features/timer/hooks'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'

interface SimpleProject { project_id: number; project_name: string }

function formatElapsed(startedAt: string): string {
  const start = new Date(startedAt).getTime()
  const now = Date.now()
  const seconds = Math.floor((now - start) / 1000)
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

export default function TimerWidget() {
  const { data: activeTimer, isLoading } = useActiveTimer()
  const { data: projects = [] } = useQuery<SimpleProject[]>({
    queryKey: ['projects-simple'],
    queryFn: () => apiClient.get<SimpleProject[]>('/projects?active=true'),
  })
  const startMutation = useStartTimer()
  const stopMutation = useStopTimer()
  const [elapsed, setElapsed] = useState('00:00:00')
  const [selectedProjectId, setSelectedProjectId] = useState<number | ''>('')
  const [description, setDescription] = useState('')

  useEffect(() => {
    if (!activeTimer) return
    const interval = setInterval(() => {
      setElapsed(formatElapsed(activeTimer.started_at))
    }, 1000)
    return () => clearInterval(interval)
  }, [activeTimer])

  const handleStart = () => {
    if (!selectedProjectId) return
    startMutation.mutate({ project_id: Number(selectedProjectId), description: description || undefined })
  }

  const handleStop = () => {
    stopMutation.mutate()
  }

  if (isLoading) return null

  const activeProjects = projects
  const projectName = activeTimer
    ? activeProjects.find(p => p.project_id === activeTimer.project_id)?.project_name
    : null

  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <Timer className="h-4 w-4 text-indigo-500" />
        <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">Chronomètre</span>
      </div>
      
      {activeTimer ? (
        <div className="space-y-2">
          <div className="text-2xl font-mono font-bold text-indigo-600 dark:text-indigo-400 text-center">
            {elapsed}
          </div>
          <div className="text-xs text-slate-500 dark:text-slate-400 text-center">
            {projectName || `Projet #${activeTimer.project_id}`}
            {activeTimer.description && ` — ${activeTimer.description}`}
          </div>
          <button
            onClick={handleStop}
            disabled={stopMutation.isPending}
            aria-label="Arrêter le timer"
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-red-500 hover:bg-red-600 dark:bg-red-600 dark:hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            <Square className="h-4 w-4" />
            Arrêter
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value ? Number(e.target.value) : '')}
            className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label="Sélectionner un projet"
          >
            <option value="">Choisir un projet...</option>
            {activeProjects.map(p => (
              <option key={p.project_id} value={p.project_id}>
                {p.project_name}
              </option>
            ))}
          </select>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optionnel)"
            className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={handleStart}
            disabled={!selectedProjectId || startMutation.isPending}
            aria-label="Démarrer le timer"
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="h-4 w-4" />
            Démarrer
          </button>
        </div>
      )}
    </div>
  )
}

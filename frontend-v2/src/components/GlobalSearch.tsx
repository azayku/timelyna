import { useState, useRef, useEffect, useMemo } from 'react'
import { Search, Users, FolderOpen, Building2, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../lib/authStore'
import { fetchEmployees } from '../features/employees/api'
import { fetchProjects } from '../features/projects/api'
import { fetchClients } from '../features/clients/api'

interface SearchItem {
  type: 'employee' | 'project' | 'client'
  label: string
  sub: string
  to: string
  icon: React.ReactNode
}

const TYPE_LABELS: Record<string, string> = {
  employee: 'Employés',
  project: 'Projets',
  client: 'Clients',
}

const TYPE_COLORS: Record<string, string> = {
  employee: 'text-indigo-600 bg-indigo-50',
  project: 'text-emerald-600 bg-emerald-50',
  client: 'text-amber-600 bg-amber-50',
}

export default function GlobalSearch() {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const { t } = useTranslation()
  const user = useAuthStore(s => s.user)
  const isAdmin = user?.role === 'admin'

  // Fetch data from API — admin only
  const { data: employees = [] } = useQuery({ queryKey: ['employees'], queryFn: fetchEmployees, enabled: isAdmin })
  const { data: projects = [] } = useQuery({ queryKey: ['projects'], queryFn: fetchProjects, enabled: isAdmin })
  const { data: clients = [] } = useQuery({ queryKey: ['clients'], queryFn: fetchClients, enabled: isAdmin })

  // Build search data from API
  const searchData = useMemo<SearchItem[]>(() => {
    const items: SearchItem[] = []
    
    // Employees
    employees.forEach(e => {
      items.push({
        type: 'employee',
        label: `${e.first_name} ${e.last_name}`,
        sub: `${e.role} · ${e.employment_status === 'active' ? 'actif' : 'inactif'}`,
        to: '/admin/users',
        icon: <Users size={14} />,
      })
    })
    
    // Projects
    projects.forEach(p => {
      const statusLabels: Record<string, string> = {
        draft: 'brouillon',
        planning: 'planification',
        active: 'actif',
        completed: 'terminé',
        on_hold: 'en pause',
      }
      items.push({
        type: 'project',
        label: p.project_name,
        sub: `${p.client_id ? `Client #${p.client_id}` : 'Client inconnu'} · ${statusLabels[p.status] ?? p.status}`,
        to: '/admin/projects',
        icon: <FolderOpen size={14} />,
      })
    })
    
    // Clients
    clients.forEach(c => {
      const projectCount = projects.filter(p => p.client_id === c.client_id).length
      items.push({
        type: 'client',
        label: c.client_name,
        sub: `Client · ${projectCount} projet${projectCount !== 1 ? 's' : ''}`,
        to: '/admin/clients',
        icon: <Building2 size={14} />,
      })
    })
    
    return items
  }, [employees, projects, clients])

  const results = query.trim().length >= 1
    ? searchData.filter(item =>
        item.label.toLowerCase().includes(query.toLowerCase()) ||
        item.sub.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 8)
    : []

  // Group results by type
  const grouped = results.reduce<Record<string, typeof results>>((acc, item) => {
    if (!acc[item.type]) acc[item.type] = []
    acc[item.type].push(item)
    return acc
  }, {})

  const flatResults = Object.values(grouped).flat()

  const handleSelect = (item: SearchItem) => {
    navigate(item.to)
    setQuery('')
    setOpen(false)
    setSelected(-1)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open || flatResults.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelected(s => Math.min(s + 1, flatResults.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelected(s => Math.max(s - 1, 0))
    } else if (e.key === 'Enter' && selected >= 0) {
      handleSelect(flatResults[selected])
    } else if (e.key === 'Escape') {
      setOpen(false)
      setQuery('')
    }
  }

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Reset selected when results change
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { setSelected(-1) }, [query])

  let flatIndex = 0

  return (
    <div ref={containerRef} className="relative hidden md:block">
      <div className={`flex items-center gap-2 rounded-lg px-3 py-2 w-56 transition-all ${
        open ? 'bg-white border border-indigo-300 shadow-sm' : 'bg-slate-100'
      }`}>
        <Search size={14} className="text-slate-400 flex-shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => { setQuery(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={t('common.search') + '…'}
          className="bg-transparent text-sm text-slate-700 outline-none w-full placeholder-slate-400"
        />
        {query && (
          <button onClick={() => { setQuery(''); setOpen(false); inputRef.current?.focus() }}>
            <X size={13} className="text-slate-400 hover:text-slate-600" />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {open && query.trim().length >= 1 && (
        <div className="absolute top-full left-0 mt-1.5 w-80 bg-white rounded-xl shadow-xl border border-slate-200 z-50 overflow-hidden">
          {flatResults.length === 0 ? (
            <div className="px-4 py-6 text-center text-sm text-slate-400">
              Aucun résultat pour « {query} »
            </div>
          ) : (
            <div className="py-1.5 max-h-80 overflow-y-auto">
              {Object.entries(grouped).map(([type, items]) => (
                <div key={type}>
                  {/* Group header */}
                  <div className="px-3 py-1.5 flex items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${TYPE_COLORS[type]}`}>
                      {TYPE_LABELS[type]}
                    </span>
                  </div>
                  {/* Items */}
                  {items.map(item => {
                    const idx = flatIndex++
                    return (
                      <button
                        key={item.label}
                        onClick={() => handleSelect(item)}
                        onMouseEnter={() => setSelected(idx)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors ${
                          selected === idx ? 'bg-indigo-50' : 'hover:bg-slate-50'
                        }`}
                      >
                        <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${TYPE_COLORS[type]}`}>
                          {item.icon}
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-800 truncate">
                            {/* Highlight matching text */}
                            {item.label.split(new RegExp(`(${query})`, 'gi')).map((part, i) =>
                              part.toLowerCase() === query.toLowerCase()
                                ? <mark key={i} className="bg-yellow-100 text-yellow-800 rounded px-0.5">{part}</mark>
                                : part
                            )}
                          </p>
                          <p className="text-xs text-slate-400 truncate">{item.sub}</p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              ))}
            </div>
          )}

          {/* Footer hint */}
          <div className="px-3 py-2 border-t border-slate-100 flex items-center gap-3 text-[10px] text-slate-400">
            <span>↑↓ naviguer</span>
            <span>↵ ouvrir</span>
            <span>Esc fermer</span>
          </div>
        </div>
      )}
    </div>
  )
}

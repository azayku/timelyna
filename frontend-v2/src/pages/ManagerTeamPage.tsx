import { useState } from 'react'
import { User, Building2, Calendar, Mail, Search, Settings } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'
import Avatar from '../components/ui/Avatar'
import { displayNameFromEmail } from '../utils/userDisplay'
import Pagination from '../components/ui/Pagination'
import EmployeeSkillModal from '../components/manager/EmployeeSkillModal'

interface TeamMember {
  employee_id: number
  first_name: string
  last_name: string
  email: string
  hire_date: string | null
  organization_name: string
  skills: string[]
}

export default function ManagerTeamPage() {
  const { t } = useTranslation()
  const [page, setPage] = useState(1)
  const [searchQuery, setSearchQuery] = useState('')
  const [organizationFilter, setOrganizationFilter] = useState<string>('')
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null)
  const itemsPerPage = 10

  const { data: teamMembers = [], isLoading } = useQuery({
    queryKey: ['manager-team'],
    queryFn: () => apiClient.get<TeamMember[]>('/manager/team'),
  })

  // Get unique organizations for filter dropdown
  const organizations = Array.from(
    new Set(teamMembers.map(m => m.organization_name))
  ).sort()

  // Filter by search query and organization
  const filteredMembers = teamMembers.filter(member => {
    const searchLower = searchQuery.toLowerCase()
    const matchesSearch = searchQuery === '' || (
      member.first_name.toLowerCase().includes(searchLower) ||
      member.last_name.toLowerCase().includes(searchLower) ||
      member.email.toLowerCase().includes(searchLower)
    )
    const matchesOrg = organizationFilter === '' || member.organization_name === organizationFilter
    return matchesSearch && matchesOrg
  })

  const totalPages = Math.ceil(filteredMembers.length / itemsPerPage)
  const paginatedMembers = filteredMembers.slice(
    (page - 1) * itemsPerPage,
    page * itemsPerPage
  )

  // Reset page when filters change
  const handleSearch = (value: string) => {
    setSearchQuery(value)
    setPage(1)
  }

  const handleOrgFilter = (value: string) => {
    setOrganizationFilter(value)
    setPage(1)
  }

  if (isLoading) {
    return (
      <div className="max-w-6xl space-y-5">
        <div className="text-center py-12 text-slate-400">
          {t('common.loading', 'Chargement…')}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white">
          {t('team.myTeam', 'Mon équipe')}
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          {filteredMembers.length} membre{filteredMembers.length > 1 ? 's' : ''} {(searchQuery || organizationFilter) && `(${teamMembers.length} au total)`}
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => handleSearch(e.target.value)}
            placeholder={t('common.search', 'Rechercher par nom ou email')}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Organization Filter */}
        {organizations.length > 0 && (
          <select
            value={organizationFilter}
            onChange={e => handleOrgFilter(e.target.value)}
            className="px-4 py-2 border border-slate-200 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">{t('common.allOrganizations', 'Toutes les organisations')}</option>
            {organizations.map(org => (
              <option key={org} value={org}>{org}</option>
            ))}
          </select>
        )}
      </div>

      {/* Team Members */}
      {filteredMembers.length === 0 ? (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <User size={48} className="mx-auto mb-4 text-slate-300 dark:text-slate-600" />
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            {searchQuery || organizationFilter
              ? t('team.noResults', 'Aucun résultat pour cette recherche')
              : t('team.noTeamMembers', 'Aucun membre d\'équipe')}
          </p>
          {(searchQuery || organizationFilter) && (
            <button
              onClick={() => {
                handleSearch('')
                handleOrgFilter('')
              }}
              className="mt-3 text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400"
            >
              {t('managers.team.resetFilters', 'Réinitialiser les filtres')}
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Desktop Table */}
          <div className="hidden md:block bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/50">
                  <th className="px-4 py-3 text-left">{t('tableHeaders.employee', 'Employé')}</th>
                  <th className="px-4 py-3 text-left">{t('tableHeaders.email', 'Email')}</th>
                  <th className="px-4 py-3 text-left">{t('tableHeaders.organization', 'Organisation')}</th>
                  <th className="px-4 py-3 text-left">{t('tableHeaders.skills', 'Compétences')}</th>
                  <th className="px-4 py-3 text-left">{t('tableHeaders.hireDate', 'Date d\'entrée')}</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {paginatedMembers.map(member => (
                  <tr key={member.employee_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <Avatar
                          name={displayNameFromEmail(member.email)}
                          size="sm"
                        />
                        <div>
                          <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                            {member.first_name} {member.last_name}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                        <Mail size={14} />
                        <span>{member.email}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                        <Building2 size={14} />
                        <span>{member.organization_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {member.skills.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {member.skills.map(skill => (
                            <span
                              key={skill}
                              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {member.hire_date ? (
                        <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                          <Calendar size={14} />
                          <span>{new Date(member.hire_date).toLocaleDateString('fr-FR')}</span>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => setSelectedMember(member)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 dark:hover:text-indigo-400 transition-colors"
                        title="Gérer les compétences"
                      >
                        <Settings size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="md:hidden space-y-3">
            {paginatedMembers.map(member => (
              <div
                key={member.employee_id}
                className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4"
              >
                <div className="flex items-start gap-3 mb-3">
                  <Avatar
                    name={displayNameFromEmail(member.email)}
                    size="sm"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                      {member.first_name} {member.last_name}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                      {member.email}
                    </p>
                  </div>
                </div>
                <div className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
                  <div className="flex items-center gap-2">
                    <Building2 size={12} />
                    <span>{member.organization_name}</span>
                  </div>
                  {member.hire_date && (
                    <div className="flex items-center gap-2">
                      <Calendar size={12} />
                      <span>Depuis le {new Date(member.hire_date).toLocaleDateString('fr-FR')}</span>
                    </div>
                  )}
                  {member.skills.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {member.skills.map(skill => (
                        <span
                          key={skill}
                          className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                  <button
                    onClick={() => setSelectedMember(member)}
                    className="mt-3 flex items-center gap-1.5 text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
                  >
                    <Settings size={12} />
                    Gérer les compétences
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          <Pagination
            page={page}
            totalPages={totalPages}
            totalItems={filteredMembers.length}
            itemsPerPage={itemsPerPage}
            onPageChange={setPage}
          />
        </>
      )}

      {selectedMember && (
        <EmployeeSkillModal
          member={selectedMember}
          onClose={() => setSelectedMember(null)}
        />
      )}
    </div>
  )
}

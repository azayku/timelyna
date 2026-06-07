import { useState } from 'react'
import { Building2, Users, User, Search } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../lib/apiClient'
import Pagination from '../components/ui/Pagination'

interface Organization {
  organization_id: number
  organization_name: string
  employee_count: number
  manager_name: string
  created_at: string
}

export default function ManagerOrganizationsPage() {
  const { t } = useTranslation()
  const [page, setPage] = useState(1)
  const [searchQuery, setSearchQuery] = useState('')
  const itemsPerPage = 10

  const { data: organizations = [], isLoading } = useQuery({
    queryKey: ['manager-organizations'],
    queryFn: () => apiClient.get<Organization[]>('/manager/organizations'),
  })

  // Filter by search query
  const filteredOrgs = organizations.filter(org => {
    const searchLower = searchQuery.toLowerCase()
    return searchQuery === '' || (
      org.organization_name.toLowerCase().includes(searchLower) ||
      org.manager_name.toLowerCase().includes(searchLower)
    )
  })

  const totalPages = Math.ceil(filteredOrgs.length / itemsPerPage)
  const paginatedOrgs = filteredOrgs.slice(
    (page - 1) * itemsPerPage,
    page * itemsPerPage
  )

  // Reset page when search changes
  const handleSearch = (value: string) => {
    setSearchQuery(value)
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white">
            {t('organizations.myOrganizations', 'Mes organisations')}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            {filteredOrgs.length} organisation{filteredOrgs.length > 1 ? 's' : ''} · {filteredOrgs.reduce((sum, org) => sum + org.employee_count, 0)} employé{filteredOrgs.reduce((sum, org) => sum + org.employee_count, 0) > 1 ? 's' : ''} au total
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={e => handleSearch(e.target.value)}
          placeholder={t('common.search', 'Rechercher par nom d\'organisation ou manager...')}
          className="w-full pl-10 pr-4 py-2 border border-slate-200 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Organizations Table */}
      {filteredOrgs.length === 0 ? (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-12 text-center">
          <Building2 size={48} className="mx-auto mb-4 text-slate-300 dark:text-slate-600" />
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            {searchQuery
              ? t('common.noResults', 'Aucun résultat')
              : t('organizations.noOrganizations', 'Aucune organisation')}
          </p>
          {searchQuery && (
            <button
              onClick={() => handleSearch('')}
              className="mt-3 text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-400"
            >
              {t('common.resetFilters', 'Réinitialiser')}
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
                  <th className="px-4 py-3 text-left">{t('common.name', 'Organisation')}</th>
                  <th className="px-4 py-3 text-left">{t('organizations.manager', 'Manager')}</th>
                  <th className="px-4 py-3 text-left">{t('organizations.employeeCount', 'Employés')}</th>
                  <th className="px-4 py-3 text-left">{t('common.createdAt', 'Date de création')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {paginatedOrgs.map(org => (
                  <tr key={org.organization_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center flex-shrink-0">
                          <Building2 size={20} className="text-indigo-600 dark:text-indigo-400" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                            {org.organization_name}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                        <User size={14} />
                        <span>{org.manager_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                        <Users size={14} />
                        <span>{org.employee_count} employé{org.employee_count > 1 ? 's' : ''}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-600 dark:text-slate-400">
                        {new Date(org.created_at).toLocaleDateString('fr-FR')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="md:hidden space-y-3">
            {paginatedOrgs.map(org => (
              <div
                key={org.organization_id}
                className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4"
              >
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center flex-shrink-0">
                    <Building2 size={20} className="text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-200 mb-1">
                      {org.organization_name}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {t('managers.organizations.createdOn', 'Créée le')} {new Date(org.created_at).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                </div>
                <div className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
                  <div className="flex items-center gap-2">
                    <User size={12} />
                    <span>{t('managers.organizations.manager', 'Manager:')} {org.manager_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users size={12} />
                    <span>{org.employee_count} employé{org.employee_count > 1 ? 's' : ''}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          <Pagination
            page={page}
            totalPages={totalPages}
            totalItems={filteredOrgs.length}
            itemsPerPage={itemsPerPage}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  )
}

import { useState, useMemo } from 'react'
import { useAllContacts, useCreateContact, useUpdateContact, useDeleteContact } from '../features/emergency-contacts'
import { fetchEmployees } from '../features/employees/api'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, AlertCircle, Loader } from 'lucide-react'
import { EmergencyContactCard } from '../components/EmergencyContactCard'
import { EmergencyContactForm } from '../components/EmergencyContactForm'
import type { EmergencyContact, CreateEmergencyContactPayload, UpdateEmergencyContactPayload } from '../features/emergency-contacts'
import type { Employee } from '../features/employees/types'

export function EmergencyContactsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingContact, setEditingContact] = useState<EmergencyContact | null>(null)

  // Fetch employees
  const { data: employees = [], isLoading: employeesLoading } = useQuery<Employee[]>({
    queryKey: ['employees'],
    queryFn: fetchEmployees,
    staleTime: 10 * 60 * 1000,
  })

  // Fetch all contacts
  const { data: allContacts = [], isLoading: contactsLoading } = useAllContacts()

  // Get selected employee
  const selectedEmployee = useMemo(
    () => employees.find((e: Employee) => e.employee_id === selectedEmployeeId),
    [employees, selectedEmployeeId],
  )

  // Get contacts for selected employee
  const employeeContacts = useMemo(
    () => (selectedEmployeeId ? allContacts.filter((c) => c.employee_id === selectedEmployeeId) : []),
    [allContacts, selectedEmployeeId],
  )

  // Search filtered employees
  const filteredEmployees = useMemo(
    () =>
      employees.filter(
        (e: Employee) =>
          `${e.first_name} ${e.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
          e.email.toLowerCase().includes(searchTerm.toLowerCase()),
      ),
    [employees, searchTerm],
  )

  // Mutations
  const createMutation = useCreateContact()
  const updateMutation = useUpdateContact()
  const deleteMutation = useDeleteContact()

  const handleCreateContact = async (payload: CreateEmergencyContactPayload) => {
    try {
      await createMutation.mutateAsync(payload)
      setShowForm(false)
      setEditingContact(null)
    } catch (error) {
      console.error('Failed to create contact:', error)
    }
  }

  const handleUpdateContact = async (payload: UpdateEmergencyContactPayload) => {
    if (!editingContact) return
    try {
      await updateMutation.mutateAsync({ contactId: editingContact.contact_id, payload })
      setShowForm(false)
      setEditingContact(null)
    } catch (error) {
      console.error('Failed to update contact:', error)
    }
  }

  const handleDeleteContact = async (contactId: number) => {
    if (window.confirm('Are you sure you want to delete this contact?')) {
      try {
        await deleteMutation.mutateAsync(contactId)
      } catch (error) {
        console.error('Failed to delete contact:', error)
      }
    }
  }

  const handleEditContact = (contact: EmergencyContact) => {
    setEditingContact(contact)
    setShowForm(true)
  }

  const handleFormSubmit = async (payload: CreateEmergencyContactPayload | UpdateEmergencyContactPayload) => {
    if (editingContact) {
      await handleUpdateContact(payload as UpdateEmergencyContactPayload)
    } else {
      await handleCreateContact(payload as CreateEmergencyContactPayload)
    }
  }

  if (employeesLoading || contactsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="animate-spin text-indigo-500" size={32} />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Emergency Contacts</h1>
          <p className="text-slate-600 dark:text-slate-400">Manage emergency contact information for all employees</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Employee List */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
              {/* Search */}
              <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
                  <input
                    type="text"
                    placeholder="Search employees..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Employee List */}
              <div className="divide-y divide-slate-200 dark:divide-slate-700 max-h-[600px] overflow-y-auto">
                {filteredEmployees.length === 0 ? (
                  <div className="p-4 text-center text-slate-500 dark:text-slate-400">No employees found</div>
                ) : (
                  filteredEmployees.map((employee) => (
                    <button
                      key={employee.employee_id}
                      onClick={() => setSelectedEmployeeId(employee.employee_id)}
                      className={`w-full text-left p-4 transition-colors ${
                        selectedEmployeeId === employee.employee_id
                          ? 'bg-indigo-50 dark:bg-indigo-900/20 border-l-4 border-indigo-600'
                          : 'hover:bg-slate-50 dark:hover:bg-slate-700'
                      }`}
                    >
                      <div className="font-medium text-slate-900 dark:text-white">
                        {employee.first_name} {employee.last_name}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 truncate">{employee.email}</div>
                      <div className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                        {allContacts.filter((c) => c.employee_id === employee.employee_id).length} contact(s)
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right: Employee Details and Contacts */}
          <div className="lg:col-span-2">
            {selectedEmployee ? (
              <div className="space-y-6">
                {/* Employee Info Card */}
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                        {selectedEmployee.first_name} {selectedEmployee.last_name}
                      </h2>
                      <p className="text-slate-600 dark:text-slate-400">{selectedEmployee.email}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-slate-600 dark:text-slate-400">Role</div>
                      <div className="font-semibold text-slate-900 dark:text-white capitalize">{selectedEmployee.role}</div>
                    </div>
                  </div>

                  {selectedEmployee.phone && (
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      Phone: <span className="font-medium">{selectedEmployee.phone}</span>
                    </div>
                  )}
                  {selectedEmployee.department && (
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      Department: <span className="font-medium">{selectedEmployee.department}</span>
                    </div>
                  )}
                </div>

                {/* Add Contact Form or Button */}
                {showForm ? (
                  <EmergencyContactForm
                    employeeId={selectedEmployee.employee_id}
                    contact={editingContact || undefined}
                    onSubmit={handleFormSubmit}
                    onCancel={() => {
                      setShowForm(false)
                      setEditingContact(null)
                    }}
                    isLoading={createMutation.isPending || updateMutation.isPending}
                  />
                ) : (
                  <button
                    onClick={() => {
                      setEditingContact(null)
                      setShowForm(true)
                    }}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
                  >
                    <Plus size={20} />
                    Add Emergency Contact
                  </button>
                )}

                {/* Contacts List */}
                {employeeContacts.length > 0 ? (
                  <div className="space-y-3">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Emergency Contacts</h3>
                    <div className="grid gap-3">
                      {employeeContacts.map((contact) => (
                        <EmergencyContactCard
                          key={contact.contact_id}
                          contact={contact}
                          onEdit={handleEditContact}
                          onDelete={handleDeleteContact}
                          isLoading={deleteMutation.isPending}
                        />
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600 p-6 text-center">
                    <AlertCircle className="mx-auto mb-3 text-slate-400" size={32} />
                    <p className="text-slate-600 dark:text-slate-400">No emergency contacts for this employee</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-12 text-center">
                <AlertCircle className="mx-auto mb-4 text-slate-400" size={40} />
                <p className="text-slate-600 dark:text-slate-400">Select an employee to view and manage their emergency contacts</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

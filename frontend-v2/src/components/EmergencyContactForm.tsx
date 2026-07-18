import { useState } from 'react'
import type { EmergencyContact, CreateEmergencyContactPayload, UpdateEmergencyContactPayload } from '../features/emergency-contacts'
import { CONTACT_TYPES } from '../features/emergency-contacts'
import { X } from 'lucide-react'

interface EmergencyContactFormProps {
  employeeId?: number
  contact?: EmergencyContact
  onSubmit: (payload: CreateEmergencyContactPayload | UpdateEmergencyContactPayload) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

export function EmergencyContactForm({
  employeeId,
  contact,
  onSubmit,
  onCancel,
  isLoading = false,
}: EmergencyContactFormProps) {
  const [formData, setFormData] = useState({
    contact_name: contact?.contact_name || '',
    phone_number: contact?.phone_number || '',
    contact_type: contact?.contact_type || 'urgence',
    tags: contact?.tags ? (typeof contact.tags === 'string' ? contact.tags : '') : '',
    notes: contact?.notes || '',
  })
  const [error, setError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!formData.contact_name.trim()) {
      setError('Contact name is required')
      return
    }

    if (!formData.phone_number.trim()) {
      setError('Phone number is required')
      return
    }

    try {
      const payload = contact
        ? {
            contact_name: formData.contact_name,
            phone_number: formData.phone_number,
            contact_type: formData.contact_type,
            tags: formData.tags || undefined,
            notes: formData.notes || undefined,
          }
        : {
            employee_id: employeeId || 0,
            contact_name: formData.contact_name,
            phone_number: formData.phone_number,
            contact_type: formData.contact_type,
            tags: formData.tags || undefined,
            notes: formData.notes || undefined,
          }

      await onSubmit(payload)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          {contact ? 'Edit Emergency Contact' : 'Add Emergency Contact'}
        </h3>
        <button
          type="button"
          onClick={onCancel}
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          <X size={20} />
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {/* Contact Name */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Contact Name *
          </label>
          <input
            type="text"
            name="contact_name"
            value={formData.contact_name}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="e.g., John Smith"
          />
        </div>

        {/* Phone Number */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Phone Number *
          </label>
          <input
            type="tel"
            name="phone_number"
            value={formData.phone_number}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="e.g., +33 6 12 34 56 78"
          />
        </div>

        {/* Contact Type */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Contact Type
          </label>
          <select
            name="contact_type"
            value={formData.contact_type}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            {CONTACT_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Tags (comma-separated)
          </label>
          <input
            type="text"
            name="tags"
            value={formData.tags}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="e.g., medical, billing, urgent"
          />
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Notes
          </label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows={3}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="Additional notes..."
          />
        </div>
      </div>

      {/* Submit Buttons */}
      <div className="flex gap-3 mt-6">
        <button
          type="submit"
          disabled={isLoading}
          className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Saving...' : 'Save Contact'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

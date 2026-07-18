import { Trash2, Edit2, Phone, Tag, FileText } from 'lucide-react'
import type { EmergencyContact } from '../features/emergency-contacts'
import { CONTACT_TYPES } from '../features/emergency-contacts'

interface EmergencyContactCardProps {
  contact: EmergencyContact
  onEdit?: (contact: EmergencyContact) => void
  onDelete?: (contactId: number) => void
  isLoading?: boolean
}

export function EmergencyContactCard({
  contact,
  onEdit,
  onDelete,
  isLoading = false,
}: EmergencyContactCardProps) {
  const contactTypeLabel = CONTACT_TYPES.find((ct) => ct.value === contact.contact_type)?.label || contact.contact_type

  // Parse tags if it's a JSON string
  let tags: string[] = []
  if (contact.tags) {
    try {
      tags = JSON.parse(contact.tags)
    } catch (e) {
      tags = contact.tags.split(',').map((t) => t.trim())
    }
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-slate-900 dark:text-white">{contact.contact_name}</h3>
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300">
              {contactTypeLabel}
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 mb-2">
            <Phone size={16} />
            <a href={`tel:${contact.phone_number}`} className="hover:text-indigo-600 dark:hover:text-indigo-400">
              {contact.phone_number}
            </a>
          </div>
        </div>

        {(onEdit || onDelete) && (
          <div className="flex gap-2 ml-2">
            {onEdit && (
              <button
                onClick={() => onEdit(contact)}
                disabled={isLoading}
                className="p-2 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 disabled:opacity-50"
              >
                <Edit2 size={16} />
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(contact.contact_id)}
                disabled={isLoading}
                className="p-2 text-red-500 hover:text-red-700 dark:hover:text-red-400 disabled:opacity-50"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {tags.map((tag, idx) => (
            <span key={idx} className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
              <Tag size={12} />
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Notes */}
      {contact.notes && (
        <div className="flex gap-2 text-xs text-slate-600 dark:text-slate-400">
          <FileText size={14} className="flex-shrink-0 mt-0.5" />
          <p className="italic">{contact.notes}</p>
        </div>
      )}
    </div>
  )
}

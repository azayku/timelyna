import type { SelectHTMLAttributes } from 'react'

interface Option {
  value: string
  label: string
}

interface FormSelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  options: Option[]
  error?: string
  placeholder?: string
}

export default function FormSelect({
  label,
  options,
  error,
  placeholder,
  className = '',
  id,
  ...props
}: FormSelectProps) {
  const selectId = id ?? label?.toLowerCase().replace(/\s+/g, '-')
  return (
    <div className="space-y-1.5">
      {label && (
        <label
          htmlFor={selectId}
          className="block text-xs font-semibold text-slate-600 dark:text-slate-400"
        >
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`w-full border rounded-lg px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 ${
          error
            ? 'border-red-500 dark:border-red-500'
            : 'border-slate-300 dark:border-slate-600'
        } bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200 ${className}`}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>{placeholder}</option>
        )}
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      {error && (
        <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  )
}

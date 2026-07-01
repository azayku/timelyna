// Helpers to derive a display-friendly name from a user email or AuthUser.

function titleCase(s: string): string {
  if (!s) return ''
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase()
}

/**
 * Returns "Prénom Nom" if first_name/last_name available, otherwise falls back to email parsing.
 */
export function displayNameFromUser(user: { first_name?: string; last_name?: string; email?: string } | null | undefined): string {
  if (!user) return 'User'
  const first = user.first_name?.trim()
  const last = user.last_name?.trim()
  if (first && last) return `${titleCase(first)} ${titleCase(last)}`
  if (first) return titleCase(first)
  if (last) return titleCase(last)
  return displayNameFromEmail(user.email)
}

/**
 * Returns initials from first_name/last_name if available, otherwise falls back to email.
 */
export function initialsFromUser(user: { first_name?: string; last_name?: string; email?: string } | null | undefined): string {
  if (!user) return '?'
  const first = user.first_name?.trim()
  const last = user.last_name?.trim()
  if (first && last) return (first[0] + last[0]).toUpperCase()
  if (first) return first.slice(0, 2).toUpperCase()
  return initialsFromEmail(user.email)
}

/**
 * "achille.romano@emp15.test.it" → "Achille Romano"
 * "admin@..."                    → "Admin"
 */
export function displayNameFromEmail(email: string | null | undefined): string {
  if (!email) return 'User'
  const local = email.split('@')[0]
  const parts = local.split('.').filter(Boolean)
  if (parts.length === 0) return 'User'
  return parts.map(titleCase).join(' ')
}

/**
 * "achille.romano@..." → "AR"
 * "admin@..."          → "AD" (first 2 chars when single-word)
 * Always 2 uppercase letters when possible.
 */
export function initialsFromEmail(email: string | null | undefined): string {
  if (!email) return '?'
  const local = email.split('@')[0]
  const parts = local.split('.').filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return parts[0].slice(0, 2).toUpperCase()
}

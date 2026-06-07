// Helpers to derive a display-friendly name from a user email.
// Convention: emails are typically `firstname.lastname@domain`.
// We split on `.` to recover both parts, then title-case each.

function titleCase(s: string): string {
  if (!s) return ''
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase()
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

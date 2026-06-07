import Swal, { type SweetAlertOptions } from 'sweetalert2'

export function getSwalTheme(): Partial<SweetAlertOptions> {
  // Lire le theme sans hook (pour usage hors composant React)
  const stored = localStorage.getItem('theme-store')
  let isDark = false
  if (stored) {
    try {
      const parsed = JSON.parse(stored)
      isDark = parsed?.state?.dark ?? false
    } catch {}
  }
  
  if (!isDark) return {}
  
  return {
    background: '#1e293b',
    color: '#f1f5f9',
    confirmButtonColor: '#6366f1',
    cancelButtonColor: '#475569',
  }
}

export function swalDark(options: SweetAlertOptions): Promise<any> {
  return Swal.fire({ ...getSwalTheme(), ...options } as SweetAlertOptions)
}

export function swalConfirm(options: SweetAlertOptions): Promise<any> {
  return Swal.fire({
    ...getSwalTheme(),
    showCancelButton: true,
    confirmButtonText: 'Confirmer',
    cancelButtonText: 'Annuler',
    ...options,
  } as SweetAlertOptions)
}

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ThemeState {
  dark: boolean
  toggle: () => void
}

function getSystemDark(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      dark: getSystemDark(),
      toggle: () => set((s) => ({ dark: !s.dark })),
    }),
    { name: 'theme-store' }
  )
)

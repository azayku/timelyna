import { useThemeStore } from './themeStore'

export interface ChartTheme {
  textColor: string
  gridColor: string
  backgroundColor: string
  tooltipStyle: React.CSSProperties
  colors: string[]
}

export function useChartTheme(): ChartTheme {
  const { dark } = useThemeStore()
  return {
    textColor: dark ? '#94a3b8' : '#64748b',
    gridColor: dark ? '#1e293b' : '#f1f5f9',
    backgroundColor: dark ? '#1e293b' : '#ffffff',
    tooltipStyle: {
      borderRadius: 8,
      border: 'none',
      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
      fontSize: 12,
      backgroundColor: dark ? '#1e293b' : '#ffffff',
      color: dark ? '#e2e8f0' : '#1e293b',
    },
    colors: ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
  }
}

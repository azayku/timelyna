import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  fetchNotificationPreferences,
  updateNotificationPreferences,
} from './api'
import type { NotificationPreference } from './types'

const KEYS = {
  all: ['notifications'] as const,
  preferences: ['notification-preferences'] as const,
}

export function useNotifications() {
  return useQuery({
    queryKey: KEYS.all,
    queryFn: () => fetchNotifications(),
    refetchInterval: 30_000, // poll every 30s
  })
}

export function useUnreadCount() {
  const { data = [] } = useNotifications()
  return data.filter((n) => !n.is_read).length
}

export function useMarkRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => markNotificationRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}

export function useMarkAllRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}

export function useNotificationPreferences() {
  return useQuery({
    queryKey: KEYS.preferences,
    queryFn: fetchNotificationPreferences,
  })
}

export function useUpdateNotificationPreferences() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (prefs: NotificationPreference[]) => updateNotificationPreferences(prefs),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.preferences }),
  })
}

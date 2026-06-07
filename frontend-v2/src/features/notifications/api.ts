import { apiClient } from '../../lib/apiClient'
import type { Notification, NotificationPreference } from './types'

export function fetchNotifications(unreadOnly = false): Promise<Notification[]> {
  return apiClient.get<Notification[]>(`/notifications${unreadOnly ? '?unread=true' : ''}`)
}

export function markNotificationRead(id: number): Promise<void> {
  return apiClient.post(`/notifications/${id}/read`, {})
}

export function markAllNotificationsRead(): Promise<void> {
  return apiClient.post('/notifications/read-all', {})
}

export function fetchNotificationPreferences(): Promise<NotificationPreference[]> {
  return apiClient.get<NotificationPreference[]>('/notifications/preferences')
}

export function updateNotificationPreferences(prefs: NotificationPreference[]): Promise<void> {
  return apiClient.put('/notifications/preferences', prefs)
}

export interface Notification {
  id: number
  title: string
  message: string | null
  is_read: boolean
  created_at: string
  notification_type: string
}

export interface NotificationPreference {
  type: string
  email_enabled: boolean
  in_app_enabled: boolean
}

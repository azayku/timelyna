export async function requestNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) return false
  if (Notification.permission === 'granted') return true
  if (Notification.permission === 'denied') return false
  
  const permission = await Notification.requestPermission()
  return permission === 'granted'
}

export function sendBrowserNotification(title: string, options?: NotificationOptions): void {
  if (Notification.permission !== 'granted') return
  
  const notification = new Notification(title, {
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    ...options,
  })
  
  notification.onclick = () => {
    window.focus()
    notification.close()
  }
}

export function notifyTimesheetApproved(employeeName: string): void {
  sendBrowserNotification('Timesheet approuvé ✓', {
    body: `Les heures de ${employeeName} ont été approuvées`,
    tag: 'timesheet-approved',
  })
}

export function notifyTimesheetRejected(reason?: string): void {
  sendBrowserNotification('Timesheet rejeté', {
    body: reason ? `Raison : ${reason}` : 'Votre timesheet a été rejeté',
    tag: 'timesheet-rejected',
  })
}

export function notifyPendingApprovals(count: number): void {
  sendBrowserNotification(`${count} timesheet(s) à approuver`, {
    body: 'Des timesheets attendent votre validation',
    tag: 'pending-approvals',
  })
}

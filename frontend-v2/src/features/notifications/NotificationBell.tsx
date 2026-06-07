import { useState } from 'react'
import { Bell } from 'lucide-react'
import { useUnreadCount } from './hooks'
import NotificationDrawer from './NotificationDrawer'

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const unread = useUnreadCount()

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="relative p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
        aria-label="Notifications"
      >
        <Bell size={20} />
        {unread > 0 && (
          <span className="absolute top-1 right-1 inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold text-white bg-red-500 rounded-full">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>
      <NotificationDrawer open={open} onClose={() => setOpen(false)} />
    </>
  )
}

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useStore } from '@/store/useStore'

const icons = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertCircle,
}

const colors = {
  info: 'border-edge-500 bg-edge-500/10',
  success: 'border-success-500 bg-success-500/10',
  warning: 'border-warning-500 bg-warning-500/10',
  error: 'border-danger-500 bg-danger-500/10',
}

const iconColors = {
  info: 'text-edge-400',
  success: 'text-success-400',
  warning: 'text-warning-400',
  error: 'text-danger-400',
}

export function Toaster() {
  const { notifications, markNotificationRead } = useStore()
  const [visible, setVisible] = useState<string[]>([])

  useEffect(() => {
    const unread = notifications.filter((n) => !n.read).slice(0, 5)
    setVisible(unread.map((n) => n.id))

    // Auto-dismiss after 5 seconds
    unread.forEach((n) => {
      setTimeout(() => {
        markNotificationRead(n.id)
      }, 5000)
    })
  }, [notifications, markNotificationRead])

  const visibleNotifications = notifications.filter((n) => visible.includes(n.id))

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence>
        {visibleNotifications.map((notification) => {
          const Icon = icons[notification.type]
          return (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 100, scale: 0.95 }}
              className={cn(
                'glass-card border px-4 py-3 pr-10 min-w-[320px] max-w-[420px] relative',
                colors[notification.type]
              )}
            >
              <div className="flex items-start gap-3">
                <Icon className={cn('w-5 h-5 mt-0.5', iconColors[notification.type])} />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-white">{notification.title}</p>
                  <p className="text-sm text-slate-400 mt-0.5">{notification.message}</p>
                </div>
              </div>
              <button
                onClick={() => markNotificationRead(notification.id)}
                className="absolute top-3 right-3 text-slate-500 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}

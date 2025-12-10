import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bell,
  Search,
  Moon,
  Sun,
  Upload,
  Download,
  HelpCircle,
  X,
} from 'lucide-react'
import { useStore } from '@/store/useStore'
import { cn } from '@/lib/utils'

export default function Header() {
  const { darkMode, toggleDarkMode, notifications, alerts } = useStore()
  const [showNotifications, setShowNotifications] = useState(false)
  const [showSearch, setShowSearch] = useState(false)

  const unreadCount = notifications.filter((n) => !n.read).length
  const activeAlerts = alerts.filter((a) => !a.acknowledged).length

  return (
    <header className="h-16 border-b border-slate-800/50 bg-slate-900/50 backdrop-blur-xl sticky top-0 z-30">
      <div className="h-full px-6 flex items-center justify-between">
        {/* Search */}
        <div className="flex-1 max-w-xl">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type="text"
              placeholder="Search services, metrics, shortcuts..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-edge-500/50 focus:ring-1 focus:ring-edge-500/50 transition-all"
              onFocus={() => setShowSearch(true)}
              onBlur={() => setTimeout(() => setShowSearch(false), 200)}
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
              <kbd className="px-2 py-0.5 text-xs bg-slate-700 rounded text-slate-400">
                ⌘K
              </kbd>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Upload */}
          <button className="p-2.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors">
            <Upload className="w-5 h-5" />
          </button>

          {/* Download */}
          <button className="p-2.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors">
            <Download className="w-5 h-5" />
          </button>

          {/* Theme toggle */}
          <button
            onClick={toggleDarkMode}
            className="p-2.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
          >
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>

          {/* Help */}
          <button className="p-2.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors">
            <HelpCircle className="w-5 h-5" />
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className={cn(
                'p-2.5 rounded-xl transition-colors relative',
                showNotifications
                  ? 'bg-edge-500/20 text-edge-400'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )}
            >
              <Bell className="w-5 h-5" />
              {(unreadCount > 0 || activeAlerts > 0) && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-danger-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                  {unreadCount + activeAlerts}
                </span>
              )}
            </button>

            <AnimatePresence>
              {showNotifications && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute right-0 top-full mt-2 w-96 glass-card border border-slate-700/50 overflow-hidden"
                >
                  <div className="p-4 border-b border-slate-800/50 flex items-center justify-between">
                    <h3 className="font-semibold text-white">Notifications</h3>
                    <button
                      onClick={() => setShowNotifications(false)}
                      className="text-slate-400 hover:text-white"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {notifications.length === 0 && alerts.length === 0 ? (
                      <div className="p-8 text-center text-slate-500">
                        No notifications
                      </div>
                    ) : (
                      <>
                        {alerts.slice(0, 3).map((alert) => (
                          <div
                            key={alert.id}
                            className="p-4 border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                          >
                            <div className="flex items-start gap-3">
                              <div
                                className={cn(
                                  'w-2 h-2 rounded-full mt-2',
                                  alert.severity === 'critical' && 'bg-danger-500',
                                  alert.severity === 'high' && 'bg-warning-500',
                                  alert.severity === 'medium' && 'bg-edge-500',
                                  alert.severity === 'low' && 'bg-slate-500'
                                )}
                              />
                              <div>
                                <p className="font-medium text-white">{alert.service}</p>
                                <p className="text-sm text-slate-400">{alert.message}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                        {notifications.slice(0, 5).map((notif) => (
                          <div
                            key={notif.id}
                            className={cn(
                              'p-4 border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors',
                              !notif.read && 'bg-slate-800/20'
                            )}
                          >
                            <p className="font-medium text-white">{notif.title}</p>
                            <p className="text-sm text-slate-400">{notif.message}</p>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </header>
  )
}

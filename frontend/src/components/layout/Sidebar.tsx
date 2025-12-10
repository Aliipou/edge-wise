import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  Network,
  FlaskConical,
  Gamepad2,
  AlertTriangle,
  Trophy,
  Settings,
  ChevronLeft,
  Zap,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useStore } from '@/store/useStore'

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/explorer', icon: Network, label: 'Graph Explorer' },
  { path: '/simulation', icon: FlaskConical, label: 'Simulation' },
  { path: '/playground', icon: Gamepad2, label: 'Playground' },
  { path: '/alerts', icon: AlertTriangle, label: 'Alerts' },
  { path: '/leaderboard', icon: Trophy, label: 'Leaderboard' },
  { path: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useStore()

  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarCollapsed ? 80 : 256 }}
      className="fixed left-0 top-0 h-screen bg-slate-900/80 backdrop-blur-xl border-r border-slate-800/50 z-40 flex flex-col"
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/50">
        <NavLink to="/" className="flex items-center gap-3 group">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-edge-500 to-neural-500 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-edge-500 to-neural-500 blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
          </div>
          {!sidebarCollapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-display font-bold text-xl gradient-text"
            >
              EdgeWise
            </motion.span>
          )}
        </NavLink>
        <button
          onClick={toggleSidebar}
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
        >
          <ChevronLeft
            className={cn('w-5 h-5 transition-transform', sidebarCollapsed && 'rotate-180')}
          />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-1 px-3">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200',
                    'text-slate-400 hover:text-white hover:bg-slate-800/50',
                    isActive && 'bg-gradient-to-r from-edge-500/20 to-neural-500/20 text-white border border-edge-500/30'
                  )
                }
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="font-medium"
                  >
                    {item.label}
                  </motion.span>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-slate-800/50">
        <div
          className={cn(
            'flex items-center gap-3',
            sidebarCollapsed && 'justify-center'
          )}
        >
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-edge-500 to-neural-500 flex items-center justify-center text-white font-bold">
            DU
          </div>
          {!sidebarCollapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex-1 min-w-0"
            >
              <p className="font-medium text-white truncate">Demo User</p>
              <p className="text-sm text-slate-400">1,250 points</p>
            </motion.div>
          )}
        </div>
      </div>
    </motion.aside>
  )
}

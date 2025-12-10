import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import { useStore } from '@/store/useStore'
import { cn } from '@/lib/utils'

export default function Layout() {
  const { sidebarCollapsed } = useStore()

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Grid background */}
      <div className="fixed inset-0 grid-bg opacity-50 pointer-events-none" />

      {/* Gradient orbs */}
      <div className="fixed top-0 left-1/4 w-96 h-96 bg-edge-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-96 h-96 bg-neural-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative flex">
        <Sidebar />
        <div
          className={cn(
            'flex-1 min-h-screen transition-all duration-300',
            sidebarCollapsed ? 'ml-20' : 'ml-64'
          )}
        >
          <Header />
          <main className="p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Service, Edge, AnalyzeResponse, NodeMetrics, Shortcut } from '@/lib/api'

interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: Date
  read: boolean
}

interface Alert {
  id: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  type: 'bottleneck' | 'latency' | 'error_rate' | 'load' | 'prediction'
  service: string
  message: string
  timestamp: Date
  acknowledged: boolean
  prediction?: {
    probability: number
    timeframe: string
    recommendation: string
  }
}

interface User {
  id: string
  name: string
  avatar?: string
  score: number
  rank: number
  achievements: string[]
  simulationsRun: number
  shortcutsApplied: number
}

interface SimulationResult {
  id: string
  timestamp: Date
  originalMetrics: AnalyzeResponse['metrics']
  modifiedMetrics: AnalyzeResponse['metrics']
  appliedShortcuts: Shortcut[]
  improvement: number
  userId: string
}

interface AppState {
  // Theme
  darkMode: boolean
  toggleDarkMode: () => void

  // Graph data
  services: Service[]
  edges: Edge[]
  analysisResult: AnalyzeResponse | null
  selectedNode: string | null
  setServices: (services: Service[]) => void
  setEdges: (edges: Edge[]) => void
  setAnalysisResult: (result: AnalyzeResponse | null) => void
  setSelectedNode: (node: string | null) => void

  // Notifications
  notifications: Notification[]
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markNotificationRead: (id: string) => void
  clearNotifications: () => void

  // Alerts
  alerts: Alert[]
  addAlert: (alert: Omit<Alert, 'id' | 'timestamp' | 'acknowledged'>) => void
  acknowledgeAlert: (id: string) => void
  clearAlerts: () => void

  // Gamification
  currentUser: User | null
  leaderboard: User[]
  setCurrentUser: (user: User) => void
  updateUserScore: (points: number) => void
  addAchievement: (achievement: string) => void

  // Simulations
  simulationHistory: SimulationResult[]
  addSimulationResult: (result: Omit<SimulationResult, 'id' | 'timestamp'>) => void

  // UI state
  sidebarCollapsed: boolean
  toggleSidebar: () => void
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Theme
      darkMode: true,
      toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),

      // Graph data
      services: [],
      edges: [],
      analysisResult: null,
      selectedNode: null,
      setServices: (services) => set({ services }),
      setEdges: (edges) => set({ edges }),
      setAnalysisResult: (result) => set({ analysisResult: result }),
      setSelectedNode: (node) => set({ selectedNode: node }),

      // Notifications
      notifications: [],
      addNotification: (notification) =>
        set((state) => ({
          notifications: [
            {
              ...notification,
              id: Math.random().toString(36).substring(7),
              timestamp: new Date(),
              read: false,
            },
            ...state.notifications,
          ].slice(0, 50),
        })),
      markNotificationRead: (id) =>
        set((state) => ({
          notifications: state.notifications.map((n) =>
            n.id === id ? { ...n, read: true } : n
          ),
        })),
      clearNotifications: () => set({ notifications: [] }),

      // Alerts
      alerts: [],
      addAlert: (alert) =>
        set((state) => ({
          alerts: [
            {
              ...alert,
              id: Math.random().toString(36).substring(7),
              timestamp: new Date(),
              acknowledged: false,
            },
            ...state.alerts,
          ].slice(0, 100),
        })),
      acknowledgeAlert: (id) =>
        set((state) => ({
          alerts: state.alerts.map((a) =>
            a.id === id ? { ...a, acknowledged: true } : a
          ),
        })),
      clearAlerts: () => set({ alerts: [] }),

      // Gamification
      currentUser: {
        id: 'demo-user',
        name: 'Demo User',
        score: 1250,
        rank: 42,
        achievements: ['first_analysis', 'shortcut_master'],
        simulationsRun: 15,
        shortcutsApplied: 8,
      },
      leaderboard: [
        { id: '1', name: 'Alice Chen', score: 5420, rank: 1, achievements: [], simulationsRun: 89, shortcutsApplied: 34 },
        { id: '2', name: 'Bob Smith', score: 4890, rank: 2, achievements: [], simulationsRun: 76, shortcutsApplied: 28 },
        { id: '3', name: 'Carol Davis', score: 4210, rank: 3, achievements: [], simulationsRun: 65, shortcutsApplied: 22 },
        { id: '4', name: 'David Kim', score: 3850, rank: 4, achievements: [], simulationsRun: 58, shortcutsApplied: 19 },
        { id: '5', name: 'Eve Johnson', score: 3420, rank: 5, achievements: [], simulationsRun: 45, shortcutsApplied: 15 },
      ],
      setCurrentUser: (user) => set({ currentUser: user }),
      updateUserScore: (points) =>
        set((state) => ({
          currentUser: state.currentUser
            ? { ...state.currentUser, score: state.currentUser.score + points }
            : null,
        })),
      addAchievement: (achievement) =>
        set((state) => ({
          currentUser: state.currentUser
            ? {
                ...state.currentUser,
                achievements: [...state.currentUser.achievements, achievement],
              }
            : null,
        })),

      // Simulations
      simulationHistory: [],
      addSimulationResult: (result) =>
        set((state) => ({
          simulationHistory: [
            {
              ...result,
              id: Math.random().toString(36).substring(7),
              timestamp: new Date(),
            },
            ...state.simulationHistory,
          ].slice(0, 50),
        })),

      // UI state
      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    }),
    {
      name: 'edgewise-storage',
      partialize: (state) => ({
        darkMode: state.darkMode,
        sidebarCollapsed: state.sidebarCollapsed,
        currentUser: state.currentUser,
      }),
    }
  )
)

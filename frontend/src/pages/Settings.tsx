import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  User,
  Bell,
  Palette,
  Shield,
  Database,
  Key,
  Globe,
  Moon,
  Sun,
  Monitor,
  Save,
  RefreshCw,
  Trash2,
  Download,
  Upload,
  ChevronRight,
  Check,
  AlertTriangle,
} from 'lucide-react'
import { useStore } from '@/store/useStore'
import { cn } from '@/lib/utils'

interface SettingSection {
  id: string
  title: string
  icon: typeof User
  description: string
}

const sections: SettingSection[] = [
  { id: 'profile', title: 'Profile', icon: User, description: 'Manage your account details' },
  { id: 'notifications', title: 'Notifications', icon: Bell, description: 'Configure alert preferences' },
  { id: 'appearance', title: 'Appearance', icon: Palette, description: 'Customize the interface' },
  { id: 'api', title: 'API & Integrations', icon: Key, description: 'Manage API keys and connections' },
  { id: 'data', title: 'Data Management', icon: Database, description: 'Export, import, and clear data' },
  { id: 'security', title: 'Security', icon: Shield, description: 'Security and privacy settings' },
]

export default function Settings() {
  const { addNotification, clearAlerts, clearNotifications } = useStore()
  const [activeSection, setActiveSection] = useState('profile')
  const [isSaving, setIsSaving] = useState(false)

  // Form states
  const [profile, setProfile] = useState({
    username: 'demo_user',
    email: 'demo@edgewise.io',
    organization: 'EdgeWise Demo',
    timezone: 'UTC',
  })

  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    criticalOnly: false,
    dailyDigest: true,
    weeklyReport: true,
    slackIntegration: false,
    webhookUrl: '',
  })

  const [appearance, setAppearance] = useState({
    theme: 'dark' as 'dark' | 'light' | 'system',
    accentColor: 'edge' as 'edge' | 'neural' | 'success',
    compactMode: false,
    animations: true,
    graphQuality: 'high' as 'low' | 'medium' | 'high',
  })

  const [api, setApi] = useState({
    apiKey: 'ew_live_xxxxx...xxxxx',
    webhookSecret: 'whsec_xxxxx...xxxxx',
    rateLimitPerMin: 100,
    prometheusEnabled: false,
    jaegerEnabled: false,
  })

  const handleSave = async () => {
    setIsSaving(true)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))
    setIsSaving(false)
    addNotification({
      type: 'success',
      title: 'Settings Saved',
      message: 'Your preferences have been updated successfully',
    })
  }

  const handleClearData = () => {
    clearAlerts()
    clearNotifications()
    addNotification({
      type: 'success',
      title: 'Data Cleared',
      message: 'All local data has been cleared',
    })
  }

  const handleExportData = () => {
    const data = {
      profile,
      notifications,
      appearance,
      exportedAt: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'edgewise-settings.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const renderSection = () => {
    switch (activeSection) {
      case 'profile':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Username</label>
              <input
                type="text"
                value={profile.username}
                onChange={(e) => setProfile({ ...profile, username: e.target.value })}
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-edge-500/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Email</label>
              <input
                type="email"
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-edge-500/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Organization</label>
              <input
                type="text"
                value={profile.organization}
                onChange={(e) => setProfile({ ...profile, organization: e.target.value })}
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-edge-500/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Timezone</label>
              <select
                value={profile.timezone}
                onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-edge-500/50"
              >
                <option value="UTC">UTC</option>
                <option value="America/New_York">Eastern Time</option>
                <option value="America/Los_Angeles">Pacific Time</option>
                <option value="Europe/London">London</option>
                <option value="Europe/Paris">Paris</option>
                <option value="Asia/Tokyo">Tokyo</option>
              </select>
            </div>
          </div>
        )

      case 'notifications':
        return (
          <div className="space-y-6">
            <ToggleSetting
              label="Email Alerts"
              description="Receive email notifications for important alerts"
              enabled={notifications.emailAlerts}
              onChange={(v) => setNotifications({ ...notifications, emailAlerts: v })}
            />
            <ToggleSetting
              label="Critical Alerts Only"
              description="Only notify for critical severity alerts"
              enabled={notifications.criticalOnly}
              onChange={(v) => setNotifications({ ...notifications, criticalOnly: v })}
            />
            <ToggleSetting
              label="Daily Digest"
              description="Receive a daily summary of all alerts"
              enabled={notifications.dailyDigest}
              onChange={(v) => setNotifications({ ...notifications, dailyDigest: v })}
            />
            <ToggleSetting
              label="Weekly Report"
              description="Get weekly optimization insights"
              enabled={notifications.weeklyReport}
              onChange={(v) => setNotifications({ ...notifications, weeklyReport: v })}
            />
            <div className="pt-4 border-t border-slate-800">
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Webhook URL (Optional)
              </label>
              <input
                type="url"
                value={notifications.webhookUrl}
                onChange={(e) => setNotifications({ ...notifications, webhookUrl: e.target.value })}
                placeholder="https://your-webhook-endpoint.com/alerts"
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-edge-500/50"
              />
            </div>
          </div>
        )

      case 'appearance':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-3">Theme</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'dark', icon: Moon, label: 'Dark' },
                  { value: 'light', icon: Sun, label: 'Light' },
                  { value: 'system', icon: Monitor, label: 'System' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setAppearance({ ...appearance, theme: option.value as any })}
                    className={cn(
                      'p-4 rounded-xl border flex flex-col items-center gap-2 transition-all',
                      appearance.theme === option.value
                        ? 'bg-edge-500/20 border-edge-500/50 text-edge-400'
                        : 'bg-slate-800/50 border-slate-700/50 text-slate-400 hover:border-slate-600'
                    )}
                  >
                    <option.icon className="w-6 h-6" />
                    <span className="text-sm font-medium">{option.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-3">Accent Color</label>
              <div className="flex gap-3">
                {[
                  { value: 'edge', color: 'bg-edge-500', label: 'Cyan' },
                  { value: 'neural', color: 'bg-neural-500', label: 'Purple' },
                  { value: 'success', color: 'bg-success-500', label: 'Green' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setAppearance({ ...appearance, accentColor: option.value as any })}
                    className={cn(
                      'px-4 py-2 rounded-xl border flex items-center gap-2 transition-all',
                      appearance.accentColor === option.value
                        ? 'border-white/50'
                        : 'border-slate-700/50 hover:border-slate-600'
                    )}
                  >
                    <div className={cn('w-4 h-4 rounded-full', option.color)} />
                    <span className="text-sm text-slate-300">{option.label}</span>
                    {appearance.accentColor === option.value && (
                      <Check className="w-4 h-4 text-success-400" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-3">Graph Quality</label>
              <div className="flex gap-3">
                {(['low', 'medium', 'high'] as const).map((quality) => (
                  <button
                    key={quality}
                    onClick={() => setAppearance({ ...appearance, graphQuality: quality })}
                    className={cn(
                      'px-4 py-2 rounded-xl border capitalize transition-all',
                      appearance.graphQuality === quality
                        ? 'bg-edge-500/20 border-edge-500/50 text-edge-400'
                        : 'border-slate-700/50 text-slate-400 hover:border-slate-600'
                    )}
                  >
                    {quality}
                  </button>
                ))}
              </div>
            </div>

            <ToggleSetting
              label="Compact Mode"
              description="Reduce spacing and padding throughout the UI"
              enabled={appearance.compactMode}
              onChange={(v) => setAppearance({ ...appearance, compactMode: v })}
            />
            <ToggleSetting
              label="Animations"
              description="Enable smooth transitions and animations"
              enabled={appearance.animations}
              onChange={(v) => setAppearance({ ...appearance, animations: v })}
            />
          </div>
        )

      case 'api':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">API Key</label>
              <div className="flex gap-2">
                <input
                  type="password"
                  value={api.apiKey}
                  readOnly
                  className="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white font-mono"
                />
                <button className="px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-400 hover:text-white transition-colors">
                  <RefreshCw className="w-5 h-5" />
                </button>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Use this key to authenticate API requests
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Rate Limit (requests/min)
              </label>
              <input
                type="number"
                value={api.rateLimitPerMin}
                onChange={(e) => setApi({ ...api, rateLimitPerMin: parseInt(e.target.value) })}
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white focus:outline-none focus:border-edge-500/50"
              />
            </div>

            <div className="pt-4 border-t border-slate-800">
              <h3 className="text-sm font-medium text-white mb-4">Integrations</h3>
              <ToggleSetting
                label="Prometheus Metrics"
                description="Export metrics in Prometheus format"
                enabled={api.prometheusEnabled}
                onChange={(v) => setApi({ ...api, prometheusEnabled: v })}
              />
              <div className="mt-4">
                <ToggleSetting
                  label="Jaeger Tracing"
                  description="Enable distributed tracing with Jaeger"
                  enabled={api.jaegerEnabled}
                  onChange={(v) => setApi({ ...api, jaegerEnabled: v })}
                />
              </div>
            </div>
          </div>
        )

      case 'data':
        return (
          <div className="space-y-6">
            <div className="p-4 bg-slate-800/30 rounded-xl">
              <h3 className="text-white font-medium mb-2">Export Data</h3>
              <p className="text-sm text-slate-400 mb-4">
                Download all your settings and analysis history
              </p>
              <button
                onClick={handleExportData}
                className="px-4 py-2 bg-edge-500/20 text-edge-400 rounded-lg hover:bg-edge-500/30 transition-colors flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export Settings
              </button>
            </div>

            <div className="p-4 bg-slate-800/30 rounded-xl">
              <h3 className="text-white font-medium mb-2">Import Data</h3>
              <p className="text-sm text-slate-400 mb-4">
                Restore settings from a previous export
              </p>
              <label className="px-4 py-2 bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors flex items-center gap-2 cursor-pointer inline-flex">
                <Upload className="w-4 h-4" />
                Import Settings
                <input type="file" accept=".json" className="hidden" />
              </label>
            </div>

            <div className="p-4 bg-danger-500/10 border border-danger-500/30 rounded-xl">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-danger-400 mt-0.5" />
                <div>
                  <h3 className="text-white font-medium mb-2">Clear All Data</h3>
                  <p className="text-sm text-slate-400 mb-4">
                    This will clear all local data including alerts, notifications, and analysis history.
                    This action cannot be undone.
                  </p>
                  <button
                    onClick={handleClearData}
                    className="px-4 py-2 bg-danger-500/20 text-danger-400 rounded-lg hover:bg-danger-500/30 transition-colors flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Clear All Data
                  </button>
                </div>
              </div>
            </div>
          </div>
        )

      case 'security':
        return (
          <div className="space-y-6">
            <div className="p-4 bg-slate-800/30 rounded-xl">
              <h3 className="text-white font-medium mb-2">Two-Factor Authentication</h3>
              <p className="text-sm text-slate-400 mb-4">
                Add an extra layer of security to your account
              </p>
              <button className="px-4 py-2 bg-edge-500/20 text-edge-400 rounded-lg hover:bg-edge-500/30 transition-colors">
                Enable 2FA
              </button>
            </div>

            <div className="p-4 bg-slate-800/30 rounded-xl">
              <h3 className="text-white font-medium mb-2">Active Sessions</h3>
              <p className="text-sm text-slate-400 mb-4">
                Manage your active login sessions
              </p>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Globe className="w-5 h-5 text-slate-400" />
                    <div>
                      <p className="text-sm text-white">Chrome on Windows</p>
                      <p className="text-xs text-slate-500">Current session</p>
                    </div>
                  </div>
                  <span className="px-2 py-1 text-xs bg-success-500/20 text-success-400 rounded">
                    Active
                  </span>
                </div>
              </div>
            </div>

            <div className="p-4 bg-slate-800/30 rounded-xl">
              <h3 className="text-white font-medium mb-2">Change Password</h3>
              <p className="text-sm text-slate-400 mb-4">
                Update your account password
              </p>
              <button className="px-4 py-2 bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors">
                Change Password
              </button>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">Settings</h1>
          <p className="text-slate-400 mt-1">Manage your preferences and account</p>
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className={cn(
            'btn-glow flex items-center gap-2',
            isSaving && 'opacity-50 cursor-not-allowed'
          )}
        >
          {isSaving ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Changes
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Navigation */}
        <div className="glass-card p-4">
          <nav className="space-y-1">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors text-left',
                  activeSection === section.id
                    ? 'bg-edge-500/20 text-edge-400'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                )}
              >
                <section.icon className="w-5 h-5" />
                <div className="flex-1">
                  <p className="font-medium">{section.title}</p>
                  <p className="text-xs opacity-70">{section.description}</p>
                </div>
                <ChevronRight
                  className={cn(
                    'w-4 h-4 transition-transform',
                    activeSection === section.id && 'rotate-90'
                  )}
                />
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <motion.div
          key={activeSection}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="lg:col-span-3 glass-card p-6"
        >
          <h2 className="text-xl font-semibold text-white mb-6">
            {sections.find((s) => s.id === activeSection)?.title}
          </h2>
          {renderSection()}
        </motion.div>
      </div>
    </div>
  )
}

function ToggleSetting({
  label,
  description,
  enabled,
  onChange,
}: {
  label: string
  description: string
  enabled: boolean
  onChange: (value: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-white font-medium">{label}</p>
        <p className="text-sm text-slate-400">{description}</p>
      </div>
      <button
        onClick={() => onChange(!enabled)}
        className={cn(
          'relative w-12 h-6 rounded-full transition-colors',
          enabled ? 'bg-edge-500' : 'bg-slate-700'
        )}
      >
        <div
          className={cn(
            'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
            enabled ? 'translate-x-7' : 'translate-x-1'
          )}
        />
      </button>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  Bell,
  Filter,
  X,
  Clock,
  TrendingUp,
  Zap,
  RefreshCw,
} from 'lucide-react'
import { useStore } from '@/store/useStore'
import { cn } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'

const severityConfig = {
  critical: {
    icon: AlertCircle,
    color: 'text-danger-400',
    bgColor: 'bg-danger-500/10',
    borderColor: 'border-danger-500/30',
    label: 'Critical',
  },
  high: {
    icon: AlertTriangle,
    color: 'text-warning-400',
    bgColor: 'bg-warning-500/10',
    borderColor: 'border-warning-500/30',
    label: 'High',
  },
  medium: {
    icon: Info,
    color: 'text-edge-400',
    bgColor: 'bg-edge-500/10',
    borderColor: 'border-edge-500/30',
    label: 'Medium',
  },
  low: {
    icon: Bell,
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/30',
    label: 'Low',
  },
}

const typeConfig = {
  bottleneck: { label: 'Bottleneck', icon: Zap },
  latency: { label: 'Latency', icon: Clock },
  error_rate: { label: 'Error Rate', icon: AlertTriangle },
  load: { label: 'Load', icon: TrendingUp },
  prediction: { label: 'Prediction', icon: TrendingUp },
}

export default function Alerts() {
  const { alerts, addAlert, acknowledgeAlert, clearAlerts } = useStore()
  const [filter, setFilter] = useState<'all' | 'active' | 'acknowledged'>('all')
  const [severityFilter, setSeverityFilter] = useState<string | null>(null)

  // Simulate incoming alerts
  useEffect(() => {
    const services = [
      'api-gateway',
      'auth-service',
      'user-service',
      'order-service',
      'payment-service',
    ]

    const alertTypes: Array<'bottleneck' | 'latency' | 'error_rate' | 'load' | 'prediction'> = [
      'bottleneck',
      'latency',
      'error_rate',
      'load',
      'prediction',
    ]

    const severities: Array<'low' | 'medium' | 'high' | 'critical'> = [
      'low',
      'medium',
      'high',
      'critical',
    ]

    const messages = {
      bottleneck: 'High betweenness centrality detected',
      latency: 'P95 latency exceeded threshold',
      error_rate: 'Error rate spike detected',
      load: 'Unusual load pattern detected',
      prediction: 'Potential failure predicted in next 30 minutes',
    }

    // Add some initial alerts
    if (alerts.length === 0) {
      services.slice(0, 3).forEach((service, i) => {
        const type = alertTypes[i % alertTypes.length]
        addAlert({
          severity: severities[i % severities.length],
          type,
          service,
          message: messages[type],
          prediction:
            type === 'prediction'
              ? {
                  probability: 0.75 + Math.random() * 0.2,
                  timeframe: '30 minutes',
                  recommendation: 'Consider adding redundancy or scaling',
                }
              : undefined,
        })
      })
    }

    // Simulate new alerts
    const interval = setInterval(() => {
      if (Math.random() > 0.8) {
        const type = alertTypes[Math.floor(Math.random() * alertTypes.length)]
        addAlert({
          severity: severities[Math.floor(Math.random() * severities.length)],
          type,
          service: services[Math.floor(Math.random() * services.length)],
          message: messages[type],
          prediction:
            type === 'prediction'
              ? {
                  probability: 0.6 + Math.random() * 0.35,
                  timeframe: `${Math.floor(Math.random() * 60) + 10} minutes`,
                  recommendation: 'Monitor closely and prepare scaling resources',
                }
              : undefined,
        })
      }
    }, 15000)

    return () => clearInterval(interval)
  }, [addAlert, alerts.length])

  const filteredAlerts = alerts.filter((alert) => {
    if (filter === 'active' && alert.acknowledged) return false
    if (filter === 'acknowledged' && !alert.acknowledged) return false
    if (severityFilter && alert.severity !== severityFilter) return false
    return true
  })

  const activeCount = alerts.filter((a) => !a.acknowledged).length
  const criticalCount = alerts.filter((a) => !a.acknowledged && a.severity === 'critical').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">Alerts</h1>
          <p className="text-slate-400 mt-1">
            Predictive alerts and system notifications
          </p>
        </div>
        <div className="flex items-center gap-3">
          {criticalCount > 0 && (
            <div className="px-4 py-2 bg-danger-500/10 border border-danger-500/30 rounded-xl flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-danger-400" />
              <span className="text-danger-400 font-medium">{criticalCount} Critical</span>
            </div>
          )}
          <button
            onClick={clearAlerts}
            className="px-4 py-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatsCard
          label="Active Alerts"
          value={activeCount}
          icon={Bell}
          color="text-edge-400"
        />
        <StatsCard
          label="Critical"
          value={alerts.filter((a) => a.severity === 'critical' && !a.acknowledged).length}
          icon={AlertCircle}
          color="text-danger-400"
        />
        <StatsCard
          label="Predictions"
          value={alerts.filter((a) => a.type === 'prediction' && !a.acknowledged).length}
          icon={TrendingUp}
          color="text-neural-400"
        />
        <StatsCard
          label="Acknowledged"
          value={alerts.filter((a) => a.acknowledged).length}
          icon={CheckCircle}
          color="text-success-400"
        />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 bg-slate-800/50 rounded-xl p-1">
          {(['all', 'active', 'acknowledged'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize',
                filter === f
                  ? 'bg-edge-500/20 text-edge-400'
                  : 'text-slate-400 hover:text-white'
              )}
            >
              {f}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {(['critical', 'high', 'medium', 'low'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setSeverityFilter(severityFilter === s ? null : s)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors capitalize',
                severityFilter === s
                  ? severityConfig[s].bgColor + ' ' + severityConfig[s].borderColor + ' ' + severityConfig[s].color
                  : 'border-slate-700 text-slate-400 hover:text-white hover:border-slate-600'
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        <AnimatePresence>
          {filteredAlerts.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="glass-card p-12 text-center"
            >
              <CheckCircle className="w-16 h-16 mx-auto text-success-400 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">All Clear</h3>
              <p className="text-slate-400">No alerts match your current filters</p>
            </motion.div>
          ) : (
            filteredAlerts.map((alert) => {
              const config = severityConfig[alert.severity]
              const typeInfo = typeConfig[alert.type]
              const Icon = config.icon

              return (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  className={cn(
                    'glass-card p-6 border',
                    config.borderColor,
                    alert.acknowledged && 'opacity-60'
                  )}
                >
                  <div className="flex items-start gap-4">
                    <div className={cn('p-3 rounded-xl', config.bgColor)}>
                      <Icon className={cn('w-6 h-6', config.color)} />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold text-white">{alert.service}</span>
                            <span
                              className={cn(
                                'px-2 py-0.5 text-xs rounded',
                                config.bgColor,
                                config.color
                              )}
                            >
                              {config.label}
                            </span>
                            <span className="px-2 py-0.5 text-xs bg-slate-700/50 text-slate-300 rounded">
                              {typeInfo.label}
                            </span>
                          </div>
                          <p className="text-slate-300">{alert.message}</p>
                          <p className="text-sm text-slate-500 mt-1">
                            {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                          </p>
                        </div>

                        {!alert.acknowledged && (
                          <button
                            onClick={() => acknowledgeAlert(alert.id)}
                            className="px-4 py-2 text-sm text-slate-400 hover:text-white bg-slate-800/50 hover:bg-slate-800 rounded-lg transition-colors whitespace-nowrap"
                          >
                            Acknowledge
                          </button>
                        )}
                      </div>

                      {/* Prediction Details */}
                      {alert.prediction && (
                        <div className="mt-4 p-4 bg-neural-500/10 border border-neural-500/30 rounded-xl">
                          <div className="flex items-center gap-2 mb-2">
                            <TrendingUp className="w-4 h-4 text-neural-400" />
                            <span className="text-sm font-medium text-neural-400">
                              Predictive Analysis
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <p className="text-slate-500">Probability</p>
                              <p className="text-white font-medium">
                                {(alert.prediction.probability * 100).toFixed(0)}%
                              </p>
                            </div>
                            <div>
                              <p className="text-slate-500">Timeframe</p>
                              <p className="text-white font-medium">{alert.prediction.timeframe}</p>
                            </div>
                            <div>
                              <p className="text-slate-500">Recommendation</p>
                              <p className="text-white font-medium">{alert.prediction.recommendation}</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )
            })
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

function StatsCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string
  value: number
  icon: any
  color: string
}) {
  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="text-2xl font-display font-bold text-white mt-1">{value}</p>
        </div>
        <Icon className={cn('w-8 h-8', color)} />
      </div>
    </div>
  )
}

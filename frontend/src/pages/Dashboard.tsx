import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Network,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Zap,
  Clock,
  Activity,
  Target,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { cn, formatNumber, formatLatency, formatPercentage } from '@/lib/utils'
import { api, generateMockTopology } from '@/lib/api'
import { useStore } from '@/store/useStore'
import ForceGraph from '@/components/graph/ForceGraph'

const COLORS = ['#0ea5e9', '#a855f7', '#22c55e', '#f59e0b', '#ef4444']

// Generate mock time-series data
const generateTimeSeriesData = (points: number = 24) => {
  return Array.from({ length: points }, (_, i) => ({
    time: `${i}:00`,
    latency: Math.random() * 50 + 20,
    throughput: Math.random() * 1000 + 500,
    errors: Math.random() * 0.05,
  }))
}

export default function Dashboard() {
  const { setServices, setEdges, setAnalysisResult, analysisResult, addNotification } = useStore()
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  // Load initial data
  const { data: analysis, isLoading, error } = useQuery({
    queryKey: ['analysis'],
    queryFn: async () => {
      const { services, edges } = generateMockTopology(12)
      setServices(services)
      setEdges(edges)

      const result = await api.analyze({
        services,
        edges,
        options: { goal: 'balanced', k: 5 },
      })
      setAnalysisResult(result)
      return result
    },
    staleTime: 60000,
  })

  // Simulated real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      const random = Math.random()
      if (random < 0.1) {
        addNotification({
          type: 'warning',
          title: 'High Latency Detected',
          message: 'auth-service p95 latency exceeded 100ms threshold',
        })
      } else if (random < 0.05) {
        addNotification({
          type: 'error',
          title: 'Service Alert',
          message: 'payment-service error rate spike detected',
        })
      }
    }, 10000)

    return () => clearInterval(interval)
  }, [addNotification])

  const timeSeriesData = generateTimeSeriesData()

  const metrics = analysis?.metrics
  const nodeMetrics = analysis?.node_metrics || []
  const shortcuts = analysis?.shortcuts || []

  // Graph data for visualization
  const graphNodes = nodeMetrics.map((nm) => ({
    id: nm.name,
    name: nm.name,
    metrics: nm,
  }))

  // Prepare links from edges
  const { edges } = useStore.getState()
  const graphLinks = edges.map((e) => ({
    source: e.from,
    target: e.to,
    call_rate: e.call_rate,
    p50: e.p50,
  }))

  // Stats for cards
  const statsCards = [
    {
      title: 'Total Services',
      value: metrics?.node_count || 0,
      change: '+2',
      trend: 'up',
      icon: Network,
      color: 'from-edge-500 to-edge-600',
    },
    {
      title: 'Avg Path Length',
      value: metrics?.average_path_length?.toFixed(2) || '0',
      change: '-0.3',
      trend: 'down',
      icon: Target,
      color: 'from-neural-500 to-neural-600',
    },
    {
      title: 'Small-World Coef',
      value: metrics?.small_world_coefficient?.toFixed(2) || '0',
      change: '+0.5',
      trend: 'up',
      icon: Zap,
      color: 'from-success-500 to-success-600',
    },
    {
      title: 'Bottlenecks',
      value: metrics?.bottleneck_count || 0,
      change: '-1',
      trend: 'down',
      icon: AlertTriangle,
      color: 'from-warning-500 to-warning-600',
    },
  ]

  // Distribution data for pie chart
  const criticalityDistribution = [
    { name: 'Critical', value: nodeMetrics.filter((n) => n.is_bottleneck).length },
    { name: 'Hub', value: nodeMetrics.filter((n) => n.is_hub && !n.is_bottleneck).length },
    { name: 'Normal', value: nodeMetrics.filter((n) => !n.is_hub && !n.is_bottleneck).length },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-edge-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Analyzing topology...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">Real-time topology analysis and optimization insights</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Activity className="w-4 h-4 text-success-500 animate-pulse" />
          <span>Live</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsCards.map((stat, index) => (
          <motion.div
            key={stat.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="metric-card"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-slate-400 text-sm font-medium">{stat.title}</p>
                <p className="text-3xl font-display font-bold text-white mt-2">{stat.value}</p>
              </div>
              <div className={cn('p-3 rounded-xl bg-gradient-to-br', stat.color)}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-4">
              {stat.trend === 'up' ? (
                <ArrowUpRight className="w-4 h-4 text-success-400" />
              ) : (
                <ArrowDownRight className="w-4 h-4 text-danger-400" />
              )}
              <span
                className={cn(
                  'text-sm font-medium',
                  stat.trend === 'up' ? 'text-success-400' : 'text-danger-400'
                )}
              >
                {stat.change}
              </span>
              <span className="text-slate-500 text-sm">vs last hour</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Graph Visualization */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="lg:col-span-2 glass-card p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Service Topology</h2>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-400">
                {shortcuts.length} shortcuts suggested
              </span>
            </div>
          </div>
          <div className="h-[400px]">
            <ForceGraph
              nodes={graphNodes}
              links={graphLinks}
              selectedNode={selectedNode}
              onNodeSelect={setSelectedNode}
              shortcuts={shortcuts.map((s) => ({ from: s.from, to: s.to }))}
            />
          </div>
        </motion.div>

        {/* Shortcuts Panel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-card p-6"
        >
          <h2 className="text-xl font-semibold text-white mb-4">Suggested Shortcuts</h2>
          <div className="space-y-3 max-h-[360px] overflow-y-auto">
            {shortcuts.map((shortcut, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50 hover:border-edge-500/30 transition-colors cursor-pointer"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">{shortcut.from}</span>
                    <span className="text-slate-500">→</span>
                    <span className="text-white font-medium">{shortcut.to}</span>
                  </div>
                  <span className="text-success-400 font-semibold">
                    +{(shortcut.improvement * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Confidence: {(shortcut.confidence * 100).toFixed(0)}%</span>
                  <span className="text-slate-400">Risk: {(shortcut.risk_score * 100).toFixed(0)}%</span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Latency Trends */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="glass-card p-6"
        >
          <h2 className="text-xl font-semibold text-white mb-4">Latency Trends</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeSeriesData}>
                <defs>
                  <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="latency"
                  stroke="#0ea5e9"
                  fill="url(#latencyGradient)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Service Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="glass-card p-6"
        >
          <h2 className="text-xl font-semibold text-white mb-4">Service Distribution</h2>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={criticalityDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {criticalityDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute flex flex-col items-center">
              <span className="text-3xl font-bold text-white">{nodeMetrics.length}</span>
              <span className="text-slate-400 text-sm">Services</span>
            </div>
          </div>
          <div className="flex justify-center gap-6 mt-4">
            {criticalityDistribution.map((item, index) => (
              <div key={item.name} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: COLORS[index] }}
                />
                <span className="text-slate-400 text-sm">
                  {item.name} ({item.value})
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Recommendations */}
      {analysis?.graph_summary?.recommendations && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="glass-card p-6"
        >
          <h2 className="text-xl font-semibold text-white mb-4">Recommendations</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {analysis.graph_summary.recommendations.map((rec, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-4 bg-slate-800/30 rounded-xl"
              >
                <div className="p-2 bg-edge-500/20 rounded-lg">
                  <Zap className="w-5 h-5 text-edge-400" />
                </div>
                <p className="text-slate-300 text-sm leading-relaxed">{rec}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}

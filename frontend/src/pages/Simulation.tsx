import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play,
  Pause,
  RotateCcw,
  Plus,
  Minus,
  ChevronRight,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Zap,
} from 'lucide-react'
import { useStore } from '@/store/useStore'
import { api, generateMockTopology } from '@/lib/api'
import { cn } from '@/lib/utils'
import ForceGraph from '@/components/graph/ForceGraph'

interface SimulationShortcut {
  from: string
  to: string
  applied: boolean
}

export default function Simulation() {
  const { analysisResult, services, edges, addSimulationResult, updateUserScore, addNotification } = useStore()
  const [isRunning, setIsRunning] = useState(false)
  const [simulationShortcuts, setSimulationShortcuts] = useState<SimulationShortcut[]>([])
  const [beforeMetrics, setBeforeMetrics] = useState(analysisResult?.metrics || null)
  const [afterMetrics, setAfterMetrics] = useState<typeof beforeMetrics>(null)
  const [selectedShortcut, setSelectedShortcut] = useState<string | null>(null)

  const shortcuts = analysisResult?.shortcuts || []
  const nodeMetrics = analysisResult?.node_metrics || []

  // Initialize simulation shortcuts from analysis
  const initializeSimulation = useCallback(() => {
    setSimulationShortcuts(
      shortcuts.map((s) => ({
        from: s.from,
        to: s.to,
        applied: false,
      }))
    )
    setAfterMetrics(null)
  }, [shortcuts])

  // Toggle a shortcut
  const toggleShortcut = (from: string, to: string) => {
    setSimulationShortcuts((prev) =>
      prev.map((s) =>
        s.from === from && s.to === to ? { ...s, applied: !s.applied } : s
      )
    )
  }

  // Run simulation
  const runSimulation = async () => {
    setIsRunning(true)

    try {
      // Create modified edges with applied shortcuts
      const appliedShortcuts = simulationShortcuts.filter((s) => s.applied)
      const modifiedEdges = [
        ...edges,
        ...appliedShortcuts.map((s) => ({
          from: s.from,
          to: s.to,
          call_rate: 50,
          p50: 10,
          p95: 40,
          error_rate: 0,
        })),
      ]

      // Run analysis with modified topology
      const result = await api.analyze({
        services,
        edges: modifiedEdges,
        options: { goal: 'balanced', k: 0 },
      })

      setAfterMetrics(result.metrics)

      // Calculate improvement
      if (beforeMetrics) {
        const improvement =
          ((beforeMetrics.average_path_length - result.metrics.average_path_length) /
            beforeMetrics.average_path_length) *
          100

        // Award points
        if (improvement > 0) {
          const points = Math.round(improvement * 10)
          updateUserScore(points)
          addNotification({
            type: 'success',
            title: 'Simulation Complete',
            message: `You earned ${points} points for ${improvement.toFixed(1)}% improvement!`,
          })
        }

        // Save to history
        addSimulationResult({
          originalMetrics: beforeMetrics,
          modifiedMetrics: result.metrics,
          appliedShortcuts: shortcuts.filter((s) =>
            appliedShortcuts.some((as) => as.from === s.from && as.to === s.to)
          ),
          improvement,
          userId: 'demo-user',
        })
      }
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Simulation Failed',
        message: 'Could not run simulation. Please try again.',
      })
    } finally {
      setIsRunning(false)
    }
  }

  // Reset simulation
  const resetSimulation = () => {
    setSimulationShortcuts((prev) => prev.map((s) => ({ ...s, applied: false })))
    setAfterMetrics(null)
  }

  const graphNodes = nodeMetrics.map((nm) => ({
    id: nm.name,
    name: nm.name,
    metrics: nm,
  }))

  const graphLinks = edges.map((e) => ({
    source: e.from,
    target: e.to,
    call_rate: e.call_rate,
    p50: e.p50,
  }))

  const appliedShortcuts = simulationShortcuts.filter((s) => s.applied)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">Simulation</h1>
          <p className="text-slate-400 mt-1">
            Test topology changes before applying them to production
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={resetSimulation}
            className="px-4 py-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors flex items-center gap-2"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
          <button
            onClick={runSimulation}
            disabled={isRunning || appliedShortcuts.length === 0}
            className={cn(
              'btn-glow flex items-center gap-2',
              (isRunning || appliedShortcuts.length === 0) && 'opacity-50 cursor-not-allowed'
            )}
          >
            {isRunning ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run Simulation
              </>
            )}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Graph Preview */}
        <div className="lg:col-span-2 glass-card p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Topology Preview</h2>
          <div className="h-[500px]">
            <ForceGraph
              nodes={graphNodes}
              links={graphLinks}
              shortcuts={appliedShortcuts}
            />
          </div>
        </div>

        {/* Shortcut Selector */}
        <div className="glass-card p-6">
          <h2 className="text-xl font-semibold text-white mb-4">
            Available Shortcuts
            <span className="text-sm font-normal text-slate-400 ml-2">
              ({appliedShortcuts.length} selected)
            </span>
          </h2>

          <div className="space-y-3 max-h-[450px] overflow-y-auto">
            {simulationShortcuts.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-slate-400">No shortcuts available</p>
                <button
                  onClick={initializeSimulation}
                  className="mt-4 px-4 py-2 text-edge-400 hover:bg-edge-500/10 rounded-xl transition-colors"
                >
                  Load Suggestions
                </button>
              </div>
            ) : (
              simulationShortcuts.map((shortcut) => {
                const originalShortcut = shortcuts.find(
                  (s) => s.from === shortcut.from && s.to === shortcut.to
                )
                return (
                  <motion.div
                    key={`${shortcut.from}-${shortcut.to}`}
                    layout
                    className={cn(
                      'p-4 rounded-xl border transition-all cursor-pointer',
                      shortcut.applied
                        ? 'bg-success-500/10 border-success-500/50'
                        : 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600'
                    )}
                    onClick={() => toggleShortcut(shortcut.from, shortcut.to)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-white font-medium">{shortcut.from}</span>
                        <ChevronRight className="w-4 h-4 text-slate-500" />
                        <span className="text-white font-medium">{shortcut.to}</span>
                      </div>
                      <div
                        className={cn(
                          'w-6 h-6 rounded-full flex items-center justify-center transition-colors',
                          shortcut.applied ? 'bg-success-500' : 'bg-slate-700'
                        )}
                      >
                        {shortcut.applied && <CheckCircle className="w-4 h-4 text-white" />}
                      </div>
                    </div>
                    {originalShortcut && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-success-400">
                          +{(originalShortcut.improvement * 100).toFixed(1)}% improvement
                        </span>
                        <span className="text-slate-400">
                          {(originalShortcut.confidence * 100).toFixed(0)}% confidence
                        </span>
                      </div>
                    )}
                  </motion.div>
                )
              })
            )}
          </div>

          {simulationShortcuts.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-800/50">
              <button
                onClick={() =>
                  setSimulationShortcuts((prev) =>
                    prev.map((s) => ({ ...s, applied: true }))
                  )
                }
                className="w-full py-2 text-edge-400 hover:bg-edge-500/10 rounded-xl transition-colors text-sm"
              >
                Select All
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Metrics Comparison */}
      <AnimatePresence>
        {afterMetrics && beforeMetrics && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="glass-card p-6"
          >
            <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
              <Zap className="w-5 h-5 text-edge-400" />
              Simulation Results
            </h2>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <MetricComparison
                label="Avg Path Length"
                before={beforeMetrics.average_path_length}
                after={afterMetrics.average_path_length}
                lowerIsBetter
              />
              <MetricComparison
                label="Max Betweenness"
                before={beforeMetrics.max_betweenness}
                after={afterMetrics.max_betweenness}
                lowerIsBetter
              />
              <MetricComparison
                label="Clustering"
                before={beforeMetrics.average_clustering}
                after={afterMetrics.average_clustering}
              />
              <MetricComparison
                label="Small-World Coef"
                before={beforeMetrics.small_world_coefficient}
                after={afterMetrics.small_world_coefficient}
              />
            </div>

            <div className="mt-6 p-4 bg-slate-800/30 rounded-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400">Overall Improvement</p>
                  <p className="text-3xl font-display font-bold text-success-400 mt-1">
                    {(
                      ((beforeMetrics.average_path_length - afterMetrics.average_path_length) /
                        beforeMetrics.average_path_length) *
                      100
                    ).toFixed(1)}
                    %
                  </p>
                </div>
                <button className="btn-glow">
                  Apply to Production
                  <ChevronRight className="w-4 h-4 ml-2" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function MetricComparison({
  label,
  before,
  after,
  lowerIsBetter = false,
}: {
  label: string
  before: number
  after: number
  lowerIsBetter?: boolean
}) {
  const change = after - before
  const isImprovement = lowerIsBetter ? change < 0 : change > 0
  const percentChange = ((change / before) * 100).toFixed(1)

  return (
    <div className="p-4 bg-slate-800/50 rounded-xl">
      <p className="text-sm text-slate-400 mb-2">{label}</p>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs text-slate-500">Before</p>
          <p className="text-lg font-semibold text-slate-300">{before.toFixed(2)}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500">After</p>
          <p className="text-lg font-semibold text-white">{after.toFixed(2)}</p>
        </div>
      </div>
      <div
        className={cn(
          'mt-2 flex items-center gap-1 text-sm',
          isImprovement ? 'text-success-400' : 'text-danger-400'
        )}
      >
        {isImprovement ? (
          <TrendingDown className="w-4 h-4" />
        ) : (
          <TrendingUp className="w-4 h-4" />
        )}
        <span>
          {change > 0 ? '+' : ''}
          {percentChange}%
        </span>
      </div>
    </div>
  )
}

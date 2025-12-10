import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  Filter,
  Download,
  Settings,
  Info,
  X,
  ChevronRight,
  Activity,
  Server,
  GitBranch,
} from 'lucide-react'
import { useStore } from '@/store/useStore'
import { cn } from '@/lib/utils'
import ForceGraph from '@/components/graph/ForceGraph'

export default function GraphExplorer() {
  const { analysisResult, services, edges } = useStore()
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({
    showHubs: true,
    showBottlenecks: true,
    showNormal: true,
    showShortcuts: true,
    minDegree: 0,
  })

  const nodeMetrics = analysisResult?.node_metrics || []
  const shortcuts = analysisResult?.shortcuts || []

  // Filter nodes based on search and filters
  const filteredNodes = useMemo(() => {
    return nodeMetrics
      .filter((nm) => {
        if (searchQuery && !nm.name.toLowerCase().includes(searchQuery.toLowerCase())) {
          return false
        }
        if (!filters.showHubs && nm.is_hub && !nm.is_bottleneck) return false
        if (!filters.showBottlenecks && nm.is_bottleneck) return false
        if (!filters.showNormal && !nm.is_hub && !nm.is_bottleneck) return false
        if (nm.total_degree < filters.minDegree) return false
        return true
      })
      .map((nm) => ({
        id: nm.name,
        name: nm.name,
        metrics: nm,
      }))
  }, [nodeMetrics, searchQuery, filters])

  const filteredLinks = useMemo(() => {
    const nodeIds = new Set(filteredNodes.map((n) => n.id))
    return edges
      .filter((e) => nodeIds.has(e.from) && nodeIds.has(e.to))
      .map((e) => ({
        source: e.from,
        target: e.to,
        call_rate: e.call_rate,
        p50: e.p50,
      }))
  }, [edges, filteredNodes])

  const selectedNodeMetrics = selectedNode
    ? nodeMetrics.find((nm) => nm.name === selectedNode)
    : null

  return (
    <div className="h-[calc(100vh-7rem)] flex gap-6">
      {/* Main Graph Area */}
      <div className="flex-1 glass-card p-4 flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search services..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-edge-500/50 text-sm w-64"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={cn(
                'p-2 rounded-lg transition-colors',
                showFilters
                  ? 'bg-edge-500/20 text-edge-400'
                  : 'text-slate-400 hover:bg-slate-800'
              )}
            >
              <Filter className="w-5 h-5" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400">
              {filteredNodes.length} services • {filteredLinks.length} connections
            </span>
            <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
              <Download className="w-5 h-5" />
            </button>
            <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filters Panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-4 p-4 bg-slate-800/30 rounded-xl overflow-hidden"
            >
              <div className="flex flex-wrap gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.showHubs}
                    onChange={(e) => setFilters({ ...filters, showHubs: e.target.checked })}
                    className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-edge-500 focus:ring-edge-500"
                  />
                  <span className="text-sm text-slate-300">Show Hubs</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.showBottlenecks}
                    onChange={(e) => setFilters({ ...filters, showBottlenecks: e.target.checked })}
                    className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-edge-500 focus:ring-edge-500"
                  />
                  <span className="text-sm text-slate-300">Show Bottlenecks</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.showShortcuts}
                    onChange={(e) => setFilters({ ...filters, showShortcuts: e.target.checked })}
                    className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-edge-500 focus:ring-edge-500"
                  />
                  <span className="text-sm text-slate-300">Show Shortcuts</span>
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-400">Min Degree:</span>
                  <input
                    type="range"
                    min="0"
                    max="10"
                    value={filters.minDegree}
                    onChange={(e) => setFilters({ ...filters, minDegree: parseInt(e.target.value) })}
                    className="w-24"
                  />
                  <span className="text-sm text-white w-6">{filters.minDegree}</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Graph */}
        <div className="flex-1 min-h-0">
          <ForceGraph
            nodes={filteredNodes}
            links={filteredLinks}
            selectedNode={selectedNode}
            onNodeSelect={setSelectedNode}
            shortcuts={filters.showShortcuts ? shortcuts.map((s) => ({ from: s.from, to: s.to })) : []}
          />
        </div>
      </div>

      {/* Details Panel */}
      <AnimatePresence>
        {selectedNodeMetrics && (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 50 }}
            className="w-80 glass-card p-6 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="text-xl font-semibold text-white">{selectedNodeMetrics.name}</h3>
                <div className="flex items-center gap-2 mt-1">
                  {selectedNodeMetrics.is_hub && (
                    <span className="px-2 py-0.5 text-xs bg-neural-500/20 text-neural-400 rounded">
                      Hub
                    </span>
                  )}
                  {selectedNodeMetrics.is_bottleneck && (
                    <span className="px-2 py-0.5 text-xs bg-warning-500/20 text-warning-400 rounded">
                      Bottleneck
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Metrics */}
            <div className="space-y-4 flex-1 overflow-y-auto">
              <div>
                <h4 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  Connectivity
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <MetricItem label="In Degree" value={selectedNodeMetrics.in_degree} />
                  <MetricItem label="Out Degree" value={selectedNodeMetrics.out_degree} />
                  <MetricItem label="Total Degree" value={selectedNodeMetrics.total_degree} />
                  <MetricItem
                    label="Clustering"
                    value={selectedNodeMetrics.clustering_coefficient.toFixed(3)}
                  />
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  <Server className="w-4 h-4" />
                  Centrality
                </h4>
                <div className="space-y-3">
                  <MetricBar
                    label="Betweenness"
                    value={selectedNodeMetrics.betweenness_centrality}
                    max={1}
                  />
                  <MetricBar
                    label="Closeness"
                    value={selectedNodeMetrics.closeness_centrality}
                    max={1}
                  />
                  <MetricBar
                    label="PageRank"
                    value={selectedNodeMetrics.pagerank}
                    max={0.5}
                  />
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  <GitBranch className="w-4 h-4" />
                  Load
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <MetricItem
                    label="Incoming"
                    value={selectedNodeMetrics.incoming_load.toFixed(1)}
                    unit="req/s"
                  />
                  <MetricItem
                    label="Outgoing"
                    value={selectedNodeMetrics.outgoing_load.toFixed(1)}
                    unit="req/s"
                  />
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  Risk Assessment
                </h4>
                <div className="p-4 bg-slate-800/50 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-300">Vulnerability Score</span>
                    <span
                      className={cn(
                        'font-semibold',
                        selectedNodeMetrics.vulnerability_score > 0.5
                          ? 'text-danger-400'
                          : selectedNodeMetrics.vulnerability_score > 0.3
                          ? 'text-warning-400'
                          : 'text-success-400'
                      )}
                    >
                      {(selectedNodeMetrics.vulnerability_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full transition-all',
                        selectedNodeMetrics.vulnerability_score > 0.5
                          ? 'bg-danger-500'
                          : selectedNodeMetrics.vulnerability_score > 0.3
                          ? 'bg-warning-500'
                          : 'bg-success-500'
                      )}
                      style={{ width: `${selectedNodeMetrics.vulnerability_score * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-6 pt-4 border-t border-slate-800/50">
              <button className="w-full py-2.5 bg-gradient-to-r from-edge-500 to-neural-500 text-white font-medium rounded-xl hover:from-edge-400 hover:to-neural-400 transition-colors flex items-center justify-center gap-2">
                View in Simulation
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function MetricItem({
  label,
  value,
  unit,
}: {
  label: string
  value: string | number
  unit?: string
}) {
  return (
    <div className="p-3 bg-slate-800/50 rounded-lg">
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p className="text-lg font-semibold text-white">
        {value}
        {unit && <span className="text-xs text-slate-400 ml-1">{unit}</span>}
      </p>
    </div>
  )
}

function MetricBar({ label, value, max }: { label: string; value: number; max: number }) {
  const percentage = Math.min((value / max) * 100, 100)

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-slate-300">{label}</span>
        <span className="text-sm font-medium text-white">{value.toFixed(3)}</span>
      </div>
      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-edge-500 to-neural-500 rounded-full transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

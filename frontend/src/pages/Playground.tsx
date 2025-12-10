import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Plus,
  Trash2,
  Wand2,
  Upload,
  Download,
  RefreshCw,
  Save,
  Code,
  Eye,
} from 'lucide-react'
import { api, generateMockTopology, type Service, type Edge } from '@/lib/api'
import { useStore } from '@/store/useStore'
import { cn } from '@/lib/utils'
import ForceGraph from '@/components/graph/ForceGraph'

export default function Playground() {
  const { addNotification, updateUserScore } = useStore()
  const [services, setServices] = useState<Service[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [viewMode, setViewMode] = useState<'visual' | 'json'>('visual')
  const [newServiceName, setNewServiceName] = useState('')

  // Generate random topology
  const generateRandom = useCallback(() => {
    const { services, edges } = generateMockTopology(Math.floor(Math.random() * 8) + 5)
    setServices(services)
    setEdges(edges)
    setAnalysisResult(null)
    updateUserScore(5)
    addNotification({
      type: 'success',
      title: 'Topology Generated',
      message: `Created ${services.length} services with ${edges.length} connections`,
    })
  }, [addNotification, updateUserScore])

  // Add a service
  const addService = () => {
    if (!newServiceName.trim()) return
    const name = newServiceName.trim().toLowerCase().replace(/\s+/g, '-')
    if (services.some((s) => s.name === name)) {
      addNotification({
        type: 'warning',
        title: 'Service Exists',
        message: `A service named "${name}" already exists`,
      })
      return
    }

    setServices([
      ...services,
      {
        name,
        replicas: 1,
        tags: [],
        criticality: 'medium',
      },
    ])
    setNewServiceName('')
    setAnalysisResult(null)
  }

  // Remove a service
  const removeService = (name: string) => {
    setServices(services.filter((s) => s.name !== name))
    setEdges(edges.filter((e) => e.from !== name && e.to !== name))
    setAnalysisResult(null)
  }

  // Add an edge
  const addEdge = (from: string, to: string) => {
    if (from === to) return
    if (edges.some((e) => e.from === from && e.to === to)) return

    setEdges([
      ...edges,
      {
        from,
        to,
        call_rate: Math.random() * 100 + 10,
        p50: Math.random() * 20 + 5,
        p95: Math.random() * 100 + 30,
        error_rate: Math.random() * 0.01,
      },
    ])
    setAnalysisResult(null)
  }

  // Remove an edge
  const removeEdge = (from: string, to: string) => {
    setEdges(edges.filter((e) => !(e.from === from && e.to === to)))
    setAnalysisResult(null)
  }

  // Run analysis
  const runAnalysis = async () => {
    if (services.length < 2) {
      addNotification({
        type: 'warning',
        title: 'Not Enough Services',
        message: 'Add at least 2 services to run analysis',
      })
      return
    }

    setIsAnalyzing(true)
    try {
      const result = await api.analyze({
        services,
        edges,
        options: { goal: 'balanced', k: 5 },
      })
      setAnalysisResult(result)
      updateUserScore(20)
      addNotification({
        type: 'success',
        title: 'Analysis Complete',
        message: `Found ${result.shortcuts.length} optimization opportunities`,
      })
    } catch (error) {
      addNotification({
        type: 'error',
        title: 'Analysis Failed',
        message: 'Could not analyze topology. Check your configuration.',
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Export topology
  const exportTopology = () => {
    const data = JSON.stringify({ services, edges }, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'topology.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  // Import topology
  const importTopology = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target?.result as string)
        if (data.services && data.edges) {
          setServices(data.services)
          setEdges(data.edges)
          setAnalysisResult(null)
          addNotification({
            type: 'success',
            title: 'Import Successful',
            message: `Loaded ${data.services.length} services`,
          })
        }
      } catch (error) {
        addNotification({
          type: 'error',
          title: 'Import Failed',
          message: 'Invalid JSON file',
        })
      }
    }
    reader.readAsText(file)
  }

  const graphNodes = services.map((s) => ({
    id: s.name,
    name: s.name,
    metrics: analysisResult?.node_metrics?.find((nm: any) => nm.name === s.name),
  }))

  const graphLinks = edges.map((e) => ({
    source: e.from,
    target: e.to,
    call_rate: e.call_rate,
    p50: e.p50,
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold text-white">Playground</h1>
          <p className="text-slate-400 mt-1">
            Build and experiment with custom topologies
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={generateRandom}
            className="px-4 py-2 text-slate-300 hover:text-white bg-slate-800/50 hover:bg-slate-800 rounded-xl transition-colors flex items-center gap-2"
          >
            <Wand2 className="w-4 h-4" />
            Random
          </button>
          <label className="px-4 py-2 text-slate-300 hover:text-white bg-slate-800/50 hover:bg-slate-800 rounded-xl transition-colors flex items-center gap-2 cursor-pointer">
            <Upload className="w-4 h-4" />
            Import
            <input
              type="file"
              accept=".json"
              onChange={importTopology}
              className="hidden"
            />
          </label>
          <button
            onClick={exportTopology}
            disabled={services.length === 0}
            className="px-4 py-2 text-slate-300 hover:text-white bg-slate-800/50 hover:bg-slate-800 rounded-xl transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          <button
            onClick={runAnalysis}
            disabled={isAnalyzing || services.length < 2}
            className={cn(
              'btn-glow flex items-center gap-2',
              (isAnalyzing || services.length < 2) && 'opacity-50 cursor-not-allowed'
            )}
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Wand2 className="w-4 h-4" />
                Analyze
              </>
            )}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Editor Panel */}
        <div className="glass-card p-6">
          {/* View Toggle */}
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={() => setViewMode('visual')}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                viewMode === 'visual'
                  ? 'bg-edge-500/20 text-edge-400'
                  : 'text-slate-400 hover:text-white'
              )}
            >
              <Eye className="w-4 h-4 inline-block mr-1" />
              Visual
            </button>
            <button
              onClick={() => setViewMode('json')}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                viewMode === 'json'
                  ? 'bg-edge-500/20 text-edge-400'
                  : 'text-slate-400 hover:text-white'
              )}
            >
              <Code className="w-4 h-4 inline-block mr-1" />
              JSON
            </button>
          </div>

          {viewMode === 'visual' ? (
            <>
              {/* Add Service */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-slate-400 mb-2">Add Service</h3>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newServiceName}
                    onChange={(e) => setNewServiceName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addService()}
                    placeholder="service-name"
                    className="flex-1 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-edge-500/50 text-sm"
                  />
                  <button
                    onClick={addService}
                    className="p-2 bg-edge-500/20 hover:bg-edge-500/30 text-edge-400 rounded-lg transition-colors"
                  >
                    <Plus className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Services List */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-slate-400 mb-2">
                  Services ({services.length})
                </h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {services.map((service) => (
                    <div
                      key={service.name}
                      className="flex items-center justify-between p-2 bg-slate-800/30 rounded-lg group"
                    >
                      <span className="text-white text-sm">{service.name}</span>
                      <button
                        onClick={() => removeService(service.name)}
                        className="p-1 text-slate-500 hover:text-danger-400 opacity-0 group-hover:opacity-100 transition-all"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  {services.length === 0 && (
                    <p className="text-slate-500 text-sm text-center py-4">
                      No services yet
                    </p>
                  )}
                </div>
              </div>

              {/* Edges */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">
                  Connections ({edges.length})
                </h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {edges.map((edge) => (
                    <div
                      key={`${edge.from}-${edge.to}`}
                      className="flex items-center justify-between p-2 bg-slate-800/30 rounded-lg group"
                    >
                      <span className="text-white text-sm">
                        {edge.from} → {edge.to}
                      </span>
                      <button
                        onClick={() => removeEdge(edge.from, edge.to)}
                        className="p-1 text-slate-500 hover:text-danger-400 opacity-0 group-hover:opacity-100 transition-all"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  {edges.length === 0 && (
                    <p className="text-slate-500 text-sm text-center py-4">
                      No connections yet
                    </p>
                  )}
                </div>

                {/* Quick Edge Builder */}
                {services.length >= 2 && (
                  <div className="mt-4 p-3 bg-slate-800/20 rounded-lg">
                    <p className="text-xs text-slate-500 mb-2">Quick Add Edge</p>
                    <div className="flex gap-2">
                      <select
                        id="edge-from"
                        className="flex-1 px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-white text-sm"
                      >
                        {services.map((s) => (
                          <option key={s.name} value={s.name}>
                            {s.name}
                          </option>
                        ))}
                      </select>
                      <span className="text-slate-500 self-center">→</span>
                      <select
                        id="edge-to"
                        className="flex-1 px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-white text-sm"
                      >
                        {services.map((s) => (
                          <option key={s.name} value={s.name}>
                            {s.name}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => {
                          const from = (document.getElementById('edge-from') as HTMLSelectElement).value
                          const to = (document.getElementById('edge-to') as HTMLSelectElement).value
                          addEdge(from, to)
                        }}
                        className="p-1.5 bg-edge-500/20 hover:bg-edge-500/30 text-edge-400 rounded transition-colors"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="h-[400px]">
              <textarea
                value={JSON.stringify({ services, edges }, null, 2)}
                onChange={(e) => {
                  try {
                    const data = JSON.parse(e.target.value)
                    if (data.services) setServices(data.services)
                    if (data.edges) setEdges(data.edges)
                  } catch {}
                }}
                className="w-full h-full p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 font-mono text-sm resize-none focus:outline-none focus:border-edge-500/50"
              />
            </div>
          )}
        </div>

        {/* Graph Preview */}
        <div className="lg:col-span-2 glass-card p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Preview</h2>
          <div className="h-[500px]">
            {services.length > 0 ? (
              <ForceGraph
                nodes={graphNodes}
                links={graphLinks}
                shortcuts={analysisResult?.shortcuts?.map((s: any) => ({
                  from: s.from,
                  to: s.to,
                })) || []}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500">
                <div className="text-center">
                  <Wand2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Add services or generate a random topology to start</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Analysis Results */}
      {analysisResult && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6"
        >
          <h2 className="text-xl font-semibold text-white mb-4">Analysis Results</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <ResultCard
              label="Avg Path Length"
              value={analysisResult.metrics.average_path_length.toFixed(2)}
            />
            <ResultCard
              label="Clustering"
              value={analysisResult.metrics.average_clustering.toFixed(3)}
            />
            <ResultCard
              label="Small-World Coef"
              value={analysisResult.metrics.small_world_coefficient.toFixed(2)}
            />
            <ResultCard
              label="Shortcuts Found"
              value={analysisResult.shortcuts.length}
            />
          </div>
        </motion.div>
      )}
    </div>
  )
}

function ResultCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="p-4 bg-slate-800/50 rounded-xl">
      <p className="text-sm text-slate-400 mb-1">{label}</p>
      <p className="text-2xl font-display font-bold text-white">{value}</p>
    </div>
  )
}

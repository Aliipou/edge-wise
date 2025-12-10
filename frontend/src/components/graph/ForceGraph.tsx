import { useEffect, useRef, useState, useCallback } from 'react'
import * as d3 from 'd3'
import { motion } from 'framer-motion'
import { ZoomIn, ZoomOut, Maximize2, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { NodeMetrics } from '@/lib/api'

interface Node {
  id: string
  name: string
  metrics?: NodeMetrics
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

interface Link {
  source: string | Node
  target: string | Node
  call_rate: number
  p50: number
  isShortcut?: boolean
}

interface ForceGraphProps {
  nodes: Node[]
  links: Link[]
  selectedNode?: string | null
  onNodeSelect?: (nodeId: string | null) => void
  shortcuts?: Array<{ from: string; to: string }>
  className?: string
}

export default function ForceGraph({
  nodes,
  links,
  selectedNode,
  onNodeSelect,
  shortcuts = [],
  className,
}: ForceGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

  // Handle resize
  useEffect(() => {
    if (!containerRef.current) return

    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect
      setDimensions({ width, height })
    })

    observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  // D3 Force Simulation
  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const { width, height } = dimensions

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    // Main group for zoom/pan
    const g = svg.append('g')

    // Create gradient definitions
    const defs = svg.append('defs')

    // Node gradient
    const nodeGradient = defs.append('radialGradient')
      .attr('id', 'nodeGradient')
      .attr('cx', '30%')
      .attr('cy', '30%')

    nodeGradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#38bdf8')

    nodeGradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', '#0284c7')

    // Hub gradient
    const hubGradient = defs.append('radialGradient')
      .attr('id', 'hubGradient')
      .attr('cx', '30%')
      .attr('cy', '30%')

    hubGradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#c084fc')

    hubGradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', '#7c3aed')

    // Bottleneck gradient
    const bottleneckGradient = defs.append('radialGradient')
      .attr('id', 'bottleneckGradient')
      .attr('cx', '30%')
      .attr('cy', '30%')

    bottleneckGradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#fbbf24')

    bottleneckGradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', '#d97706')

    // Glow filter
    const filter = defs.append('filter')
      .attr('id', 'glow')
      .attr('x', '-50%')
      .attr('y', '-50%')
      .attr('width', '200%')
      .attr('height', '200%')

    filter.append('feGaussianBlur')
      .attr('stdDeviation', '3')
      .attr('result', 'coloredBlur')

    const feMerge = filter.append('feMerge')
    feMerge.append('feMergeNode').attr('in', 'coloredBlur')
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    // Process data
    const nodeMap = new Map(nodes.map((n) => [n.id, { ...n }]))
    const processedLinks = links.map((l) => ({
      ...l,
      source: typeof l.source === 'string' ? l.source : l.source.id,
      target: typeof l.target === 'string' ? l.target : l.target.id,
    }))

    // Add shortcut links
    const shortcutSet = new Set(shortcuts.map((s) => `${s.from}-${s.to}`))
    shortcuts.forEach((s) => {
      if (!processedLinks.some((l) => l.source === s.from && l.target === s.to)) {
        processedLinks.push({
          source: s.from,
          target: s.to,
          call_rate: 0,
          p50: 0,
          isShortcut: true,
        })
      }
    })

    // Create simulation
    const simulation = d3.forceSimulation(Array.from(nodeMap.values()) as d3.SimulationNodeDatum[])
      .force('link', d3.forceLink(processedLinks)
        .id((d: any) => d.id)
        .distance(100)
        .strength(0.5))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40))

    // Draw links
    const link = g.append('g')
      .selectAll('line')
      .data(processedLinks)
      .join('line')
      .attr('stroke', (d) => d.isShortcut || shortcutSet.has(`${d.source}-${d.target}`) ? '#22c55e' : '#334155')
      .attr('stroke-width', (d) => Math.min(Math.max(d.call_rate / 50, 1), 4))
      .attr('stroke-dasharray', (d) => d.isShortcut || shortcutSet.has(`${d.source}-${d.target}`) ? '5,5' : 'none')
      .attr('stroke-opacity', 0.6)

    // Draw nodes
    const node = g.append('g')
      .selectAll('g')
      .data(Array.from(nodeMap.values()))
      .join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag<any, any>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
        }))
      .on('click', (event, d) => {
        event.stopPropagation()
        onNodeSelect?.(d.id === selectedNode ? null : d.id)
      })

    // Node circles
    node.append('circle')
      .attr('r', (d) => {
        const degree = d.metrics?.total_degree || 2
        return Math.min(Math.max(degree * 3, 12), 30)
      })
      .attr('fill', (d) => {
        if (d.metrics?.is_bottleneck) return 'url(#bottleneckGradient)'
        if (d.metrics?.is_hub) return 'url(#hubGradient)'
        return 'url(#nodeGradient)'
      })
      .attr('filter', 'url(#glow)')
      .attr('stroke', (d) => d.id === selectedNode ? '#fff' : 'none')
      .attr('stroke-width', 2)

    // Node labels
    node.append('text')
      .text((d) => d.name.length > 12 ? d.name.slice(0, 12) + '...' : d.name)
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => {
        const degree = d.metrics?.total_degree || 2
        return Math.min(Math.max(degree * 3, 12), 30) + 16
      })
      .attr('fill', '#94a3b8')
      .attr('font-size', '11px')
      .attr('font-family', 'Inter, sans-serif')

    // Update positions
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
    })

    // Click on background to deselect
    svg.on('click', () => onNodeSelect?.(null))

    // Cleanup
    return () => {
      simulation.stop()
    }
  }, [nodes, links, shortcuts, dimensions, selectedNode, onNodeSelect])

  const handleZoomIn = useCallback(() => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      1.5
    )
  }, [])

  const handleZoomOut = useCallback(() => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      0.67
    )
  }, [])

  const handleReset = useCallback(() => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().transform as any,
      d3.zoomIdentity
    )
  }, [])

  return (
    <div ref={containerRef} className={cn('relative w-full h-full min-h-[400px]', className)}>
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="bg-slate-900/50 rounded-xl"
      />

      {/* Controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleZoomIn}
          className="p-2 bg-slate-800/80 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition-colors"
        >
          <ZoomIn className="w-5 h-5" />
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleZoomOut}
          className="p-2 bg-slate-800/80 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition-colors"
        >
          <ZoomOut className="w-5 h-5" />
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleReset}
          className="p-2 bg-slate-800/80 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition-colors"
        >
          <RotateCcw className="w-5 h-5" />
        </motion.button>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 glass-card p-3 text-xs space-y-2">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gradient-to-br from-edge-400 to-edge-600" />
          <span className="text-slate-400">Normal Node</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gradient-to-br from-neural-400 to-neural-600" />
          <span className="text-slate-400">Hub</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gradient-to-br from-warning-400 to-warning-600" />
          <span className="text-slate-400">Bottleneck</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-0 border border-dashed border-success-500" />
          <span className="text-slate-400">Shortcut</span>
        </div>
      </div>
    </div>
  )
}

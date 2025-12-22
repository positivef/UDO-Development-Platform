"use client"

/**
 * DependencyGraph - Task dependency visualization with D3.js
 *
 * Week 7 Day 1: Dependency Graph Visualization
 *
 * Features:
 * - Force-directed graph showing task dependencies
 * - Nodes: Tasks with status-based colors
 * - Edges: Dependency relationships (dependencies, blocked_by)
 * - Interactive: Click node to focus, drag to rearrange
 * - Emergency override button (Q7: Hard Block + Emergency override)
 *
 * Q7 Implementation:
 * - Hard Block: Red edges for blocked relationships
 * - Emergency override: Admin can override dependency blocking
 */

import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import type { KanbanTask } from '@/lib/types/kanban'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Zap, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface DependencyGraphProps {
  tasks: KanbanTask[]
  currentTaskId?: string
  onTaskClick?: (taskId: string) => void
  onEmergencyOverride?: (taskId: string, dependencyId: string) => void
}

interface GraphNode extends d3.SimulationNodeDatum {
  id: string
  title: string
  status: string
  priority: string
  phase: string
}

interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode
  target: string | GraphNode
  type: 'dependency' | 'blocked'
}

export function DependencyGraph({
  tasks,
  currentTaskId,
  onTaskClick,
  onEmergencyOverride,
}: DependencyGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [showEmergencyOverride, setShowEmergencyOverride] = useState(false)
  const [renderTime, setRenderTime] = useState<number>(0)
  const [nodeCount, setNodeCount] = useState<number>(0)
  const [edgeCount, setEdgeCount] = useState<number>(0)
  const [zoomLevel, setZoomLevel] = useState<number>(1)

  useEffect(() => {
    if (!svgRef.current || tasks.length === 0) return

    const startTime = performance.now()

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove()

    const width = 800
    const height = 600
    const svg = d3
      .select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height])

    // Add zoom behavior
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        const g = svg.select('g.graph-container')
        g.attr('transform', event.transform)
        setZoomLevel(event.transform.k)
      })

    svg.call(zoom)

    // Add arrow markers FIRST (must be in svg, not container)
    svg
      .append('defs')
      .selectAll('marker')
      .data(['dependency', 'blocked'])
      .join('marker')
      .attr('id', (d) => `arrow-${d}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('fill', (d) => (d === 'blocked' ? '#ef4444' : '#3b82f6'))
      .attr('d', 'M0,-5L10,0L0,5')

    // Create container group for graph elements (for zoom transform)
    const graphContainer = svg.append('g').attr('class', 'graph-container')

    // Build graph data
    const nodes: GraphNode[] = tasks.map((task) => ({
      id: task.id,
      title: task.title,
      status: task.status,
      priority: task.priority,
      phase: task.phase,
    }))

    const links: GraphLink[] = []

    // Update node count
    setNodeCount(nodes.length)

    // Add dependency links (task → dependency)
    tasks.forEach((task) => {
      if (task.dependencies && task.dependencies.length > 0) {
        task.dependencies.forEach((depId) => {
          links.push({
            source: task.id,
            target: depId,
            type: 'dependency',
          })
        })
      }
      // Add blocked links (task ← blocker)
      if (task.blocked_by && task.blocked_by.length > 0) {
        task.blocked_by.forEach((blockerId) => {
          links.push({
            source: blockerId,
            target: task.id,
            type: 'blocked',
          })
        })
      }
    })

    // Update edge count
    setEdgeCount(links.length)

    // Create force simulation
    const simulation = d3
      .forceSimulation<GraphNode>(nodes)
      .force(
        'link',
        d3
          .forceLink<GraphNode, GraphLink>(links)
          .id((d) => d.id)
          .distance(150)
      )
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(60))

    // Draw links (edges)
    const link = graphContainer
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', (d) => (d.type === 'blocked' ? '#ef4444' : '#3b82f6'))
      .attr('stroke-width', (d) => (d.type === 'blocked' ? 3 : 2))
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', (d) => `url(#arrow-${d.type})`)

    // Draw nodes
    const node = graphContainer
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(drag(simulation) as any)

    // Node circles with status-based colors
    node
      .append('circle')
      .attr('r', 20)
      .attr('fill', (d) => getStatusColor(d.status))
      .attr('stroke', (d) =>
        d.id === currentTaskId
          ? '#8b5cf6'
          : d.id === selectedNode
          ? '#fbbf24'
          : '#e5e7eb'
      )
      .attr('stroke-width', (d) =>
        d.id === currentTaskId || d.id === selectedNode ? 4 : 2
      )

    // Node labels
    node
      .append('text')
      .text((d) => d.title.substring(0, 15) + (d.title.length > 15 ? '...' : ''))
      .attr('x', 0)
      .attr('y', 35)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#374151')

    // Priority badges (small circles)
    node
      .append('circle')
      .attr('r', 6)
      .attr('cx', 15)
      .attr('cy', -15)
      .attr('fill', (d) => getPriorityColor(d.priority))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)

    // Node click handler
    node.on('click', (event, d) => {
      event.stopPropagation()
      setSelectedNode(d.id)
      if (onTaskClick) {
        onTaskClick(d.id)
      }

      // Check if this node is blocked
      const isBlocked = links.some(
        (link) =>
          (link.target as GraphNode).id === d.id && link.type === 'blocked'
      )
      setShowEmergencyOverride(isBlocked)
    })

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as GraphNode).x ?? 0)
        .attr('y1', (d) => (d.source as GraphNode).y ?? 0)
        .attr('x2', (d) => (d.target as GraphNode).x ?? 0)
        .attr('y2', (d) => (d.target as GraphNode).y ?? 0)

      node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
    })

    // Drag behavior
    function drag(simulation: d3.Simulation<GraphNode, undefined>) {
      function dragstarted(event: any) {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        event.subject.fx = event.subject.x
        event.subject.fy = event.subject.y
      }

      function dragged(event: any) {
        event.subject.fx = event.x
        event.subject.fy = event.y
      }

      function dragended(event: any) {
        if (!event.active) simulation.alphaTarget(0)
        event.subject.fx = null
        event.subject.fy = null
      }

      return d3
        .drag<SVGGElement, GraphNode>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
    }

    // Update render time
    const endTime = performance.now()
    setRenderTime(Math.round(endTime - startTime))

    // Cleanup
    return () => {
      simulation.stop()
    }
  }, [tasks, currentTaskId, selectedNode, onTaskClick])

  // Status color mapping
  function getStatusColor(status: string): string {
    const colors: Record<string, string> = {
      pending: '#94a3b8',
      in_progress: '#fbbf24',
      blocked: '#ef4444',
      completed: '#10b981',
    }
    return colors[status] || '#94a3b8'
  }

  // Priority color mapping
  function getPriorityColor(priority: string): string {
    const colors: Record<string, string> = {
      low: '#10b981',
      medium: '#fbbf24',
      high: '#f97316',
      critical: '#ef4444',
    }
    return colors[priority] || '#94a3b8'
  }

  const handleEmergencyOverride = () => {
    if (selectedNode && onEmergencyOverride) {
      // Find blocker tasks
      const blockers = tasks
        .find((t) => t.id === selectedNode)
        ?.blocked_by?.filter(Boolean) || []

      if (blockers.length > 0) {
        // Override the first blocker (can be extended to show selection UI)
        onEmergencyOverride(selectedNode, blockers[0])
        setShowEmergencyOverride(false)
      }
    }
  }

  const handleZoomIn = () => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    const zoom = d3.zoom<SVGSVGElement, unknown>()
    svg.transition().call(zoom.scaleBy, 1.3)
  }

  const handleZoomOut = () => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    const zoom = d3.zoom<SVGSVGElement, unknown>()
    svg.transition().call(zoom.scaleBy, 0.7)
  }

  const handleResetZoom = () => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    const zoom = d3.zoom<SVGSVGElement, unknown>()
    svg.transition().call(zoom.transform, d3.zoomIdentity)
  }

  return (
    <div className="space-y-4">
      {/* Graph Canvas */}
      <div className="border rounded-lg bg-white dark:bg-gray-900 p-4 relative">
        <svg ref={svgRef} className="w-full h-auto" />

        {/* Zoom Controls */}
        <div className="absolute top-4 right-4 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleZoomIn}
            title="Zoom In"
            className="bg-white dark:bg-gray-800"
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleZoomOut}
            title="Zoom Out"
            className="bg-white dark:bg-gray-800"
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleResetZoom}
            title="Reset Zoom"
            className="bg-white dark:bg-gray-800"
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>

        {/* Graph Statistics */}
        <div className="absolute bottom-4 left-4 text-xs text-muted-foreground">
          {nodeCount} nodes, {edgeCount} edges · Rendered in {renderTime}ms
        </div>
      </div>

      {/* Legend */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold">Legend</h3>
        <div className="flex gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-slate-400" />
            <span>Pending</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-yellow-400" />
            <span>In Progress</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500" />
            <span>Blocked</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500" />
            <span>Completed</span>
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <div className="w-8 h-0.5 bg-blue-500" />
            <span>Dependency</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-red-500" />
            <span>Hard Block</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-blue-500 opacity-50" />
            <span>Soft Dependency</span>
          </div>
        </div>
      </div>

      {/* Emergency Override (Q7) */}
      {showEmergencyOverride && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>
              Task is blocked by dependencies. Emergency override available (Admin
              only)
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleEmergencyOverride}
              className="bg-yellow-500 hover:bg-yellow-600 text-white border-yellow-600"
            >
              <Zap className="h-3 w-3 mr-1" />
              Emergency Override
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Instructions */}
      <div className="text-xs text-muted-foreground">
        <p>
          <strong>Tip:</strong> Drag nodes to rearrange. Click a node to select it.
          Purple border = current task, Yellow border = selected task.
        </p>
      </div>
    </div>
  )
}

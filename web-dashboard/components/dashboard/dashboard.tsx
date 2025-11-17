"use client"

import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  Activity,
  Brain,
  Cpu,
  GitBranch,
  Layers,
  TrendingUp,
  Zap,
  AlertCircle,
  CheckCircle2,
  Clock,
  Loader2
} from "lucide-react"
import { SystemStatus } from "./system-status"
import { PhaseProgress } from "./phase-progress"
import { UncertaintyMap } from "./uncertainty-map"
import { AICollaboration } from "./ai-collaboration"
import { ExecutionHistory } from "./execution-history"
import { MetricsChart } from "./metrics-chart"
import { ControlPanel } from "./control-panel"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function Dashboard() {
  const [selectedPhase, setSelectedPhase] = useState<string>("ideation")
  const [isConnected, setIsConnected] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)

  // Fetch system status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ["system-status"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/status`)
      return res.json()
    },
  })

  // Fetch metrics
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ["metrics"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/metrics`)
      return res.json()
    },
  })

  // WebSocket connection
  useEffect(() => {
    const wsUrl = API_URL.replace("http", "ws")
    const socket = new WebSocket(`${wsUrl}/ws`)

    socket.onopen = () => {
      setIsConnected(true)
      toast.success("Connected to UDO System")
    }

    socket.onclose = () => {
      setIsConnected(false)
      toast.error("Disconnected from UDO System")
    }

    socket.onerror = (error) => {
      console.error("WebSocket error:", error)
      toast.error("Connection error")
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    }

    setWs(socket)

    return () => {
      socket.close()
    }
  }, [])

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case "task_executed":
        toast.success("Task executed successfully")
        break
      case "phase_changed":
        setSelectedPhase(data.data.new_phase)
        toast.info(`Phase changed to ${data.data.new_phase}`)
        break
      case "error":
        toast.error(data.message)
        break
    }
  }

  const executeTask = async (task: string, phase: string) => {
    try {
      const res = await fetch(`${API_URL}/api/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, phase }),
      })
      const data = await res.json()
      if (data.success) {
        toast.success("Task executed successfully")
      }
    } catch (error) {
      toast.error("Failed to execute task")
    }
  }

  if (statusLoading || metricsLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <Brain className="h-8 w-8 text-blue-500" />
              UDO Development Platform v3.0
            </h1>
            <p className="text-gray-400 mt-2">
              Intelligent Development Automation & Predictive Analytics
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg",
              isConnected ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
            )}>
              {isConnected ? (
                <>
                  <CheckCircle2 className="h-5 w-5" />
                  <span>Connected</span>
                </>
              ) : (
                <>
                  <AlertCircle className="h-5 w-5" />
                  <span>Disconnected</span>
                </>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          <SystemStatus status={status?.report?.status || {}} />
          <PhaseProgress
            currentPhase={metrics?.current_phase || "ideation"}
            onPhaseChange={setSelectedPhase}
          />
        </div>

        {/* Middle Column */}
        <div className="space-y-6">
          <UncertaintyMap
            state={metrics?.uncertainty_state || "unknown"}
            confidence={metrics?.confidence_level || 0}
          />
          <MetricsChart metrics={metrics} />
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          <AICollaboration services={metrics?.ai_services || {}} />
          <ControlPanel onExecute={executeTask} currentPhase={selectedPhase} />
        </div>
      </div>

      {/* Bottom Section */}
      <ExecutionHistory
        executions={metrics?.recent_tasks || []}
        performanceMetrics={metrics?.performance_metrics || {}}
      />
    </div>
  )
}
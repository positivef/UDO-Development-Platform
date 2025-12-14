"use client"

import { useState, useEffect, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import Link from "next/link"
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
  Loader2,
  BarChart3,
  Lightbulb,
  Palette,
  HelpCircle
} from "lucide-react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { SystemStatus } from "./system-status"
import { PhaseProgress } from "./phase-progress"
import { UncertaintyMap } from "./uncertainty-map"
import { BayesianConfidence } from "./bayesian-confidence"
import { AICollaboration } from "./ai-collaboration"
import { ExecutionHistory } from "./execution-history"
import { MetricsChart } from "./metrics-chart"
import { ControlPanel } from "./control-panel"
import { TaskList } from "@/components/TaskList"
import { ProjectSelector } from "./project-selector"
import { QuickGuideModal } from "./quick-guide-modal"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function Dashboard() {
  const [selectedPhase, setSelectedPhase] = useState<string>("ideation")
  const [isConnected, setIsConnected] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [showQuickGuide, setShowQuickGuide] = useState(false)
  const queryClient = useQueryClient()

  // Fetch system status
  const { data: status, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ["system-status"],
    queryFn: async () => {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000) // 30초 타임아웃

      try {
        const res = await fetch(`${API_URL}/api/status`, {
          signal: controller.signal
        })
        clearTimeout(timeoutId)
        if (!res.ok) throw new Error('Status API failed')
        return await res.json()
      } catch (error) {
        clearTimeout(timeoutId)
        throw error // 에러를 던져서 재시도하도록
      }
    },
    retry: 2,
    staleTime: 10000,
    refetchOnWindowFocus: false,
  })

  // Fetch metrics
  const { data: metrics, isLoading: metricsLoading, error: metricsError } = useQuery({
    queryKey: ["metrics"],
    queryFn: async () => {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000) // 30초 타임아웃

      try {
        const res = await fetch(`${API_URL}/api/metrics`, {
          signal: controller.signal
        })
        clearTimeout(timeoutId)
        if (!res.ok) throw new Error('Metrics API failed')
        return await res.json()
      } catch (error) {
        clearTimeout(timeoutId)
        throw error // 에러를 던져서 재시도하도록
      }
    },
    retry: 2,
    staleTime: 10000,
    refetchOnWindowFocus: false,
  })

  // Fetch uncertainty status (uses dedicated endpoint)
  const { data: uncertainty, isLoading: uncertaintyLoading } = useQuery({
    queryKey: ["uncertainty-status"],
    queryFn: async () => {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 20000)

      try {
        const res = await fetch(`${API_URL}/api/uncertainty/status`, {
          signal: controller.signal
        })
        clearTimeout(timeoutId)
        if (!res.ok) throw new Error('Uncertainty API failed')
        return await res.json()
      } catch (error) {
        clearTimeout(timeoutId)
        throw error
      }
    },
    retry: 2,
    staleTime: 5000,
    refetchOnWindowFocus: false,
  })

  // Fetch Bayesian confidence analysis
  const { data: bayesianData, isLoading: bayesianLoading } = useQuery({
    queryKey: ["bayesian-confidence", selectedPhase],
    queryFn: async () => {
      const payload = {
        phase: selectedPhase,
        context: {
          phase: selectedPhase,
          has_code: true,
          validation_score: 0.7,
          team_size: 3,
          timeline_weeks: 8
        },
        historical_outcomes: [true, true, false, true, true],
        use_fast_mode: true
      }

      const res = await fetch(`${API_URL}/api/uncertainty/confidence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })

      if (!res.ok) throw new Error("Bayesian API failed")
      return await res.json()
    },
    retry: 2,
    staleTime: 10000,
    refetchOnWindowFocus: false,
    enabled: Boolean(selectedPhase)
  })

  const ackMutation = useMutation({
    mutationFn: async (params: { id: string; dimension?: string }) => {
      const res = await fetch(`${API_URL}/api/uncertainty/ack/${params.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mitigation_id: params.id,
          dimension: params.dimension
        })
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || "ACK failed")
      }
      return res.json()
    },
    onSuccess: () => {
      toast.success("Mitigation applied")
      queryClient.invalidateQueries({ queryKey: ["uncertainty-status"] })
      queryClient.invalidateQueries({ queryKey: ["metrics"] })
    },
    onError: (err: Error) => {
      toast.error(err?.message || "Failed to apply mitigation")
    }
  })

  // WebSocket connection
  useEffect(() => {
    // Build WS URL that respects http/https -> ws/wss
    const api = new URL(API_URL)
    api.protocol = api.protocol === "https:" ? "wss:" : "ws:"
    const socket = new WebSocket(`${api.origin}/ws`)

    socket.onopen = () => {
      setIsConnected(true)
      toast.success("Connected to UDO System")
    }

    socket.onclose = () => {
      setIsConnected(false)
      toast.error("Disconnected from UDO System")
    }

    socket.onerror = (error) => {
      console.error("WebSocket error:", {
        url: socket.url,
        readyState: socket.readyState,
        error,
      })
      toast.error("Connection error")
    }

    socket.onmessage = (event) => {
      let data
      try {
        data = JSON.parse(event.data)
      } catch (_err) {
        console.error("WebSocket message parse error", event.data)
        return
      }
      handleWebSocketMessage(data)
    }

    setWs(socket)

    return () => {
      socket.close()
    }
  }, [])

  const handleWebSocketMessage = (data: { type: string; data?: { new_phase?: string }; message?: string }) => {
    switch (data.type) {
      case "task_executed":
        toast.success("Task executed successfully")
        break
      case "phase_changed":
        if (data.data?.new_phase) {
          setSelectedPhase(data.data.new_phase)
          toast.info(`Phase changed to ${data.data.new_phase}`)
        }
        break
      case "error":
        toast.error(data.message || "An error occurred")
        break
      case "uncertainty_update":
        queryClient.invalidateQueries({ queryKey: ["uncertainty-status"] })
        queryClient.invalidateQueries({ queryKey: ["metrics"] })
        toast.info("Uncertainty updated")
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

  // Memoize merged values to prevent initialization errors
  const mergedUncertaintyState = useMemo(
    () => uncertainty?.state || metrics?.uncertainty_state || "unknown",
    [uncertainty?.state, metrics?.uncertainty_state]
  )

  const mergedConfidence = useMemo(
    () => uncertainty?.confidence_score ?? metrics?.confidence_level ?? 0,
    [uncertainty?.confidence_score, metrics?.confidence_level]
  )

  const mergedPrediction = useMemo(
    () => uncertainty?.prediction ?? null,
    [uncertainty?.prediction]
  )

  const mergedMitigations = useMemo(
    () => uncertainty?.mitigations ?? [],
    [uncertainty?.mitigations]
  )

  const dominantDimension = useMemo(
    () => uncertainty?.vector?.dominant_dimension || metrics?.uncertainty_dominant,
    [uncertainty?.vector?.dominant_dimension, metrics?.uncertainty_dominant]
  )

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
            <button
              onClick={() => setShowQuickGuide(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 hover:from-blue-500/30 hover:to-purple-500/30 transition-colors border border-blue-500/30"
            >
              <HelpCircle className="h-5 w-5" />
              <span className="font-medium">Quick Guide</span>
            </button>
            <ProjectSelector />
            <Link href="/gi-formula">
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors">
                <Lightbulb className="h-5 w-5" />
                <span>GI Formula</span>
              </button>
            </Link>
            <Link href="/ck-theory">
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 transition-colors">
                <Palette className="h-5 w-5" />
                <span>C-K Theory</span>
              </button>
            </Link>
            <Link href="/quality">
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors">
                <BarChart3 className="h-5 w-5" />
                <span>Quality</span>
              </button>
            </Link>
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
            state={mergedUncertaintyState}
            confidence={mergedConfidence}
            prediction={mergedPrediction}
            mitigations={mergedMitigations}
            isLoading={uncertaintyLoading}
            isAcking={ackMutation.isPending}
            onAcknowledge={async (mitigation) => {
              await ackMutation.mutateAsync({
                id: mitigation.id,
                dimension: dominantDimension
              })
            }}
            vector={uncertainty?.vector}
          />
          {bayesianData && (
            <BayesianConfidence
              decision={bayesianData.decision}
              confidence_score={bayesianData.confidence_score}
              state={bayesianData.state}
              risk_level={bayesianData.metadata?.risk_level || "medium"}
              monitoring_level={bayesianData.metadata?.monitoring_level || "standard"}
              dominant_dimension={bayesianData.metadata?.dominant_dimension}
              recommendations={
                bayesianData.recommendations?.map((rec: string, idx: number) => ({
                  action: rec,
                  priority: idx === 0 ? "high" : idx === 1 ? "medium" : "low",
                  reason: "Based on Bayesian inference and historical data"
                })) || []
              }
              bayesian_details={{
                prior: bayesianData.metadata?.prior_mean || 0.5,
                posterior: bayesianData.metadata?.posterior_mean || bayesianData.confidence_score,
                likelihood: bayesianData.metadata?.likelihood || 1.0,
                credible_interval_lower: bayesianData.metadata?.credible_interval_lower || 0.5,
                credible_interval_upper: bayesianData.metadata?.credible_interval_upper || 0.9,
                confidence_width: bayesianData.metadata?.uncertainty_magnitude || 0.2
              }}
              isLoading={bayesianLoading}
            />
          )}
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

      {/* Task Management Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="mt-6"
      >
        <TaskList />
      </motion.div>

      {/* Quick Guide Modal */}
      <QuickGuideModal
        isOpen={showQuickGuide}
        onClose={() => setShowQuickGuide(false)}
      />
    </div>
  )
}

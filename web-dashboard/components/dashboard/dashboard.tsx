"use client"

import { useState, useEffect, useMemo, lazy, Suspense } from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
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
  AlertTriangle,
  CheckCircle2,
  Clock,
  Loader2,
  BarChart3,
  Lightbulb,
  Palette,
  HelpCircle,
  Home,
  KanbanSquare,
  Archive,
  Gauge
} from "lucide-react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { SystemStatus } from "./system-status"
import { PhaseProgress } from "./phase-progress"
import { AICollaboration } from "./ai-collaboration"
import { ControlPanel } from "./control-panel"
import { ProjectTierStatus } from "./project-tier-status"

// Lazy load heavy chart components
const UncertaintyMap = lazy(() => import("./uncertainty-map").then(m => ({ default: m.UncertaintyMap })))
const BayesianConfidence = lazy(() => import("./bayesian-confidence").then(m => ({ default: m.BayesianConfidence })))
const MetricsChart = lazy(() => import("./metrics-chart").then(m => ({ default: m.MetricsChart })))
const ExecutionHistory = lazy(() => import("./execution-history").then(m => ({ default: m.ExecutionHistory })))
import { TaskList } from "@/components/TaskList"
import { ProjectSelector } from "./project-selector"
import { QuickGuideModal } from "./quick-guide-modal"
import { ErrorBoundary } from "@/components/ErrorBoundary"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// Skeleton loader component
function ChartSkeleton() {
  return (
    <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700 animate-pulse">
      <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
      <div className="space-y-3">
        <div className="h-32 bg-gray-700 rounded"></div>
        <div className="h-24 bg-gray-700 rounded"></div>
      </div>
    </div>
  )
}

export function Dashboard() {
  const t = useTranslations()
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
              {t('dashboard.title')}
            </h1>
            <p className="text-gray-400 mt-2">
              {t('dashboard.description')}
            </p>
          </div>
          <div className="flex flex-col gap-4">
            {/* Top Row: Quick Guide + Project Selector + Status */}
            <div className="flex items-center justify-end gap-4">
              <button
                onClick={() => setShowQuickGuide(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 hover:from-blue-500/30 hover:to-purple-500/30 transition-colors border border-blue-500/30"
              >
                <HelpCircle className="h-5 w-5" />
                <span className="font-medium">Quick Guide</span>
              </button>
              <ProjectSelector />
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

            {/* Navigation Menu Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 mt-4">
              <Link href="/">
                <button className="flex items-center gap-2 px-4 py-3 rounded-lg bg-gray-700/30 text-gray-300 hover:bg-gray-700/50 transition-colors w-full justify-center">
                  <Home className="h-5 w-5" />
                  <span>{t('navigation.dashboard')}</span>
                </button>
              </Link>
              <Link href="/kanban">
                <button className="flex items-center gap-2 px-4 py-3 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors w-full justify-center">
                  <KanbanSquare className="h-5 w-5" />
                  <span>{t('navigation.kanban')}</span>
                </button>
              </Link>
              <Link href="/archive">
                <button className="flex items-center gap-2 px-4 py-3 rounded-lg bg-gray-700/30 text-gray-300 hover:bg-gray-700/50 transition-colors w-full justify-center">
                  <Archive className="h-5 w-5" />
                  <span>{t('navigation.archive')}</span>
                </button>
              </Link>
              <Link href="/roi-dashboard">
                <button className="flex items-center gap-2 px-4 py-3 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors w-full justify-center">
                  <TrendingUp className="h-5 w-5" />
                  <span>{t('navigation.roi')}</span>
                </button>
              </Link>
              <Link href="/uncertainty">
                <button className="flex items-center gap-2 px-4 py-3 rounded-lg bg-orange-500/20 text-orange-400 hover:bg-orange-500/30 transition-colors w-full justify-center">
                  <AlertTriangle className="h-5 w-5" />
                  <span>{t('navigation.uncertainty')}</span>
                </button>
              </Link>
              <Link href="/confidence">
                <button className="flex items-center gap-2 px-4 py-3 rounded-lg bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 transition-colors w-full justify-center">
                  <Gauge className="h-5 w-5" />
                  <span>{t('navigation.confidence')}</span>
                </button>
              </Link>
              <Link href="/quality">
                <button className="flex items-center gap-2 px-4 py-3 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors w-full justify-center">
                  <BarChart3 className="h-5 w-5" />
                  <span>{t('navigation.quality')}</span>
                </button>
              </Link>
              <Link href="/time-tracking">
                <button className="flex items-center gap-2 px-4 py-3 rounded-lg bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 transition-colors w-full justify-center">
                  <Clock className="h-5 w-5" />
                  <span>{t('navigation.timeTracking')}</span>
                </button>
              </Link>
              <Link href="/gi-formula">
                <button className="flex items-center gap-2 px-4 py-3 rounded-lg bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 transition-colors w-full justify-center">
                  <Lightbulb className="h-5 w-5" />
                  <span>{t('navigation.giFormula')}</span>
                </button>
              </Link>
              <Link href="/ck-theory">
                <button className="flex items-center gap-2 px-4 py-3 rounded-lg bg-pink-500/20 text-pink-400 hover:bg-pink-500/30 transition-colors w-full justify-center">
                  <Palette className="h-5 w-5" />
                  <span>{t('navigation.ckTheory')}</span>
                </button>
              </Link>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          <ProjectTierStatus />
          <SystemStatus status={status?.report?.status || {}} />
          <PhaseProgress
            currentPhase={metrics?.current_phase || "ideation"}
            onPhaseChange={setSelectedPhase}
          />
        </div>

        {/* Middle Column */}
        <div className="space-y-6">
          <ErrorBoundary>
            <Suspense fallback={<ChartSkeleton />}>
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
            </Suspense>
          </ErrorBoundary>
          {bayesianData && (
            <ErrorBoundary>
              <Suspense fallback={<ChartSkeleton />}>
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
            </Suspense>
            </ErrorBoundary>
          )}
          <ErrorBoundary>
            <Suspense fallback={<ChartSkeleton />}>
            <MetricsChart metrics={metrics} />
            </Suspense>
          </ErrorBoundary>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          <AICollaboration services={metrics?.ai_services || {}} />
          <ControlPanel onExecute={executeTask} currentPhase={selectedPhase} />
        </div>
      </div>

      {/* Bottom Section */}
      <ErrorBoundary>
        <Suspense fallback={<ChartSkeleton />}>
          <ExecutionHistory
            executions={metrics?.recent_tasks || []}
            performanceMetrics={metrics?.performance_metrics || {}}
          />
        </Suspense>
      </ErrorBoundary>

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

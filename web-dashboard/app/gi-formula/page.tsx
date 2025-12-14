"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useMutation, useQuery } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  Lightbulb,
  Brain,
  Sparkles,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ArrowRight,
  Clock,
  Target
} from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface GIInsightSummary {
  id: string
  problem: string
  final_insight: string
  confidence_score: number
  created_at: string
}

interface ApiStageResult {
  stage: string
  content: string
  duration_ms?: number
}

interface ApiBiasCheck {
  biases_detected?: string[]
  mitigation_strategies?: string[]
  confidence_score?: number
}

interface ApiGIFormulaResult {
  id: string
  problem: string
  stages: Record<string, ApiStageResult>
  final_insight: string
  bias_check: ApiBiasCheck
  total_duration_ms?: number
  created_at: string
}

interface StageResult {
  stage_type: string
  output: string
  processing_time_s: number
}

interface BiasCheck {
  potential_biases: string[]
  confidence_score: number
  recommendations: string[]
}

interface GIFormulaResult {
  insight_id: string
  problem: string
  stages: StageResult[]
  final_insight: string
  bias_check: BiasCheck
  execution_time_s: number
  created_at: string
}

export default function GIFormulaPage() {
  const router = useRouter()
  const [problem, setProblem] = useState("")
  const [context, setContext] = useState<Record<string, string>>({})
  const [result, setResult] = useState<GIFormulaResult | null>(null)

  // Fetch recent insights
  const { data: recentInsights = [], refetch: refetchInsights } = useQuery<GIInsightSummary[]>({
    queryKey: ["gi-insights"],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/api/v1/gi-formula?limit=5`)
      if (!response.ok) throw new Error("Failed to fetch insights")
      return response.json() as Promise<GIInsightSummary[]>
    },
    refetchOnWindowFocus: false,
  })

  const handleBack = () => {
    const hasHistory = typeof window !== "undefined" && window.history.length > 1
    if (hasHistory) {
      router.back()
    } else {
      router.push("/")
    }
  }

  const normalizeResult = (data: ApiGIFormulaResult): GIFormulaResult => ({
    insight_id: data.id,
    problem: data.problem,
    final_insight: data.final_insight,
    created_at: data.created_at,
    execution_time_s: data.total_duration_ms ? data.total_duration_ms / 1000 : 0,
    bias_check: {
      potential_biases: data.bias_check.biases_detected || [],
      recommendations: data.bias_check.mitigation_strategies || [],
      confidence_score: data.bias_check.confidence_score || 0,
    },
    stages: Object.values(data.stages || {}).map((stage) => ({
      stage_type: stage.stage,
      output: stage.content,
      processing_time_s: (stage.duration_ms || 0) / 1000,
    })),
  })

  // Generate insight mutation
  const generateMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_URL}/api/v1/gi-formula`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem, context }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to generate insight")
      }
      return response.json()
    },
    onSuccess: (data: ApiGIFormulaResult) => {
      setResult(normalizeResult(data))
      toast.success("Insight generated successfully!")
      refetchInsights()
    },
    onError: (error: Error) => {
      toast.error(`Failed to generate insight: ${error.message}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!problem.trim()) {
      toast.error("Please enter a problem statement")
      return
    }
    generateMutation.mutate()
  }

  const getStageIcon = (stageType: string) => {
    switch (stageType) {
      case "observation": return <Target className="h-5 w-5" />
      case "connection": return <ArrowRight className="h-5 w-5" />
      case "pattern": return <TrendingUp className="h-5 w-5" />
      case "synthesis": return <Sparkles className="h-5 w-5" />
      case "bias_check": return <CheckCircle2 className="h-5 w-5" />
      default: return <Brain className="h-5 w-5" />
    }
  }

  const getStageColor = (stageType: string) => {
    switch (stageType) {
      case "observation": return "text-blue-400 bg-blue-500/10"
      case "connection": return "text-purple-400 bg-purple-500/10"
      case "pattern": return "text-green-400 bg-green-500/10"
      case "synthesis": return "text-yellow-400 bg-yellow-500/10"
      case "bias_check": return "text-red-400 bg-red-500/10"
      default: return "text-gray-400 bg-gray-500/10"
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="mb-4">
        <button
          type="button"
          onClick={handleBack}
          className={cn(
            "inline-flex items-center gap-2 px-3 py-2 rounded-lg",
            "text-sm font-medium text-white",
            "bg-gray-800/70 border border-gray-700/70",
            "hover:border-blue-500/60 hover:text-blue-200 transition-colors"
          )}
        >
          <ArrowRight className="h-4 w-4 rotate-180" />
          Back
        </button>
      </div>

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20">
            <Lightbulb className="h-8 w-8 text-blue-400" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-white">GI Formula</h1>
            <p className="text-gray-400 mt-1">
              5-Stage Genius Insight Generation System
            </p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Input Form */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-1"
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="p-6 rounded-xl bg-gray-800/50 border border-gray-700/50">
              <h2 className="text-xl font-semibold text-white mb-4">
                Problem Statement
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">
                    What problem do you want to solve?
                  </label>
                  <textarea
                    value={problem}
                    onChange={(e) => setProblem(e.target.value)}
                    placeholder="E.g., How can we reduce API latency by 50%?"
                    className={cn(
                      "w-full px-4 py-3 rounded-lg",
                      "bg-gray-900/50 border border-gray-700",
                      "text-white placeholder-gray-500",
                      "focus:outline-none focus:border-blue-500",
                      "transition-colors resize-none"
                    )}
                    rows={4}
                    disabled={generateMutation.isPending}
                    suppressHydrationWarning
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">
                    Context (Optional)
                  </label>
                  <textarea
                    value={JSON.stringify(context, null, 2)}
                    onChange={(e) => {
                      try {
                        setContext(JSON.parse(e.target.value))
                      } catch {
                        // Invalid JSON, ignore
                      }
                    }}
                    placeholder='{"current_latency": "200ms", "target_latency": "100ms"}'
                    className={cn(
                      "w-full px-4 py-3 rounded-lg",
                      "bg-gray-900/50 border border-gray-700",
                      "text-white placeholder-gray-500",
                      "focus:outline-none focus:border-blue-500",
                      "transition-colors resize-none font-mono text-sm"
                    )}
                    rows={3}
                    disabled={generateMutation.isPending}
                    suppressHydrationWarning
                  />
                </div>

                <button
                  type="submit"
                  disabled={generateMutation.isPending || !problem.trim()}
                  className={cn(
                    "w-full px-6 py-3 rounded-lg font-semibold",
                    "bg-gradient-to-r from-blue-500 to-purple-500",
                    "text-white transition-all",
                    "hover:from-blue-600 hover:to-purple-600",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    "flex items-center justify-center gap-2"
                  )}
                >
                  {generateMutation.isPending ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Generating Insight...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-5 w-5" />
                      Generate Insight
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Recent Insights */}
            {recentInsights.length > 0 && (
              <div className="p-6 rounded-xl bg-gray-800/50 border border-gray-700/50">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Recent Insights
                </h3>
                <div className="space-y-3">
                  {recentInsights.map((insight) => (
                    <button
                      key={insight.id}
                      onClick={() => {
                        setProblem(insight.problem)
                        // Optionally fetch full insight details
                      }}
                      className={cn(
                        "w-full p-3 rounded-lg",
                        "bg-gray-900/50 border border-gray-700",
                        "hover:border-blue-500/50 transition-colors",
                        "text-left"
                      )}
                    >
                      <p className="text-sm text-white line-clamp-2 mb-1">
                        {insight.problem}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <Clock className="h-3 w-3" />
                        {new Date(insight.created_at).toLocaleDateString()}
                        <span className="ml-auto text-blue-400">
                          {(insight.confidence_score * 100).toFixed(0)}% confidence
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </form>
        </motion.div>

        {/* Right Column - Results */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="space-y-6"
              >
                {/* Final Insight */}
                <div className="p-6 rounded-xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20">
                  <div className="flex items-center gap-3 mb-4">
                    <Sparkles className="h-6 w-6 text-blue-400" />
                    <h2 className="text-2xl font-bold text-white">Final Insight</h2>
                  </div>
                  <p className="text-lg text-gray-200 leading-relaxed">
                    {result.final_insight}
                  </p>
                  <div className="flex items-center gap-4 mt-4 text-sm text-gray-400">
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {result.execution_time_s.toFixed(2)}s
                    </div>
                    <div className="flex items-center gap-1">
                      <CheckCircle2 className="h-4 w-4 text-green-400" />
                      {(result.bias_check.confidence_score * 100).toFixed(0)}% confidence
                    </div>
                  </div>
                </div>

                {/* Stages */}
                <div className="space-y-4">
                  <h3 className="text-xl font-semibold text-white">
                    Processing Stages
                  </h3>
                  {result.stages.map((stage, index) => (
                    <motion.div
                      key={stage.stage_type}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 rounded-lg bg-gray-800/50 border border-gray-700/50"
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className={cn("p-2 rounded-lg", getStageColor(stage.stage_type))}>
                          {getStageIcon(stage.stage_type)}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-white capitalize">
                            {stage.stage_type.replace("_", " ")}
                          </h4>
                          <p className="text-xs text-gray-500">
                            {stage.processing_time_s.toFixed(2)}s
                          </p>
                        </div>
                      </div>
                      <p className="text-gray-300 text-sm leading-relaxed">
                        {stage.output}
                      </p>
                    </motion.div>
                  ))}
                </div>

                {/* Bias Check */}
                {result.bias_check.potential_biases.length > 0 && (
                  <div className="p-6 rounded-xl bg-red-500/10 border border-red-500/20">
                    <div className="flex items-center gap-3 mb-4">
                      <AlertCircle className="h-6 w-6 text-red-400" />
                      <h3 className="text-xl font-semibold text-white">Bias Check</h3>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <h4 className="text-sm font-medium text-red-400 mb-2">
                          Potential Biases:
                        </h4>
                        <ul className="list-disc list-inside space-y-1">
                          {result.bias_check.potential_biases.map((bias, i) => (
                            <li key={i} className="text-gray-300 text-sm">
                              {bias}
                            </li>
                          ))}
                        </ul>
                      </div>
                      {result.bias_check.recommendations.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-blue-400 mb-2">
                            Recommendations:
                          </h4>
                          <ul className="list-disc list-inside space-y-1">
                            {result.bias_check.recommendations.map((rec, i) => (
                              <li key={i} className="text-gray-300 text-sm">
                                {rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div
                key="placeholder"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center h-full min-h-[600px] text-center"
              >
                <div className="p-6 rounded-full bg-gray-800/50 mb-6">
                  <Brain className="h-16 w-16 text-gray-600" />
                </div>
                <h3 className="text-2xl font-semibold text-gray-400 mb-2">
                  No Insight Generated Yet
                </h3>
                <p className="text-gray-500 max-w-md">
                  Enter a problem statement and click &ldquo;Generate Insight&rdquo; to see the 5-stage
                  GI Formula analysis in action.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  )
}

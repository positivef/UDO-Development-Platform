"use client"

import { motion } from "framer-motion"
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Code2,
  FileCode,
  TestTube,
  TrendingUp,
  TrendingDown,
  Activity,
  RefreshCw
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useState, useEffect } from "react"

interface PylintMetrics {
  score: number
  total_issues: number
  issues_by_type: {
    convention: number
    refactor: number
    warning: number
    error: number
    fatal: number
  }
  analyzed_at: string
  error?: string
}

interface ESLintMetrics {
  score: number
  total_files: number
  total_errors: number
  total_warnings: number
  total_issues: number
  analyzed_at: string
  error?: string
}

interface TestCoverageMetrics {
  coverage_percentage: number
  tests_total: number
  tests_passed: number
  tests_failed: number
  success_rate: number
  analyzed_at: string
  error?: string
}

interface QualityMetricsData {
  overall_score: number
  code_quality: {
    python: PylintMetrics
    typescript: ESLintMetrics
  }
  test_metrics: TestCoverageMetrics
  collected_at: string
}

interface QualityMetricsProps {
  initialData?: QualityMetricsData | null
  apiUrl?: string
}

export function QualityMetrics({
  initialData = null,
  apiUrl = "http://localhost:8000/api/quality-metrics"
}: QualityMetricsProps) {
  const [metrics, setMetrics] = useState<QualityMetricsData | null>(initialData)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchMetrics = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(apiUrl)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      const data = await response.json()
      setMetrics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch metrics")
      console.error("Error fetching quality metrics:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!initialData) {
      fetchMetrics()
    }

    // 30초마다 자동 새로고침 (선택적)
    // const interval = setInterval(() => {
    //   fetchMetrics()
    // }, 30000)

    // return () => clearInterval(interval)
  }, [])

  const getScoreColor = (score: number): string => {
    if (score >= 9.0) return "text-green-400 bg-green-500/10"
    if (score >= 7.0) return "text-blue-400 bg-blue-500/10"
    if (score >= 5.0) return "text-yellow-400 bg-yellow-500/10"
    return "text-red-400 bg-red-500/10"
  }

  const getScoreIcon = (score: number) => {
    if (score >= 9.0) return <CheckCircle2 className="h-5 w-5" />
    if (score >= 7.0) return <Activity className="h-5 w-5" />
    if (score >= 5.0) return <AlertCircle className="h-5 w-5" />
    return <XCircle className="h-5 w-5" />
  }

  const getCoverageColor = (coverage: number): string => {
    if (coverage >= 80) return "text-green-400"
    if (coverage >= 60) return "text-yellow-400"
    return "text-red-400"
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-500/10">
            <Code2 className="h-6 w-6 text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Quality Metrics</h2>
            <p className="text-sm text-gray-400">Code quality, linting, and test coverage</p>
          </div>
        </div>
        <button
          onClick={fetchMetrics}
          disabled={loading}
          className={cn(
            "px-4 py-2 rounded-lg font-medium transition-all",
            "bg-blue-500/10 text-blue-400 hover:bg-blue-500/20",
            "flex items-center gap-2",
            loading && "opacity-50 cursor-not-allowed"
          )}
        >
          <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          {loading ? "Analyzing..." : "Refresh"}
        </button>
      </div>

      {/* Error State */}
      {error && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="p-4 rounded-lg bg-red-500/10 border border-red-500/20"
        >
          <div className="flex items-center gap-3">
            <XCircle className="h-5 w-5 text-red-400" />
            <div>
              <p className="font-medium text-red-400">Failed to load metrics</p>
              <p className="text-sm text-red-400/80 mt-1">{error}</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Metrics Content */}
      {metrics && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Overall Score */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2 p-6 rounded-lg bg-gray-800/50 border border-gray-700/50"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400 mb-1">Overall Quality Score</p>
                <div className="flex items-center gap-3">
                  <span className="text-5xl font-bold text-white">
                    {metrics.overall_score.toFixed(1)}
                  </span>
                  <span className="text-2xl text-gray-400">/  10</span>
                </div>
              </div>
              <div className={cn("p-4 rounded-xl", getScoreColor(metrics.overall_score))}>
                {getScoreIcon(metrics.overall_score)}
              </div>
            </div>
            <div className="mt-4 h-2 bg-gray-700 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${metrics.overall_score * 10}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className={cn(
                  "h-full rounded-full",
                  metrics.overall_score >= 9.0 ? "bg-green-400" :
                  metrics.overall_score >= 7.0 ? "bg-blue-400" :
                  metrics.overall_score >= 5.0 ? "bg-yellow-400" : "bg-red-400"
                )}
              />
            </div>
          </motion.div>

          {/* Python (Pylint) Metrics */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="p-6 rounded-lg bg-gray-800/50 border border-gray-700/50"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-blue-500/10">
                <FileCode className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Python Code Quality</h3>
                <p className="text-xs text-gray-400">Pylint Analysis</p>
              </div>
            </div>

            {metrics.code_quality.python.error ? (
              <div className="text-sm text-red-400">
                {metrics.code_quality.python.error}
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-3xl font-bold text-white">
                    {metrics.code_quality.python.score.toFixed(1)}
                  </span>
                  <span className="text-sm text-gray-400">/  10</span>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Total Issues</span>
                    <span className="font-medium text-white">
                      {metrics.code_quality.python.total_issues}
                    </span>
                  </div>

                  {metrics.code_quality.python.issues_by_type && (
                    <div className="mt-3 space-y-1 text-xs">
                      {Object.entries(metrics.code_quality.python.issues_by_type).map(([type, count]) => (
                        count > 0 && (
                          <div key={type} className="flex items-center justify-between">
                            <span className="text-gray-500 capitalize">{type}</span>
                            <span className={cn(
                              "font-medium",
                              type === "error" || type === "fatal" ? "text-red-400" :
                              type === "warning" ? "text-yellow-400" : "text-gray-400"
                            )}>
                              {count}
                            </span>
                          </div>
                        )
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </motion.div>

          {/* TypeScript (ESLint) Metrics */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="p-6 rounded-lg bg-gray-800/50 border border-gray-700/50"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-purple-500/10">
                <Code2 className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">TypeScript Code Quality</h3>
                <p className="text-xs text-gray-400">ESLint Analysis</p>
              </div>
            </div>

            {metrics.code_quality.typescript.error ? (
              <div className="text-sm text-red-400">
                {metrics.code_quality.typescript.error}
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-3xl font-bold text-white">
                    {metrics.code_quality.typescript.score.toFixed(1)}
                  </span>
                  <span className="text-sm text-gray-400">/  10</span>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Files Analyzed</span>
                    <span className="font-medium text-white">
                      {metrics.code_quality.typescript.total_files}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Errors</span>
                    <span className="font-medium text-red-400">
                      {metrics.code_quality.typescript.total_errors}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Warnings</span>
                    <span className="font-medium text-yellow-400">
                      {metrics.code_quality.typescript.total_warnings}
                    </span>
                  </div>
                </div>
              </>
            )}
          </motion.div>

          {/* Test Coverage */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="lg:col-span-2 p-6 rounded-lg bg-gray-800/50 border border-gray-700/50"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-green-500/10">
                <TestTube className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Test Coverage</h3>
                <p className="text-xs text-gray-400">pytest with coverage</p>
              </div>
            </div>

            {metrics.test_metrics.error ? (
              <div className="text-sm text-red-400">
                {metrics.test_metrics.error}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {/* Coverage Percentage */}
                <div>
                  <p className="text-sm text-gray-400 mb-2">Coverage</p>
                  <div className="flex items-center gap-2">
                    <span className={cn("text-3xl font-bold", getCoverageColor(metrics.test_metrics.coverage_percentage))}>
                      {metrics.test_metrics.coverage_percentage.toFixed(1)}%
                    </span>
                    {metrics.test_metrics.coverage_percentage >= 80 ? (
                      <TrendingUp className="h-5 w-5 text-green-400" />
                    ) : (
                      <TrendingDown className="h-5 w-5 text-red-400" />
                    )}
                  </div>
                  <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${metrics.test_metrics.coverage_percentage}%` }}
                      transition={{ duration: 0.8, ease: "easeOut" }}
                      className={cn(
                        "h-full rounded-full",
                        getCoverageColor(metrics.test_metrics.coverage_percentage)
                      )}
                    />
                  </div>
                </div>

                {/* Tests Total */}
                <div>
                  <p className="text-sm text-gray-400 mb-2">Total Tests</p>
                  <span className="text-3xl font-bold text-white">
                    {metrics.test_metrics.tests_total}
                  </span>
                </div>

                {/* Tests Passed */}
                <div>
                  <p className="text-sm text-gray-400 mb-2">Passed</p>
                  <span className="text-3xl font-bold text-green-400">
                    {metrics.test_metrics.tests_passed}
                  </span>
                </div>

                {/* Tests Failed */}
                <div>
                  <p className="text-sm text-gray-400 mb-2">Failed</p>
                  <span className="text-3xl font-bold text-red-400">
                    {metrics.test_metrics.tests_failed}
                  </span>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      )}

      {/* Loading State */}
      {loading && !metrics && (
        <div className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-4">
            <RefreshCw className="h-8 w-8 text-blue-400 animate-spin" />
            <p className="text-gray-400">Analyzing code quality...</p>
          </div>
        </div>
      )}
    </motion.div>
  )
}

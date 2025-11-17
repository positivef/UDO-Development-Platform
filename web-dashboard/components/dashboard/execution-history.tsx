"use client"

import { motion } from "framer-motion"
import { Clock, CheckCircle2, XCircle, AlertCircle, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { format } from "date-fns"

interface ExecutionHistoryProps {
  executions: Array<{
    task?: string
    phase?: string
    timestamp?: string
    decision?: string
    confidence?: number
    uncertainty_state?: string
  }>
  performanceMetrics: {
    execution_count?: number
    avg_confidence?: number
  }
}

export function ExecutionHistory({ executions, performanceMetrics }: ExecutionHistoryProps) {
  const getDecisionIcon = (decision?: string) => {
    switch (decision) {
      case "GO":
        return <CheckCircle2 className="h-4 w-4 text-green-400" />
      case "GO_WITH_CHECKPOINTS":
        return <AlertCircle className="h-4 w-4 text-yellow-400" />
      case "NO_GO":
        return <XCircle className="h-4 w-4 text-red-400" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getDecisionColor = (decision?: string) => {
    switch (decision) {
      case "GO":
        return "text-green-400 bg-green-500/10"
      case "GO_WITH_CHECKPOINTS":
        return "text-yellow-400 bg-yellow-500/10"
      case "NO_GO":
        return "text-red-400 bg-red-500/10"
      default:
        return "text-gray-400 bg-gray-500/10"
    }
  }

  const getPhaseColor = (phase?: string) => {
    const colors = {
      ideation: "text-purple-400",
      design: "text-blue-400",
      mvp: "text-green-400",
      implementation: "text-yellow-400",
      testing: "text-orange-400"
    }
    return colors[phase as keyof typeof colors] || "text-gray-400"
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Clock className="h-5 w-5 text-gray-400" />
          <h2 className="text-xl font-semibold text-white">Execution History</h2>
        </div>
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-400">Total:</span>
            <span className="font-medium text-white">
              {performanceMetrics.execution_count || 0}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400">Avg Confidence:</span>
            <span className="font-medium text-blue-400">
              {Math.round((performanceMetrics.avg_confidence || 0) * 100)}%
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {executions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No executions yet. Start by executing a task from the control panel.
          </div>
        ) : (
          executions.map((execution, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-gray-700/30 rounded-lg p-4 hover:bg-gray-700/40 transition-all"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                  {getDecisionIcon(execution.decision)}
                  <div>
                    <div className="text-sm font-medium text-white">
                      {execution.task || "Unknown Task"}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={cn("text-xs", getPhaseColor(execution.phase))}>
                        {execution.phase || "unknown"}
                      </span>
                      <ArrowRight className="h-3 w-3 text-gray-600" />
                      <span className={cn(
                        "text-xs px-2 py-0.5 rounded-full",
                        getDecisionColor(execution.decision)
                      )}>
                        {execution.decision || "PENDING"}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-500">
                    {execution.timestamp
                      ? format(new Date(execution.timestamp), "HH:mm:ss")
                      : "N/A"}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-3">
                <div className="bg-gray-800/50 rounded px-2 py-1">
                  <span className="text-xs text-gray-500">Confidence:</span>
                  <span className="ml-2 text-xs font-medium text-blue-400">
                    {execution.confidence ? `${Math.round(execution.confidence * 100)}%` : "N/A"}
                  </span>
                </div>
                <div className="bg-gray-800/50 rounded px-2 py-1">
                  <span className="text-xs text-gray-500">Uncertainty:</span>
                  <span className="ml-2 text-xs font-medium text-purple-400">
                    {execution.uncertainty_state || "Unknown"}
                  </span>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>

      {/* Summary Stats */}
      {executions.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">
                {executions.filter(e => e.decision === "GO").length}
              </div>
              <div className="text-xs text-gray-500">GO Decisions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">
                {executions.filter(e => e.decision === "GO_WITH_CHECKPOINTS").length}
              </div>
              <div className="text-xs text-gray-500">Checkpoints</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">
                {executions.filter(e => e.decision === "NO_GO").length}
              </div>
              <div className="text-xs text-gray-500">NO_GO</div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  )
}
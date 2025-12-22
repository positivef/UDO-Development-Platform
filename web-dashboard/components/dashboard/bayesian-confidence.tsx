"use client"

import { memo } from "react"
import { motion } from "framer-motion"
import { TrendingUp, AlertTriangle, CheckCircle2, Activity, Target, Zap } from "lucide-react"
import { cn } from "@/lib/utils"

interface BayesianDetails {
  prior: number
  posterior: number
  likelihood: number
  credible_interval_lower: number
  credible_interval_upper: number
  confidence_width: number
}

interface Recommendation {
  action: string
  priority: "critical" | "high" | "medium" | "low"
  reason: string
  estimated_impact?: number
}

interface BayesianConfidenceProps {
  decision: "GO" | "GO_WITH_CHECKPOINTS" | "NO_GO"
  confidence_score: number
  state: string
  risk_level: "low" | "medium" | "high" | "critical"
  monitoring_level: "standard" | "enhanced" | "intensive"
  dominant_dimension?: string
  recommendations: Recommendation[]
  bayesian_details: BayesianDetails
  isLoading?: boolean
}

const decisionConfig = {
  GO: {
    color: "text-green-400",
    bgColor: "bg-green-500/20",
    borderColor: "border-green-500/50",
    icon: CheckCircle2,
    label: "GO",
    description: "Ready to proceed"
  },
  GO_WITH_CHECKPOINTS: {
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/20",
    borderColor: "border-yellow-500/50",
    icon: AlertTriangle,
    label: "GO WITH CHECKPOINTS",
    description: "Proceed with caution"
  },
  NO_GO: {
    color: "text-red-400",
    bgColor: "bg-red-500/20",
    borderColor: "border-red-500/50",
    icon: AlertTriangle,
    label: "NO GO",
    description: "Not ready to proceed"
  }
}

const riskConfig = {
  low: { color: "text-green-400", label: "Low" },
  medium: { color: "text-yellow-400", label: "Medium" },
  high: { color: "text-orange-400", label: "High" },
  critical: { color: "text-red-400", label: "Critical" }
}

const priorityConfig = {
  critical: { color: "text-red-400", badge: "bg-red-500/20 border-red-500/50" },
  high: { color: "text-orange-400", badge: "bg-orange-500/20 border-orange-500/50" },
  medium: { color: "text-yellow-400", badge: "bg-yellow-500/20 border-yellow-500/50" },
  low: { color: "text-blue-400", badge: "bg-blue-500/20 border-blue-500/50" }
}

export const BayesianConfidence = memo(function BayesianConfidence({
  decision,
  confidence_score,
  state,
  risk_level,
  monitoring_level,
  dominant_dimension,
  recommendations,
  bayesian_details,
  isLoading
}: BayesianConfidenceProps) {
  const config = decisionConfig[decision]
  const DecisionIcon = config.icon
  const riskStyle = riskConfig[risk_level]

  if (isLoading) {
    return (
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-700 rounded w-1/2"></div>
          <div className="h-20 bg-gray-700 rounded"></div>
          <div className="h-40 bg-gray-700 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-800/50 rounded-lg border border-gray-700 p-6 space-y-6"
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-400" />
            Bayesian Confidence Analysis
          </h3>
          <p className="text-sm text-gray-400">
            Statistical decision support based on Bayesian inference
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-blue-400">
            {(confidence_score * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-400">Confidence</div>
        </div>
      </div>

      {/* Decision Badge */}
      <div className={cn(
        "p-4 rounded-lg border-2 flex items-start gap-4",
        config.bgColor,
        config.borderColor
      )}>
        <DecisionIcon className={cn("h-8 w-8 flex-shrink-0", config.color)} />
        <div className="flex-1">
          <div className={cn("text-xl font-bold mb-1", config.color)}>
            {config.label}
          </div>
          <div className="text-sm text-gray-300 mb-3">
            {config.description}
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Risk Level:</span>
              <span className={riskStyle.color}>{riskStyle.label}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-400">State:</span>
              <span className="text-gray-200">{state}</span>
            </div>
            {dominant_dimension && (
              <div className="flex items-center gap-2">
                <span className="text-gray-400">Key Factor:</span>
                <span className="text-blue-400">{dominant_dimension}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-purple-400" />
          <span className="text-sm font-medium text-gray-300">
            Recommended Actions ({recommendations.length})
          </span>
        </div>
        <div className="space-y-2">
          {recommendations.map((rec, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className={cn(
                "p-3 rounded-lg border text-sm",
                priorityConfig[rec.priority].badge
              )}
            >
              <div className="flex items-start gap-3">
                <Zap className={cn(
                  "h-4 w-4 flex-shrink-0 mt-0.5",
                  priorityConfig[rec.priority].color
                )} />
                <div className="flex-1">
                  <div className="font-medium text-gray-200 mb-1">
                    {rec.action}
                  </div>
                  <div className="text-xs text-gray-400">
                    {rec.reason}
                  </div>
                  {rec.estimated_impact && (
                    <div className="mt-2 text-xs text-gray-300">
                      Estimated Impact: <span className="text-green-400">
                        +{(rec.estimated_impact * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
                <span className={cn(
                  "px-2 py-0.5 rounded text-xs font-medium uppercase",
                  priorityConfig[rec.priority].badge
                )}>
                  {rec.priority}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Bayesian Details */}
      <div className="space-y-3 pt-4 border-t border-gray-700">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-blue-400" />
          <span className="text-sm font-medium text-gray-300">
            Bayesian Statistics
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-900/50 rounded p-3">
            <div className="text-xs text-gray-400 mb-1">Prior Belief</div>
            <div className="text-lg font-semibold text-gray-200">
              {(bayesian_details.prior * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-gray-900/50 rounded p-3">
            <div className="text-xs text-gray-400 mb-1">Posterior (Updated)</div>
            <div className="text-lg font-semibold text-blue-400">
              {(bayesian_details.posterior * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-gray-900/50 rounded p-3">
            <div className="text-xs text-gray-400 mb-1">Likelihood</div>
            <div className="text-lg font-semibold text-gray-200">
              {(bayesian_details.likelihood * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-gray-900/50 rounded p-3">
            <div className="text-xs text-gray-400 mb-1">Confidence Width</div>
            <div className="text-lg font-semibold text-gray-200">
              ±{(bayesian_details.confidence_width * 100).toFixed(1)}%
            </div>
          </div>
        </div>
        <div className="bg-gray-900/50 rounded p-3">
          <div className="text-xs text-gray-400 mb-2">95% Credible Interval</div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-300">
              {(bayesian_details.credible_interval_lower * 100).toFixed(1)}%
            </span>
            <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{
                  width: `${(bayesian_details.credible_interval_upper -
                           bayesian_details.credible_interval_lower) * 100}%`,
                  marginLeft: `${bayesian_details.credible_interval_lower * 100}%`
                }}
                className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
              />
            </div>
            <span className="text-sm text-gray-300">
              {(bayesian_details.credible_interval_upper * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Monitoring Level */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-700">
        <div className="text-sm text-gray-400">
          Monitoring Level:
        </div>
        <div className={cn(
          "px-3 py-1 rounded-full text-sm font-medium",
          monitoring_level === "intensive" && "bg-red-500/20 text-red-400 border border-red-500/50",
          monitoring_level === "enhanced" && "bg-yellow-500/20 text-yellow-400 border border-yellow-500/50",
          monitoring_level === "standard" && "bg-green-500/20 text-green-400 border border-green-500/50"
        )}>
          {monitoring_level.toUpperCase()}
        </div>
      </div>
    </motion.div>
  )
})

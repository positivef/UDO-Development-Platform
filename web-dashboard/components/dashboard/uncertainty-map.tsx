"use client"

import { motion } from "framer-motion"
import { AlertTriangle, TrendingUp, Zap } from "lucide-react"
import { cn } from "@/lib/utils"

interface UncertaintyMapProps {
  state: string
  confidence: number
}

export function UncertaintyMap({ state, confidence }: UncertaintyMapProps) {
  const stateConfig = {
    Deterministic: { color: "green", icon: "✅", description: "Highly predictable" },
    Probabilistic: { color: "blue", icon: "📊", description: "Statistically predictable" },
    Quantum: { color: "purple", icon: "⚛️", description: "Superposition state" },
    Chaotic: { color: "orange", icon: "🌪️", description: "Sensitive to conditions" },
    Void: { color: "red", icon: "⚫", description: "Unknown territory" },
    unknown: { color: "gray", icon: "❓", description: "Not analyzed" }
  }

  const config = stateConfig[state as keyof typeof stateConfig] || stateConfig.unknown
  const colorClass = {
    green: "text-green-400 bg-green-500/10 border-green-500/30",
    blue: "text-blue-400 bg-blue-500/10 border-blue-500/30",
    purple: "text-purple-400 bg-purple-500/10 border-purple-500/30",
    orange: "text-orange-400 bg-orange-500/10 border-orange-500/30",
    red: "text-red-400 bg-red-500/10 border-red-500/30",
    gray: "text-gray-400 bg-gray-500/10 border-gray-500/30"
  }[config.color] || "text-gray-400 bg-gray-500/10 border-gray-500/30"

  // Calculate risk level based on state and confidence
  const riskLevel = state === "Void" ? 90 : state === "Chaotic" ? 70 :
                    state === "Quantum" ? 50 : state === "Probabilistic" ? 30 : 10
  const adjustedRisk = Math.max(0, Math.min(100, riskLevel * (1 - confidence)))

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
    >
      <div className="flex items-center gap-3 mb-4">
        <AlertTriangle className="h-5 w-5 text-yellow-400" />
        <h2 className="text-xl font-semibold text-white">Uncertainty Analysis</h2>
      </div>

      {/* Quantum State Display */}
      <div className={cn(
        "rounded-lg p-4 border-2 mb-4",
        colorClass
      )}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-2xl">{config.icon}</span>
          <span className={cn("text-lg font-bold", colorClass.split(' ')[0])}>
            {state}
          </span>
        </div>
        <p className="text-gray-400 text-sm">{config.description}</p>
      </div>

      {/* Confidence Meter */}
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Confidence Level</span>
          <span className="text-blue-400 font-medium">
            {Math.round(confidence * 100)}%
          </span>
        </div>
        <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${confidence * 100}%` }}
            transition={{ duration: 0.5 }}
            className={cn(
              "h-full",
              confidence > 0.7 ? "bg-gradient-to-r from-green-500 to-green-400" :
              confidence > 0.4 ? "bg-gradient-to-r from-yellow-500 to-yellow-400" :
              "bg-gradient-to-r from-red-500 to-red-400"
            )}
          />
        </div>
      </div>

      {/* Risk Assessment */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Risk Level</span>
          <span className={cn(
            "font-medium",
            adjustedRisk < 30 ? "text-green-400" :
            adjustedRisk < 60 ? "text-yellow-400" :
            "text-red-400"
          )}>
            {adjustedRisk < 30 ? "Low" : adjustedRisk < 60 ? "Medium" : "High"}
          </span>
        </div>
        <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${adjustedRisk}%` }}
            transition={{ duration: 0.5 }}
            className={cn(
              "h-full",
              adjustedRisk < 30 ? "bg-gradient-to-r from-green-500 to-green-400" :
              adjustedRisk < 60 ? "bg-gradient-to-r from-yellow-500 to-yellow-400" :
              "bg-gradient-to-r from-red-500 to-red-400"
            )}
          />
        </div>
      </div>

      {/* Predictive Insights */}
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="h-4 w-4 text-blue-400" />
          <span className="text-sm font-medium text-gray-300">24h Prediction</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-700/50 rounded p-2">
            <span className="text-gray-400">Stability:</span>
            <span className="ml-2 text-blue-400">
              {state === "Deterministic" ? "High" : state === "Void" ? "Low" : "Medium"}
            </span>
          </div>
          <div className="bg-gray-700/50 rounded p-2">
            <span className="text-gray-400">Action:</span>
            <span className="ml-2 text-green-400">
              {adjustedRisk > 60 ? "Mitigate" : "Monitor"}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
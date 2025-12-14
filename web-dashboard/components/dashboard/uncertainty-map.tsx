"use client"

import { motion } from "framer-motion"
import { AlertTriangle, TrendingUp, Zap, Clock, CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"

import {
  UncertaintyState,
  UncertaintyVector,
  PredictiveModel,
  MitigationStrategy
} from "@/types/uncertainty"

interface RootCause {
  dimension: string
  score: number
  reason: string
}

interface MissedStep {
  step: string
  impact: string
  shouldHaveBeenDone: string
}

interface PreventionCheck {
  item: string
  status: "done" | "in_progress" | "not_done"
  priority: string
}

interface UncertaintyMapProps {
  state?: UncertaintyState
  confidence?: number
  prediction?: PredictiveModel | null
  mitigations?: MitigationStrategy[]
  isLoading?: boolean
  onAcknowledge?: (mitigation: MitigationStrategy) => Promise<void> | void
  isAcking?: boolean
  vector?: UncertaintyVector
}

function normalizeState(raw?: string): string {
  const value = (raw || "").toLowerCase()
  switch (value) {
    case "deterministic":
      return "Deterministic"
    case "probabilistic":
      return "Probabilistic"
    case "quantum":
      return "Quantum"
    case "chaotic":
      return "Chaotic"
    case "void":
      return "Void"
    default:
      return "unknown"
  }
}

function formatDate(value?: string | null) {
  if (!value) return "예측 없음"
  const dt = new Date(value)
  if (Number.isNaN(dt.getTime())) return "예측 없음"
  return dt.toLocaleString()
}

function getRootCauseReason(dimension?: string, vector?: any): string {
  const reasons: Record<string, string> = {
    quality: "테스트 커버리지 부족 (0%)",
    technical: "기술적 복잡도 높음",
    market: "요구사항 불명확",
    resource: "팀 리소스 부족",
    timeline: "일정 압박"
  }
  return reasons[dimension || "quality"] || "원인 분석 중"
}

function getMissedSteps(dimension?: string): MissedStep[] {
  const steps: Record<string, MissedStep[]> = {
    quality: [
      {
        step: "테스트 자동화 구축",
        impact: "High",
        shouldHaveBeenDone: "MVP 단계"
      },
      {
        step: "코드 리뷰 프로세스",
        impact: "Medium",
        shouldHaveBeenDone: "Design 단계"
      }
    ],
    technical: [
      {
        step: "기술 스택 검증",
        impact: "High",
        shouldHaveBeenDone: "Design 단계"
      }
    ]
  }
  return steps[dimension || "quality"] || []
}

export function UncertaintyMap({
  state,
  confidence,
  prediction,
  mitigations = [],
  isLoading = false,
  onAcknowledge,
  isAcking = false,
  vector
}: UncertaintyMapProps) {
  const normalizedState = normalizeState(state)
  const safeConfidence = Math.max(0, Math.min(1, confidence ?? 0))

  // Root Cause Analysis
  const rootCause: RootCause | null = vector ? {
    dimension: vector.dominant_dimension || "quality",
    score: Math.max(
      vector.technical || 0,
      vector.market || 0,
      vector.resource || 0,
      vector.timeline || 0,
      vector.quality || 0
    ),
    reason: getRootCauseReason(vector.dominant_dimension, vector)
  } : null

  // Prevention Checklist (hardcoded for now, will be dynamic later)
  const preventionChecks: PreventionCheck[] = [
    { item: "TDD 적용 (테스트 먼저 작성)", status: "not_done", priority: "P0" },
    { item: "CI/CD 파이프라인 구축", status: "not_done", priority: "P0" },
    { item: "코드 리뷰 프로세스", status: "not_done", priority: "P1" }
  ]
  const stateConfig = {
    Deterministic: { color: "green", icon: "✅", description: "Highly predictable" },
    Probabilistic: { color: "blue", icon: "📊", description: "Statistically predictable" },
    Quantum: { color: "purple", icon: "⚛️", description: "Superposition state" },
    Chaotic: { color: "orange", icon: "🌪️", description: "Sensitive to conditions" },
    Void: { color: "red", icon: "⚫", description: "Unknown territory" },
    unknown: { color: "gray", icon: "❓", description: "Not analyzed" }
  }

  const config = stateConfig[normalizedState as keyof typeof stateConfig] || stateConfig.unknown
  const colorClass = {
    green: "text-green-400 bg-green-500/10 border-green-500/30",
    blue: "text-blue-400 bg-blue-500/10 border-blue-500/30",
    purple: "text-purple-400 bg-purple-500/10 border-purple-500/30",
    orange: "text-orange-400 bg-orange-500/10 border-orange-500/30",
    red: "text-red-400 bg-red-500/10 border-red-500/30",
    gray: "text-gray-400 bg-gray-500/10 border-gray-500/30"
  }[config.color] || "text-gray-400 bg-gray-500/10 border-gray-500/30"

  // Calculate risk level based on state and confidence
  const riskLevel = normalizedState === "Void" ? 90 : normalizedState === "Chaotic" ? 70 :
    normalizedState === "Quantum" ? 50 : normalizedState === "Probabilistic" ? 30 : 10
  const adjustedRisk = Math.max(0, Math.min(100, riskLevel * (1 - safeConfidence)))

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
    >
      <div className="flex items-center justify-between gap-3 mb-4">
        <AlertTriangle className="h-5 w-5 text-yellow-400" />
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold text-white">Uncertainty Analysis</h2>
          {isLoading && (
            <span className="text-xs text-gray-400">갱신 중...</span>
          )}
        </div>
      </div>

      {/* Quantum State Display */}
      <div className={cn(
        "rounded-lg p-4 border-2 mb-4",
        colorClass
      )}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-2xl">{config.icon}</span>
          <span className={cn("text-lg font-bold", colorClass.split(' ')[0])}>
            {normalizedState}
          </span>
        </div>
        <p className="text-gray-400 text-sm">{config.description}</p>
      </div>

      {/* Confidence Meter */}
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Confidence Level</span>
          <span className="text-blue-400 font-medium">
            {Math.round(safeConfidence * 100)}%
          </span>
        </div>
        <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${safeConfidence * 100}%` }}
            transition={{ duration: 0.5 }}
            className={cn(
              "h-full",
              safeConfidence > 0.7 ? "bg-gradient-to-r from-green-500 to-green-400" :
                safeConfidence > 0.4 ? "bg-gradient-to-r from-yellow-500 to-yellow-400" :
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
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="h-4 w-4 text-blue-400" />
          <span className="text-sm font-medium text-gray-300">24h Prediction</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-700/50 rounded p-2">
            <span className="text-gray-400">Stability:</span>
            <span className="ml-2 text-blue-400">
              {normalizedState === "Deterministic" ? "High" : normalizedState === "Void" ? "Low" : "Medium"}
            </span>
          </div>
          <div className="bg-gray-700/50 rounded p-2">
            <span className="text-gray-400">Action:</span>
            <span className="ml-2 text-green-400">
              {adjustedRisk > 60 ? "Mitigate" : "Monitor"}
            </span>
          </div>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-700/50 rounded p-2 flex items-center gap-2">
            <Clock className="h-3 w-3 text-gray-400" />
            <div>
              <span className="text-gray-400 block">Predicted Resolution</span>
              <span className="text-gray-200">{formatDate(prediction?.predicted_resolution)}</span>
            </div>
          </div>
          <div className="bg-gray-700/50 rounded p-2">
            <span className="text-gray-400 block">Trend</span>
            <span className="text-gray-200">
              {prediction?.trend ?? "unknown"}
            </span>
          </div>
        </div>
      </div>

      {/* Root Cause Analysis */}
      {rootCause && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            <span className="text-sm font-medium text-gray-300">🔍 Root Cause Analysis</span>
          </div>
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 space-y-2">
            <div>
              <span className="text-xs text-gray-400">Primary Cause: </span>
              <span className="text-red-300 font-medium capitalize">{rootCause.dimension} ({Math.round(rootCause.score * 100)}%)</span>
            </div>
            <div className="text-xs text-gray-300">
              → {rootCause.reason}
            </div>

            {/* Missed Steps */}
            <div className="mt-2 pt-2 border-t border-red-500/20">
              <div className="text-xs text-gray-400 mb-1">✗ What You Missed:</div>
              {getMissedSteps(rootCause.dimension).map((step, idx) => (
                <div key={idx} className="ml-2 mb-1">
                  <div className="text-xs text-red-200">• {step.step}</div>
                  <div className="text-[10px] text-gray-500 ml-3">
                    Impact: {step.impact} | Should: {step.shouldHaveBeenDone}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Prevention Checklist */}
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle2 className="h-4 w-4 text-green-400" />
          <span className="text-sm font-medium text-gray-300">📋 Prevention Checklist</span>
        </div>
        <div className="space-y-2">
          {preventionChecks.map((check, idx) => (
            <div
              key={idx}
              className={cn(
                "p-2 rounded border",
                check.status === "done" ? "bg-green-500/10 border-green-500/30" :
                  check.status === "in_progress" ? "bg-yellow-500/10 border-yellow-500/30" :
                    "bg-gray-700/30 border-gray-600/30"
              )}
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">
                  {check.status === "done" ? "✅" : check.status === "in_progress" ? "🔄" : "□"}
                </span>
                <span className="text-xs text-gray-300 flex-1">{check.item}</span>
                <span className={cn(
                  "text-[10px] px-1 py-0.5 rounded",
                  check.priority === "P0" ? "bg-red-500/20 text-red-300" : "bg-yellow-500/20 text-yellow-300"
                )}>
                  {check.priority}
                </span>
              </div>
            </div>
          ))}
          {preventionChecks.filter(c => c.status === "not_done" && c.priority === "P0").length > 0 && (
            <div className="mt-2 text-xs text-orange-300 bg-orange-500/10 border border-orange-500/30 rounded p-2">
              ⚠️ {preventionChecks.filter(c => c.status === "not_done" && c.priority === "P0").length} P0 checks 미완료 - 다음 단계 진입 불가
            </div>
          )}
        </div>
      </div>

      {/* Mitigation Suggestions */}
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="h-4 w-4 text-yellow-400" />
          <span className="text-sm font-medium text-gray-300">⚡ Mitigation Strategies</span>
        </div>
        {mitigations.length === 0 ? (
          <p className="text-xs text-gray-400">추천 전략이 아직 없습니다.</p>
        ) : (
          <div className="space-y-2">
            {mitigations.slice(0, 3).map((item) => (
              <div
                key={item.id}
                className="bg-gray-700/50 rounded p-3 border border-gray-700"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-200">{item.action}</span>
                  <span className="text-xs text-gray-400">P{item.priority}</span>
                </div>
                <div className="mt-1 grid grid-cols-3 gap-2 text-[11px] text-gray-400">
                  <span>ROI: {item.roi !== undefined ? item.roi.toFixed(3) : "n/a"}</span>
                  <span>Impact: {item.estimated_impact !== undefined ? `${Math.round(item.estimated_impact * 100)}%` : "n/a"}</span>
                  <span>Success: {item.success_probability !== undefined ? `${Math.round(item.success_probability * 100)}%` : "n/a"}</span>
                </div>
                {onAcknowledge && (
                  <button
                    className="mt-2 w-full rounded bg-blue-500/20 text-blue-200 text-sm py-1 hover:bg-blue-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
                    onClick={() => onAcknowledge(item)}
                    disabled={isAcking}
                  >
                    {isAcking ? "Applying..." : "Mark as Completed"}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}

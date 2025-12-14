"use client"

import { motion, AnimatePresence } from "framer-motion"
import { X, CheckCircle2, AlertCircle, TrendingUp, Zap, Play } from "lucide-react"
import { cn } from "@/lib/utils"

interface QuickGuideModalProps {
  isOpen: boolean
  onClose: () => void
}

export function QuickGuideModal({ isOpen, onClose }: QuickGuideModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-gray-800 rounded-xl border border-gray-700 shadow-2xl z-50"
          >
            {/* Header */}
            <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Play className="h-6 w-6 text-blue-400" />
                  5분 Quick Start Guide
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  대시보드를 순서대로 확인하고 의사결정하는 방법
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-gray-400" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Flow Diagram */}
              <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-center gap-2 text-sm flex-wrap">
                  <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full border border-blue-500/30">
                    START
                  </span>
                  <span className="text-gray-600">→</span>
                  <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full border border-green-500/30">
                    ① System
                  </span>
                  <span className="text-gray-600">→</span>
                  <span className="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-full border border-purple-500/30">
                    ② Phase
                  </span>
                  <span className="text-gray-600">→</span>
                  <span className="px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-full border border-yellow-500/30">
                    ③ Uncertainty
                  </span>
                  <span className="text-gray-600">→</span>
                  <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full border border-blue-500/30">
                    ④ Bayesian
                  </span>
                  <span className="text-gray-600">→</span>
                  <span className="px-3 py-1 bg-orange-500/20 text-orange-400 rounded-full border border-orange-500/30">
                    ⑤ Action
                  </span>
                </div>
              </div>

              {/* Step 1 */}
              <StepCard
                number="①"
                title="System Status"
                subtitle="시스템이 정상인가?"
                duration="10초"
                color="green"
                icon={<CheckCircle2 className="h-5 w-5" />}
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-300">모두 녹색 → 다음 단계로</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <span className="text-gray-300">노란색 1개 → 로그 확인, 진행 가능</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span className="text-gray-300">빨간색 → 즉시 복구 필요</span>
                  </div>
                </div>
              </StepCard>

              {/* Step 2 */}
              <StepCard
                number="②"
                title="Phase Progress"
                subtitle="지금 어느 단계인가?"
                duration="10초"
                color="purple"
                icon={<TrendingUp className="h-5 w-5" />}
              >
                <div className="space-y-2 text-sm text-gray-300">
                  <div>💡 Ideation → 🎨 Design → ⚡ MVP → 🔧 Implementation → ✅ Testing</div>
                  <div className="text-gray-400">
                    현재 Phase 확인 및 전환 가능성 검토
                  </div>
                </div>
              </StepCard>

              {/* Step 3 */}
              <StepCard
                number="③"
                title="Uncertainty Analysis"
                subtitle="위험 상태는 어떤가?"
                duration="30초"
                color="yellow"
                icon={<AlertCircle className="h-5 w-5" />}
              >
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-gray-900/50 rounded p-2">
                      <div className="text-gray-400">State</div>
                      <div className="text-green-400">🟢 DETERMINISTIC {"<"}10%</div>
                    </div>
                    <div className="bg-gray-900/50 rounded p-2">
                      <div className="text-gray-400">Risk Level</div>
                      <div className="text-yellow-400">⚠️ Medium</div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-300">
                    <div className="font-medium mb-1">확인 순서:</div>
                    <div className="space-y-1 text-xs">
                      <div>1. State (불확실성 상태)</div>
                      <div>2. Risk Level (위험도)</div>
                      <div>3. Root Cause (근본 원인)</div>
                      <div>4. Prevention Checklist (P0 필수 완료)</div>
                      <div>5. Mitigation Strategies (ROI 순)</div>
                    </div>
                  </div>
                </div>
              </StepCard>

              {/* Step 4 */}
              <StepCard
                number="④"
                title="Bayesian Confidence"
                subtitle="진행해도 되는가?"
                duration="30초"
                color="blue"
                icon={<Zap className="h-5 w-5" />}
              >
                <div className="space-y-3">
                  <div className="flex items-center gap-4">
                    <div className="flex-1 bg-green-500/10 border border-green-500/30 rounded p-2">
                      <div className="text-xs text-gray-400">GO</div>
                      <div className="text-sm text-green-400">즉시 진행</div>
                    </div>
                    <div className="flex-1 bg-yellow-500/10 border border-yellow-500/30 rounded p-2">
                      <div className="text-xs text-gray-400">WITH CP</div>
                      <div className="text-sm text-yellow-400">조건부</div>
                    </div>
                    <div className="flex-1 bg-red-500/10 border border-red-500/30 rounded p-2">
                      <div className="text-xs text-gray-400">NO GO</div>
                      <div className="text-sm text-red-400">중단</div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-300">
                    <div className="font-medium mb-1">Phase별 필요 신뢰도:</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>Ideation: ≥ 60%</div>
                      <div>Design: ≥ 65%</div>
                      <div>MVP: ≥ 65%</div>
                      <div>Implementation: ≥ 70%</div>
                    </div>
                  </div>
                </div>
              </StepCard>

              {/* Step 5 */}
              <StepCard
                number="⑤"
                title="Action"
                subtitle="무엇을 할 것인가?"
                duration="즉시"
                color="orange"
                icon={<Play className="h-5 w-5" />}
              >
                <div className="space-y-2 text-sm">
                  <div className="bg-red-500/10 border border-red-500/30 rounded p-2">
                    <div className="font-medium text-red-400 mb-1">Priority 1 (즉시)</div>
                    <div className="text-xs text-gray-300">
                      P0 Checklist + Mitigation ROI {">"}2.0 + Critical Actions
                    </div>
                  </div>
                  <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-2">
                    <div className="font-medium text-yellow-400 mb-1">Priority 2 (당일)</div>
                    <div className="text-xs text-gray-300">
                      Missed Steps (High Impact) + High Priority Actions
                    </div>
                  </div>
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded p-2">
                    <div className="font-medium text-blue-400 mb-1">Priority 3 (주간)</div>
                    <div className="text-xs text-gray-300">
                      P1 Checklist + 정기 모니터링
                    </div>
                  </div>
                </div>
              </StepCard>

              {/* Quick Decision Matrix */}
              <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-lg p-4">
                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <Zap className="h-4 w-4 text-yellow-400" />
                  빠른 의사결정 (2초)
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-green-400">✅</span>
                    <span className="text-gray-300">
                      Decision = GO + State = DETERMINISTIC → 자동 진행
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-yellow-400">⚠️</span>
                    <span className="text-gray-300">
                      Decision = GO WITH CP → 체크포인트 설정 (주 2회)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-red-400">❌</span>
                    <span className="text-gray-300">
                      Decision = NO GO → Recommended Actions 먼저
                    </span>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="text-center pt-4 border-t border-gray-700">
                <p className="text-sm text-gray-400">
                  상세 가이드는 Obsidian의{" "}
                  <span className="text-blue-400 font-mono">
                    UDO-Development-Platform/Decision-Flow-Guide.md
                  </span>{" "}
                  참조
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

interface StepCardProps {
  number: string
  title: string
  subtitle: string
  duration: string
  color: "green" | "purple" | "yellow" | "blue" | "orange"
  icon: React.ReactNode
  children: React.ReactNode
}

function StepCard({
  number,
  title,
  subtitle,
  duration,
  color,
  icon,
  children,
}: StepCardProps) {
  const colorClasses = {
    green: "bg-green-500/20 text-green-400 border-green-500/50",
    purple: "bg-purple-500/20 text-purple-400 border-purple-500/50",
    yellow: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50",
    blue: "bg-blue-500/20 text-blue-400 border-blue-500/50",
    orange: "bg-orange-500/20 text-orange-400 border-orange-500/50",
  }

  return (
    <div className="bg-gray-900/30 rounded-lg border border-gray-700 p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex items-center justify-center w-10 h-10 rounded-full border-2 font-bold text-lg",
              colorClasses[color]
            )}
          >
            {number}
          </div>
          <div>
            <h3 className="text-white font-semibold flex items-center gap-2">
              {title}
              <span className={cn("text-sm", colorClasses[color].split(" ")[1])}>
                {icon}
              </span>
            </h3>
            <p className="text-sm text-gray-400">{subtitle}</p>
          </div>
        </div>
        <span className="text-xs bg-gray-700 px-2 py-1 rounded text-gray-300">
          {duration}
        </span>
      </div>
      <div className="ml-13">{children}</div>
    </div>
  )
}

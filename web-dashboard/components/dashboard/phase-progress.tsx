"use client"

import { motion } from "framer-motion"
import { Layers, CheckCircle2, Circle, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface PhaseInfo {
  id: string
  name: string
  description: string
  whatToDo: string[]
  expectedOutcome: string
  estimatedDuration: string
}

interface PhaseProgressProps {
  currentPhase: string
  onPhaseChange: (phase: string) => void
}

export function PhaseProgress({ currentPhase, onPhaseChange }: PhaseProgressProps) {
  const phases: PhaseInfo[] = [
    {
      id: "ideation",
      name: "💡 Ideation",
      description: "아이디어 구상 및 요구사항 정의",
      whatToDo: [
        "문제 정의 및 목표 설정",
        "사용자 요구사항 수집",
        "초기 PRD 작성"
      ],
      expectedOutcome: "불확실성: VOID(5%) → QUANTUM(50%)",
      estimatedDuration: "1-2주"
    },
    {
      id: "design",
      name: "📐 Design",
      description: "시스템 설계 및 아키텍처",
      whatToDo: [
        "시스템 아키텍처 설계",
        "데이터베이스 스키마 정의",
        "API 스펙 작성"
      ],
      expectedOutcome: "불확실성: QUANTUM(50%) → PROBABILISTIC(30%)",
      estimatedDuration: "1-2주"
    },
    {
      id: "mvp",
      name: "🚀 MVP",
      description: "최소 기능 제품",
      whatToDo: [
        "핵심 기능 구현",
        "기본 테스트 작성",
        "초기 사용자 피드백"
      ],
      expectedOutcome: "불확실성: PROBABILISTIC(30%) → DETERMINISTIC(15%)",
      estimatedDuration: "2-3주"
    },
    {
      id: "implementation",
      name: "💻 Implementation",
      description: "전체 기능 구현",
      whatToDo: [
        "전체 기능 완성",
        "테스트 커버리지 70%+",
        "CI/CD 파이프라인 구축"
      ],
      expectedOutcome: "불확실성: CHAOTIC(33%) → PROBABILISTIC(15%)",
      estimatedDuration: "4-6주"
    },
    {
      id: "testing",
      name: "🧪 Testing",
      description: "품질 보증",
      whatToDo: [
        "통합 테스트 완료",
        "성능 테스트 통과",
        "보안 검증"
      ],
      expectedOutcome: "불확실성: PROBABILISTIC(15%) → DETERMINISTIC(5%)",
      estimatedDuration: "1-2주"
    },
  ]

  const currentIndex = phases.findIndex(p => p.id === currentPhase)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
    >
      <div className="flex items-center gap-3 mb-4">
        <Layers className="h-5 w-5 text-blue-400" />
        <h2 className="text-xl font-semibold text-white">Development Phase</h2>
      </div>

      <div className="space-y-3">
        {phases.map((phase, index) => {
          const isCompleted = index < currentIndex
          const isCurrent = phase.id === currentPhase
          const isFuture = index > currentIndex

          return (
            <motion.button
              key={phase.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onPhaseChange(phase.id)}
              className={cn(
                "w-full p-3 rounded-lg flex items-center gap-3 transition-all",
                isCurrent && "bg-blue-500/20 border border-blue-500/50",
                isCompleted && "bg-green-500/10 border border-green-500/30",
                isFuture && "bg-gray-700/30 border border-gray-600/30",
                "hover:bg-gray-700/50"
              )}
            >
              {isCompleted ? (
                <CheckCircle2 className="h-5 w-5 text-green-400 flex-shrink-0" />
              ) : isCurrent ? (
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Circle className="h-5 w-5 text-blue-400 flex-shrink-0" />
                </motion.div>
              ) : (
                <Circle className="h-5 w-5 text-gray-500 flex-shrink-0" />
              )}

              <div className="flex-1 text-left">
                <div className={cn(
                  "font-medium",
                  isCurrent ? "text-blue-300" : isCompleted ? "text-green-300" : "text-gray-400"
                )}>
                  {phase.name}
                </div>
                <div className="text-sm text-gray-500">{phase.description}</div>
              </div>

              {index < phases.length - 1 && (
                <ArrowRight className={cn(
                  "h-4 w-4 flex-shrink-0",
                  isCompleted ? "text-green-400" : "text-gray-600"
                )} />
              )}
            </motion.button>
          )
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Progress</span>
          <span className="text-blue-400 font-medium">
            {Math.round((currentIndex + 1) / phases.length * 100)}%
          </span>
        </div>
        <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${((currentIndex + 1) / phases.length) * 100}%` }}
            transition={{ duration: 0.5 }}
            className="h-full bg-gradient-to-r from-blue-500 to-blue-400"
          />
        </div>
      </div>

      {/* Current Phase Details */}
      {currentIndex >= 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 pt-4 border-t border-gray-700"
        >
          <h3 className="text-sm font-semibold text-blue-300 mb-2">
            📍 Current Phase Details
          </h3>

          <div className="space-y-3 text-sm">
            {/* What to Do */}
            <div>
              <div className="text-gray-400 mb-1">🎯 What to Do:</div>
              <ul className="space-y-1 ml-2">
                {phases[currentIndex].whatToDo.map((item, idx) => (
                  <li key={idx} className="text-gray-300 text-xs">
                    • {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Expected Outcome */}
            <div>
              <div className="text-gray-400 mb-1">💡 Expected Outcome:</div>
              <div className="text-green-300 text-xs">
                {phases[currentIndex].expectedOutcome}
              </div>
            </div>

            {/* Duration */}
            <div className="flex justify-between">
              <span className="text-gray-400">⏱️ Duration:</span>
              <span className="text-yellow-300 text-xs">
                {phases[currentIndex].estimatedDuration}
              </span>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
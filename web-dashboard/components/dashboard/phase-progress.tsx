"use client"

import { motion } from "framer-motion"
import { Layers, CheckCircle2, Circle, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface PhaseProgressProps {
  currentPhase: string
  onPhaseChange: (phase: string) => void
}

export function PhaseProgress({ currentPhase, onPhaseChange }: PhaseProgressProps) {
  const phases = [
    { id: "ideation", name: "Ideation", description: "Concept & Requirements" },
    { id: "design", name: "Design", description: "Architecture & Planning" },
    { id: "mvp", name: "MVP", description: "Minimum Viable Product" },
    { id: "implementation", name: "Implementation", description: "Full Development" },
    { id: "testing", name: "Testing", description: "Quality Assurance" },
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
    </motion.div>
  )
}
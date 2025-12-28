"use client"

import { useState, memo } from "react"
import { motion } from "framer-motion"
import { Play, Pause, RotateCcw, Settings, Send, Loader2 } from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

interface ControlPanelProps {
  onExecute: (task: string, phase: string) => Promise<void>
  currentPhase: string
}

export const ControlPanel = memo(function ControlPanel({ onExecute, currentPhase }: ControlPanelProps) {
  const [task, setTask] = useState("")
  const [isExecuting, setIsExecuting] = useState(false)
  const [selectedMode, setSelectedMode] = useState<"auto" | "manual">("auto")

  const taskTemplates = [
    { label: "Design System", value: "Design a scalable microservices architecture" },
    { label: "Implement Feature", value: "Implement user authentication with JWT" },
    { label: "Fix Bug", value: "Debug and fix performance issues in API endpoints" },
    { label: "Optimize", value: "Optimize database queries for better performance" },
    { label: "Test", value: "Create comprehensive test suite for core modules" }
  ]

  const handleExecute = async () => {
    if (!task.trim()) {
      toast.error("Please enter a task description")
      return
    }

    setIsExecuting(true)
    try {
      await onExecute(task, currentPhase)
      setTask("")
      toast.success("Task executed successfully")
    } catch (error) {
      toast.error("Failed to execute task")
    } finally {
      setIsExecuting(false)
    }
  }

  const handleReset = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/control`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: "reset" })
      })
      if (res.ok) {
        toast.success("System reset successfully")
      }
    } catch (error) {
      toast.error("Failed to reset system")
    }
  }

  const handleTrainModels = async () => {
    setIsExecuting(true)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/train`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      })
      if (res.ok) {
        toast.success("ML models training started")
      }
    } catch (error) {
      toast.error("Failed to start training")
    } finally {
      setIsExecuting(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
    >
      <div className="flex items-center gap-3 mb-4">
        <Settings className="h-5 w-5 text-gray-400" />
        <h2 className="text-xl font-semibold text-white">Control Panel</h2>
      </div>

      {/* Mode Selection */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setSelectedMode("auto")}
          className={cn(
            "flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all",
            selectedMode === "auto"
              ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
              : "bg-gray-700/30 text-gray-400 border border-gray-600/30 hover:bg-gray-700/50"
          )}
        >
          Automatic
        </button>
        <button
          onClick={() => setSelectedMode("manual")}
          className={cn(
            "flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all",
            selectedMode === "manual"
              ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
              : "bg-gray-700/30 text-gray-400 border border-gray-600/30 hover:bg-gray-700/50"
          )}
        >
          Manual
        </button>
      </div>

      {/* Task Input */}
      <div className="space-y-3 mb-4">
        <textarea
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder="Enter task description..."
          className="w-full h-24 px-3 py-2 bg-gray-700/30 border border-gray-600/30 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50 resize-none"
        />

        {/* Quick Templates */}
        <div className="flex flex-wrap gap-2">
          {taskTemplates.map((template) => (
            <button
              key={template.label}
              onClick={() => setTask(template.value)}
              className="text-xs px-2 py-1 bg-gray-700/30 hover:bg-gray-700/50 text-gray-400 hover:text-gray-300 rounded-md transition-all"
            >
              {template.label}
            </button>
          ))}
        </div>
      </div>

      {/* Control Buttons */}
      <div className="grid grid-cols-2 gap-3">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleExecute}
          disabled={isExecuting}
          className={cn(
            "flex items-center justify-center gap-2 py-2.5 rounded-lg font-medium transition-all",
            isExecuting
              ? "bg-gray-700/30 text-gray-500 cursor-not-allowed"
              : "bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700"
          )}
        >
          {isExecuting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Executing...</span>
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              <span>Execute</span>
            </>
          )}
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleReset}
          className="flex items-center justify-center gap-2 py-2.5 bg-gray-700/30 hover:bg-gray-700/50 text-gray-400 hover:text-gray-300 rounded-lg font-medium transition-all"
        >
          <RotateCcw className="h-4 w-4" />
          <span>Reset</span>
        </motion.button>
      </div>

      {/* Additional Actions */}
      <div className="mt-3 pt-3 border-t border-gray-700">
        <button
          onClick={handleTrainModels}
          disabled={isExecuting}
          className="w-full py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 rounded-lg text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Train ML Models
        </button>
      </div>

      {/* Current Phase Indicator */}
      <div className="mt-3 p-2 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <div className="text-xs text-blue-400">
          Executing in: <span className="font-medium">{currentPhase}</span> phase
        </div>
      </div>
    </motion.div>
  )
})

"use client"

import { memo } from "react"
import { motion } from "framer-motion"
import { CheckCircle2, XCircle, Loader2, Activity } from "lucide-react"
import { cn } from "@/lib/utils"

interface SystemStatusProps {
  status: {
    udo?: boolean
    uncertainty?: boolean
    ai_connector?: boolean
    ml_system?: boolean
    bridge?: boolean
    overall?: boolean
  }
}

export const SystemStatus = memo(function SystemStatus({ status }: SystemStatusProps) {
  const components = [
    { name: "UDO Orchestrator", key: "udo", icon: Activity },
    { name: "Uncertainty Map", key: "uncertainty", icon: Activity },
    { name: "AI Connector", key: "ai_connector", icon: Activity },
    { name: "ML System", key: "ml_system", icon: Activity },
    { name: "3-AI Bridge", key: "bridge", icon: Activity },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
    >
      <h2 className="text-xl font-semibold text-white mb-4">System Status</h2>
      <div className="space-y-3">
        {components.map((component, index) => {
          const isActive = status[component.key as keyof typeof status]
          return (
            <motion.div
              key={component.key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={cn(
                "flex items-center justify-between p-3 rounded-lg",
                isActive ? "bg-green-500/10" : "bg-red-500/10"
              )}
            >
              <div className="flex items-center gap-3">
                <component.icon className={cn(
                  "h-5 w-5",
                  isActive ? "text-green-400" : "text-red-400"
                )} />
                <span className="text-gray-300">{component.name}</span>
              </div>
              {isActive ? (
                <CheckCircle2 className="h-5 w-5 text-green-400" />
              ) : (
                <XCircle className="h-5 w-5 text-red-400" />
              )}
            </motion.div>
          )
        })}
      </div>
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Overall System</span>
          <span className={cn(
            "px-3 py-1 rounded-full text-sm font-medium",
            status.overall
              ? "bg-green-500/20 text-green-400"
              : "bg-yellow-500/20 text-yellow-400"
          )}>
            {status.overall ? "Operational" : "Limited"}
          </span>
        </div>
      </div>
    </motion.div>
  )
})

"use client"

import { motion } from "framer-motion"
import { Brain, Cpu, Sparkles, CheckCircle2, XCircle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface AICollaborationProps {
  services: {
    claude?: { status: string; last_used?: string }
    codex?: { status: string; last_used?: string }
    gemini?: { status: string; last_used?: string }
  }
}

export function AICollaboration({ services }: AICollaborationProps) {
  const aiServices = [
    {
      name: "Claude",
      icon: Brain,
      status: services.claude?.status || "unknown",
      description: "Primary reasoning & orchestration",
      color: "text-purple-400",
      bgColor: "bg-purple-500/10"
    },
    {
      name: "Codex MCP",
      icon: Cpu,
      status: services.codex?.status || "unknown",
      description: "Code verification & review",
      color: "text-blue-400",
      bgColor: "bg-blue-500/10"
    },
    {
      name: "Gemini",
      icon: Sparkles,
      status: services.gemini?.status || "unknown",
      description: "Creative exploration & patterns",
      color: "text-yellow-400",
      bgColor: "bg-yellow-500/10"
    }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "available":
      case "active":
        return <CheckCircle2 className="h-4 w-4 text-green-400" />
      case "busy":
        return <Loader2 className="h-4 w-4 text-yellow-400 animate-spin" />
      case "error":
      case "unavailable":
        return <XCircle className="h-4 w-4 text-red-400" />
      default:
        return <XCircle className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "available":
        return "Ready"
      case "active":
        return "Active"
      case "busy":
        return "Processing"
      case "error":
        return "Error"
      case "unavailable":
        return "Offline"
      default:
        return "Unknown"
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
    >
      <div className="flex items-center gap-3 mb-4">
        <Brain className="h-5 w-5 text-purple-400" />
        <h2 className="text-xl font-semibold text-white">AI Collaboration</h2>
      </div>

      <div className="space-y-3">
        {aiServices.map((service, index) => (
          <motion.div
            key={service.name}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={cn(
              "p-3 rounded-lg border",
              service.status === "active" ? "border-green-500/30 bg-green-500/5" :
              service.status === "available" ? "border-gray-600/30 bg-gray-700/30" :
              "border-red-500/30 bg-red-500/5"
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className={cn("p-2 rounded-lg", service.bgColor)}>
                  <service.icon className={cn("h-5 w-5", service.color)} />
                </div>
                <div>
                  <div className="font-medium text-white">{service.name}</div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {service.description}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(service.status)}
                <span className="text-xs text-gray-400">
                  {getStatusText(service.status)}
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Collaboration Pattern */}
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="text-sm text-gray-400 mb-2">Active Pattern</div>
        <div className="bg-gradient-to-r from-purple-500/20 via-blue-500/20 to-yellow-500/20 rounded-lg p-3">
          <div className="text-sm font-medium text-white">Creative Exploration</div>
          <div className="text-xs text-gray-400 mt-1">
            Claude orchestrates → Codex verifies → Gemini explores
          </div>
        </div>
      </div>
    </motion.div>
  )
}
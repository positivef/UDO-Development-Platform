"use client"

import { motion } from "framer-motion"
import { TrendingUp, BarChart3 } from "lucide-react"
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from "recharts"

interface MetricsChartProps {
  metrics: any
}

export function MetricsChart({ metrics }: MetricsChartProps) {
  // Generate sample data for visualization
  const confidenceData = [
    { time: "00:00", confidence: 0.65, uncertainty: 0.35 },
    { time: "04:00", confidence: 0.72, uncertainty: 0.28 },
    { time: "08:00", confidence: 0.78, uncertainty: 0.22 },
    { time: "12:00", confidence: 0.81, uncertainty: 0.19 },
    { time: "16:00", confidence: 0.76, uncertainty: 0.24 },
    { time: "20:00", confidence: 0.83, uncertainty: 0.17 },
    { time: "Now", confidence: metrics?.confidence_level || 0.75, uncertainty: 0.25 }
  ]

  const phaseMetrics = [
    { phase: "Ideation", value: 80, fullMark: 100 },
    { phase: "Design", value: 75, fullMark: 100 },
    { phase: "MVP", value: 60, fullMark: 100 },
    { phase: "Implementation", value: 70, fullMark: 100 },
    { phase: "Testing", value: 85, fullMark: 100 }
  ]

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
    >
      <div className="flex items-center gap-3 mb-4">
        <BarChart3 className="h-5 w-5 text-blue-400" />
        <h2 className="text-xl font-semibold text-white">Performance Metrics</h2>
      </div>

      {/* Confidence Trend */}
      <div className="mb-6">
        <div className="text-sm text-gray-400 mb-2">Confidence Trend (24h)</div>
        <ResponsiveContainer width="100%" height={150}>
          <AreaChart data={confidenceData}>
            <defs>
              <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="time" stroke="#9ca3af" fontSize={10} />
            <YAxis stroke="#9ca3af" fontSize={10} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "1px solid #374151",
                borderRadius: "8px"
              }}
              labelStyle={{ color: "#9ca3af" }}
            />
            <Area
              type="monotone"
              dataKey="confidence"
              stroke="#3b82f6"
              fillOpacity={1}
              fill="url(#colorConfidence)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Phase Performance Radar */}
      <div>
        <div className="text-sm text-gray-400 mb-2">Phase Performance</div>
        <ResponsiveContainer width="100%" height={150}>
          <RadarChart data={phaseMetrics}>
            <PolarGrid stroke="#374151" />
            <PolarAngleAxis dataKey="phase" stroke="#9ca3af" fontSize={10} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#374151" fontSize={10} />
            <Radar
              name="Performance"
              dataKey="value"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.3}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-3 mt-4">
        <div className="bg-gray-700/30 rounded-lg p-3">
          <div className="text-xs text-gray-400">Avg Confidence</div>
          <div className="text-lg font-bold text-blue-400">
            {Math.round((metrics?.performance_metrics?.avg_confidence || 0) * 100)}%
          </div>
        </div>
        <div className="bg-gray-700/30 rounded-lg p-3">
          <div className="text-xs text-gray-400">Total Executions</div>
          <div className="text-lg font-bold text-green-400">
            {metrics?.performance_metrics?.execution_count || 0}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
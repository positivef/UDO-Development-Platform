"use client"

/**
 * Uncertainty Prediction Chart
 *
 * Recharts-based visualization for 24-hour uncertainty prediction trends
 * Shows historical data and predicted future states with confidence intervals
 */

import { useMemo } from "react"
import {
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts"
import { motion } from "framer-motion"
import { TrendingUp, Clock } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

interface PredictionChartProps {
  currentConfidence: number
  prediction?: {
    trend?: string
    velocity?: number
    acceleration?: number
    predicted_resolution?: string | null
    confidence_interval_lower?: number
    confidence_interval_upper?: number
  } | null
  vector?: {
    technical?: number
    market?: number
    resource?: number
    timeline?: number
    quality?: number
    magnitude?: number
  }
}

export function UncertaintyPredictionChart({
  currentConfidence,
  prediction,
  vector
}: PredictionChartProps) {
  // Generate 24-hour prediction data points
  const chartData = useMemo(() => {
    const dataPoints = []
    const hoursToPredict = 24
    const currentTime = new Date()

    // Current state (hour 0)
    dataPoints.push({
      hour: 0,
      time: currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      confidence: currentConfidence * 100,
      upper: Math.min(100, (prediction?.confidence_interval_upper ?? currentConfidence) * 100),
      lower: Math.max(0, (prediction?.confidence_interval_lower ?? currentConfidence) * 100),
      predicted: currentConfidence * 100,
      isActual: true
    })

    // Generate future predictions
    const velocity = prediction?.velocity ?? 0
    const acceleration = prediction?.acceleration ?? 0

    for (let hour = 1; hour <= hoursToPredict; hour++) {
      const futureTime = new Date(currentTime.getTime() + hour * 60 * 60 * 1000)

      // Physics-based prediction: position = initial + velocity*t + 0.5*acceleration*t^2
      const predictedChange = velocity * hour + 0.5 * acceleration * hour * hour
      const predictedConfidence = Math.max(0, Math.min(100, (currentConfidence + predictedChange) * 100))

      // Confidence interval widens over time
      const uncertaintyGrowth = Math.sqrt(hour) * 0.05 // Standard error grows with sqrt(time)
      const intervalWidth = (prediction?.confidence_interval_upper ?? currentConfidence) -
                           (prediction?.confidence_interval_lower ?? currentConfidence)
      const expandedWidth = intervalWidth * (1 + uncertaintyGrowth)

      dataPoints.push({
        hour,
        time: futureTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        predicted: predictedConfidence,
        upper: Math.min(100, predictedConfidence + expandedWidth * 50),
        lower: Math.max(0, predictedConfidence - expandedWidth * 50),
        isActual: false
      })
    }

    return dataPoints
  }, [currentConfidence, prediction])

  // Calculate trend direction
  const trendInfo = useMemo(() => {
    const trend = prediction?.trend || "stable"
    const velocity = prediction?.velocity ?? 0

    if (trend === "increasing" || velocity > 0.01) {
      return { icon: "📈", color: "text-green-400", label: "Improving" }
    } else if (trend === "decreasing" || velocity < -0.01) {
      return { icon: "📉", color: "text-red-400", label: "Degrading" }
    } else {
      return { icon: "➡️", color: "text-blue-400", label: "Stable" }
    }
  }, [prediction])

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null

    const data = payload[0].payload

    return (
      <div className="bg-gray-800/95 backdrop-blur-sm border border-gray-700 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-gray-400 mb-2">
          <Clock className="h-3 w-3 inline mr-1" />
          {data.time} {data.isActual ? "(Current)" : `(+${data.hour}h)`}
        </p>
        {data.isActual ? (
          <p className="text-sm font-medium text-white">
            Confidence: <span className="text-blue-400">{data.confidence?.toFixed(1)}%</span>
          </p>
        ) : (
          <>
            <p className="text-sm font-medium text-white mb-1">
              Predicted: <span className="text-purple-400">{data.predicted?.toFixed(1)}%</span>
            </p>
            <p className="text-xs text-gray-400">
              Range: {data.lower?.toFixed(1)}% - {data.upper?.toFixed(1)}%
            </p>
          </>
        )}
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
    >
      <Card className="border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-400" />
            24-Hour Prediction Forecast
            <span className={`ml-auto text-sm ${trendInfo.color}`}>
              {trendInfo.icon} {trendInfo.label}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="confidenceArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="time"
                stroke="#9ca3af"
                tick={{ fontSize: 11 }}
                interval="preserveStartEnd"
                tickFormatter={(value, index) => index % 4 === 0 ? value : ''}
              />
              <YAxis
                stroke="#9ca3af"
                tick={{ fontSize: 11 }}
                domain={[0, 100]}
                label={{ value: 'Confidence (%)', angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#9ca3af' } }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: 12 }}
                iconType="line"
              />

              {/* Confidence interval area */}
              <Area
                type="monotone"
                dataKey="upper"
                stroke="none"
                fill="url(#confidenceArea)"
                fillOpacity={0.4}
                name="Upper Bound"
              />
              <Area
                type="monotone"
                dataKey="lower"
                stroke="none"
                fill="url(#confidenceArea)"
                fillOpacity={0.4}
                name="Lower Bound"
              />

              {/* Current confidence (first point only) */}
              <Line
                type="monotone"
                dataKey="confidence"
                stroke="#3b82f6"
                strokeWidth={3}
                dot={{ r: 6, fill: "#3b82f6" }}
                activeDot={{ r: 8 }}
                name="Current Confidence"
                connectNulls={false}
              />

              {/* Predicted trend */}
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="#8b5cf6"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ r: 3, fill: "#8b5cf6" }}
                activeDot={{ r: 6 }}
                name="Predicted Trend"
              />

              {/* Reference line at current time */}
              <ReferenceLine
                x={chartData[0]?.time}
                stroke="#fbbf24"
                strokeDasharray="3 3"
                label={{ value: "Now", fill: "#fbbf24", fontSize: 11 }}
              />

              {/* Reference line at 70% confidence (target) */}
              <ReferenceLine
                y={70}
                stroke="#10b981"
                strokeDasharray="3 3"
                label={{ value: "Target (70%)", fill: "#10b981", fontSize: 11, position: "insideTopRight" }}
              />
            </AreaChart>
          </ResponsiveContainer>

          {/* Prediction Details */}
          <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
            <div className="bg-gray-700/30 rounded p-2">
              <span className="text-gray-400 block mb-1">Velocity</span>
              <span className={`font-medium ${(prediction?.velocity ?? 0) > 0 ? 'text-green-400' : (prediction?.velocity ?? 0) < 0 ? 'text-red-400' : 'text-gray-300'}`}>
                {prediction?.velocity !== undefined ? `${(prediction.velocity * 100).toFixed(2)}% /h` : 'N/A'}
              </span>
            </div>
            <div className="bg-gray-700/30 rounded p-2">
              <span className="text-gray-400 block mb-1">Acceleration</span>
              <span className={`font-medium ${(prediction?.acceleration ?? 0) > 0 ? 'text-green-400' : (prediction?.acceleration ?? 0) < 0 ? 'text-red-400' : 'text-gray-300'}`}>
                {prediction?.acceleration !== undefined ? `${(prediction.acceleration * 10000).toFixed(3)}% /h²` : 'N/A'}
              </span>
            </div>
            <div className="bg-gray-700/30 rounded p-2">
              <span className="text-gray-400 block mb-1">Resolution ETA</span>
              <span className="font-medium text-blue-400">
                {prediction?.predicted_resolution
                  ? new Date(prediction.predicted_resolution).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                  : 'Unknown'
                }
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

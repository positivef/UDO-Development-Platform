"use client"

/**
 * ConfidenceTrendChart - Historical confidence trend visualization
 *
 * Features:
 * - 7-day line chart with confidence scores
 * - Phase threshold reference line
 * - Decision marker points (GO/NO_GO)
 * - Animated transitions
 * - Trend direction indicator
 */

import { memo, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
} from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown, Minus, Calendar, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TrendDataPoint {
  date: string
  confidence: number
  decision: 'GO' | 'GO_WITH_CHECKPOINTS' | 'NO_GO'
  phase: string
}

interface ConfidenceTrendChartProps {
  currentConfidence: number
  currentPhase: string
  phaseThreshold: number
  historicalData?: TrendDataPoint[]
  isLoading?: boolean
}

// Generate mock historical data if not provided
function generateMockData(currentConfidence: number, days: number = 7): TrendDataPoint[] {
  const data: TrendDataPoint[] = []
  const now = new Date()

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)

    // Generate realistic variance around current confidence
    const variance = (Math.random() - 0.5) * 0.2
    const confidence = Math.max(0.3, Math.min(0.95, currentConfidence + variance - (i * 0.02)))

    let decision: 'GO' | 'GO_WITH_CHECKPOINTS' | 'NO_GO'
    if (confidence >= 0.7) decision = 'GO'
    else if (confidence >= 0.5) decision = 'GO_WITH_CHECKPOINTS'
    else decision = 'NO_GO'

    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      confidence: Number(confidence.toFixed(3)),
      decision,
      phase: 'implementation',
    })
  }

  return data
}

// Custom tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    const decisionColors = {
      GO: 'text-green-400',
      GO_WITH_CHECKPOINTS: 'text-yellow-400',
      NO_GO: 'text-red-400',
    }

    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
        <p className="text-sm font-medium text-gray-200 mb-2">{label}</p>
        <div className="space-y-1">
          <p className="text-lg font-bold text-blue-400">
            {(data.confidence * 100).toFixed(1)}%
          </p>
          <p className={cn('text-sm', decisionColors[data.decision as keyof typeof decisionColors])}>
            Decision: {data.decision.replace(/_/g, ' ')}
          </p>
        </div>
      </div>
    )
  }
  return null
}

// Custom dot for data points
const CustomDot = (props: any) => {
  const { cx, cy, payload } = props
  const colors = {
    GO: '#22c55e',
    GO_WITH_CHECKPOINTS: '#eab308',
    NO_GO: '#ef4444',
  }

  return (
    <circle
      cx={cx}
      cy={cy}
      r={5}
      fill={colors[payload.decision as keyof typeof colors]}
      stroke="#1f2937"
      strokeWidth={2}
    />
  )
}

export const ConfidenceTrendChart = memo(function ConfidenceTrendChart({
  currentConfidence,
  currentPhase,
  phaseThreshold,
  historicalData,
  isLoading = false,
}: ConfidenceTrendChartProps) {
  // Use provided data or generate mock
  const chartData = useMemo(() => {
    return historicalData || generateMockData(currentConfidence)
  }, [historicalData, currentConfidence])

  // Calculate trend direction
  const trend = useMemo(() => {
    if (chartData.length < 2) return 'stable'
    const first = chartData[0].confidence
    const last = chartData[chartData.length - 1].confidence
    const change = last - first

    if (change > 0.05) return 'up'
    if (change < -0.05) return 'down'
    return 'stable'
  }, [chartData])

  const trendConfig = {
    up: { icon: TrendingUp, color: 'text-green-400', label: 'Improving', bg: 'bg-green-500/20 border-green-500/50' },
    down: { icon: TrendingDown, color: 'text-red-400', label: 'Declining', bg: 'bg-red-500/20 border-red-500/50' },
    stable: { icon: Minus, color: 'text-gray-400', label: 'Stable', bg: 'bg-gray-500/20 border-gray-500/50' },
  }

  const TrendIcon = trendConfig[trend].icon

  if (isLoading) {
    return (
      <Card className="border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Calendar className="h-5 w-5 text-blue-400" />
            Confidence Trend
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-700 rounded w-1/3"></div>
            <div className="h-64 bg-gray-700 rounded"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      <Card className="border-gray-700">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-400" />
              7-Day Confidence Trend
            </CardTitle>
            <Badge
              variant="outline"
              className={cn('text-xs flex items-center gap-1', trendConfig[trend].bg, trendConfig[trend].color)}
            >
              <TrendIcon className="h-3 w-3" />
              {trendConfig[trend].label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Summary stats */}
          <div className="grid grid-cols-4 gap-3">
            <div className="bg-gray-800/50 rounded-lg p-3 text-center">
              <div className="text-xs text-gray-400 mb-1">Current</div>
              <div className="text-lg font-bold text-blue-400">
                {(currentConfidence * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3 text-center">
              <div className="text-xs text-gray-400 mb-1">7-Day Avg</div>
              <div className="text-lg font-bold text-gray-200">
                {(chartData.reduce((sum, d) => sum + d.confidence, 0) / chartData.length * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3 text-center">
              <div className="text-xs text-gray-400 mb-1">Peak</div>
              <div className="text-lg font-bold text-green-400">
                {(Math.max(...chartData.map(d => d.confidence)) * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3 text-center">
              <div className="text-xs text-gray-400 mb-1">Low</div>
              <div className="text-lg font-bold text-red-400">
                {(Math.min(...chartData.map(d => d.confidence)) * 100).toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="date"
                  stroke="#6b7280"
                  fontSize={12}
                  tickLine={false}
                />
                <YAxis
                  stroke="#6b7280"
                  fontSize={12}
                  tickLine={false}
                  domain={[0, 1]}
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                />
                <Tooltip content={<CustomTooltip />} />

                {/* Phase threshold reference line */}
                <ReferenceLine
                  y={phaseThreshold / 100}
                  stroke="#6b7280"
                  strokeDasharray="5 5"
                  label={{
                    value: `${currentPhase} threshold (${phaseThreshold}%)`,
                    position: 'insideTopRight',
                    fill: '#9ca3af',
                    fontSize: 10,
                  }}
                />

                {/* Area under the line */}
                <Area
                  type="monotone"
                  dataKey="confidence"
                  stroke="transparent"
                  fill="url(#confidenceGradient)"
                />

                {/* Main confidence line */}
                <Line
                  type="monotone"
                  dataKey="confidence"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={<CustomDot />}
                  activeDot={{ r: 8, fill: '#3b82f6', stroke: '#1f2937', strokeWidth: 2 }}
                  animationDuration={1000}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Legend */}
          <div className="flex flex-wrap justify-center gap-4 pt-2 border-t border-gray-700">
            <div className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-gray-400">GO</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <span className="text-gray-400">GO WITH CHECKPOINTS</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span className="text-gray-400">NO GO</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-6 h-0.5 bg-gray-500" style={{ borderStyle: 'dashed' }} />
              <span className="text-gray-400">Phase Threshold</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
})

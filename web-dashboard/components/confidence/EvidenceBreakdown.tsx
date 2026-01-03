"use client"

/**
 * EvidenceBreakdown - Evidence contribution visualization
 *
 * Features:
 * - Horizontal bar chart showing 4 contribution sources
 * - Color-coded by contribution strength
 * - Animated bars with Recharts
 * - Evidence strength badge
 */

import { memo } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  ResponsiveContainer,
  Tooltip,
  LabelList,
} from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { FlaskConical, CheckCircle, Code, Users, GitBranch } from 'lucide-react'
import { cn } from '@/lib/utils'

interface EvidenceBreakdownProps {
  breakdown?: {
    test_contribution: number
    coverage_contribution: number
    review_contribution: number
    dependency_contribution: number
  }
  evidenceStrength?: 'weak' | 'moderate' | 'strong' | 'very_strong'
  isLoading?: boolean
}

const strengthConfig = {
  weak: { color: 'text-red-400', bg: 'bg-red-500/20 border-red-500/50', label: 'Weak' },
  moderate: { color: 'text-yellow-400', bg: 'bg-yellow-500/20 border-yellow-500/50', label: 'Moderate' },
  strong: { color: 'text-green-400', bg: 'bg-green-500/20 border-green-500/50', label: 'Strong' },
  very_strong: { color: 'text-blue-400', bg: 'bg-blue-500/20 border-blue-500/50', label: 'Very Strong' },
}

const contributionConfig = [
  { key: 'test_contribution', name: 'Test Results', icon: CheckCircle, color: '#22c55e' },
  { key: 'coverage_contribution', name: 'Code Coverage', icon: Code, color: '#3b82f6' },
  { key: 'review_contribution', name: 'Code Reviews', icon: Users, color: '#a855f7' },
  { key: 'dependency_contribution', name: 'Dependencies', icon: GitBranch, color: '#eab308' },
]

// Custom tooltip for the chart
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
        <p className="text-sm font-medium text-gray-200">{data.name}</p>
        <p className="text-lg font-bold" style={{ color: data.color }}>
          {(data.value * 100).toFixed(1)}%
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Contribution to overall confidence
        </p>
      </div>
    )
  }
  return null
}

export const EvidenceBreakdown = memo(function EvidenceBreakdown({
  breakdown,
  evidenceStrength = 'moderate',
  isLoading = false,
}: EvidenceBreakdownProps) {
  if (isLoading) {
    return (
      <Card className="border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <FlaskConical className="h-5 w-5 text-purple-400" />
            Evidence Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-700 rounded w-1/3"></div>
            <div className="h-48 bg-gray-700 rounded"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Default breakdown if not provided
  const data = breakdown || {
    test_contribution: 0.3,
    coverage_contribution: 0.25,
    review_contribution: 0.25,
    dependency_contribution: 0.2,
  }

  // Transform data for chart
  const chartData = contributionConfig.map((config) => ({
    name: config.name,
    value: data[config.key as keyof typeof data] || 0,
    color: config.color,
    icon: config.icon,
  }))

  // Calculate total for percentage display
  const total = chartData.reduce((sum, item) => sum + item.value, 0)

  const strength = strengthConfig[evidenceStrength]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
    >
      <Card className="border-gray-700">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <FlaskConical className="h-5 w-5 text-purple-400" />
              Evidence Breakdown
            </CardTitle>
            <Badge
              variant="outline"
              className={cn('text-xs', strength.bg, strength.color)}
            >
              {strength.label} Evidence
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Summary row */}
          <div className="grid grid-cols-4 gap-2">
            {chartData.map((item, idx) => {
              const Icon = contributionConfig[idx].icon
              return (
                <div
                  key={item.name}
                  className="bg-gray-800/50 rounded-lg p-3 text-center"
                >
                  <Icon
                    className="h-5 w-5 mx-auto mb-1"
                    style={{ color: item.color }}
                  />
                  <div
                    className="text-lg font-bold"
                    style={{ color: item.color }}
                  >
                    {(item.value * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-400 truncate">
                    {item.name}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Bar Chart */}
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <XAxis
                  type="number"
                  domain={[0, 0.5]}
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                  stroke="#6b7280"
                  fontSize={12}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={100}
                  stroke="#6b7280"
                  fontSize={12}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(107, 114, 128, 0.1)' }} />
                <Bar
                  dataKey="value"
                  radius={[0, 4, 4, 0]}
                  animationDuration={800}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                  <LabelList
                    dataKey="value"
                    position="right"
                    formatter={(value) => `${(Number(value) * 100).toFixed(1)}%`}
                    fill="#9ca3af"
                    fontSize={12}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Legend */}
          <div className="flex flex-wrap justify-center gap-4 pt-2 border-t border-gray-700">
            {chartData.map((item, idx) => {
              const Icon = contributionConfig[idx].icon
              return (
                <div key={item.name} className="flex items-center gap-2 text-sm">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <Icon className="h-3 w-3 text-gray-400" />
                  <span className="text-gray-400">{item.name}</span>
                </div>
              )
            })}
          </div>

          {/* Total confidence contribution info */}
          <div className="bg-gray-800/30 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-400">
              Combined evidence contributes{' '}
              <span className="font-semibold text-blue-400">
                {(total * 100).toFixed(1)}%
              </span>{' '}
              to confidence calculation
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
})

"use client"

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts"
import type { TimeMetrics } from "@/lib/types/time-tracking"

interface AIPerformanceChartProps {
  aiPerformance: TimeMetrics["ai_performance"] | undefined
}

const COLORS = {
  Claude: "hsl(220 70% 50%)",
  Codex: "hsl(142 76% 36%)",
  Gemini: "hsl(24 70% 50%)",
  Default: "hsl(var(--primary))",
}

export function AIPerformanceChart({ aiPerformance }: AIPerformanceChartProps) {
  if (!aiPerformance) {
    return null
  }

  const chartData = Object.entries(aiPerformance).map(([service, data]) => ({
    name: service,
    value: data.tasks,
    avgDuration: data.avg_duration_minutes,
    successRate: data.success_rate,
  }))

  const getColor = (name: string): string => {
    return COLORS[name as keyof typeof COLORS] || COLORS.Default
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Service Performance</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="hsl(var(--primary))"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColor(entry.name)} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
              formatter={(value, name, props) => [
                `${value} tasks (${props.payload.successRate.toFixed(1)}% success, ${props.payload.avgDuration.toFixed(1)}min avg)`,
                props.payload.name,
              ]}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

"use client"

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import type { TimeMetrics } from "@/lib/types/time-tracking"

interface TasksByPhaseChartProps {
  tasksByPhase: TimeMetrics["tasks_by_phase"] | undefined
}

export function TasksByPhaseChart({ tasksByPhase }: TasksByPhaseChartProps) {
  if (!tasksByPhase) {
    return null
  }

  const chartData = Object.entries(tasksByPhase).map(([phase, count]) => ({
    phase: phase.charAt(0).toUpperCase() + phase.slice(1),
    tasks: count,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tasks by Phase</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="phase"
              className="text-xs"
              tick={{ fill: "currentColor" }}
            />
            <YAxis
              className="text-xs"
              tick={{ fill: "currentColor" }}
              label={{ value: "Tasks", angle: -90, position: "insideLeft" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
            />
            <Legend />
            <Bar
              dataKey="tasks"
              fill="hsl(var(--primary))"
              radius={[8, 8, 0, 0]}
              name="Tasks Completed"
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

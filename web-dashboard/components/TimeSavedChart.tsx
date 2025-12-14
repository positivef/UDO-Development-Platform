"use client"

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import { format } from "date-fns"
import type { TrendDataPoint } from "@/lib/types/time-tracking"

interface TimeSavedChartProps {
  data: TrendDataPoint[]
}

export function TimeSavedChart({ data }: TimeSavedChartProps) {
  const chartData = data.map((point) => ({
    ...point,
    date: format(new Date(point.date), "MMM dd"),
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Time Saved Trend (30 Days)</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="date"
              className="text-xs"
              tick={{ fill: "currentColor" }}
            />
            <YAxis
              className="text-xs"
              tick={{ fill: "currentColor" }}
              label={{ value: "Hours", angle: -90, position: "insideLeft" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="time_saved_hours"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              name="Time Saved"
              dot={{ fill: "hsl(var(--primary))", r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="baseline_hours"
              stroke="hsl(var(--muted-foreground))"
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Baseline"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="actual_hours"
              stroke="hsl(220 70% 50%)"
              strokeWidth={2}
              name="Actual"
              dot={{ fill: "hsl(220 70% 50%)", r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

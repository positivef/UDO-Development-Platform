"use client"

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { formatNumber, formatPercentage } from "@/lib/time-tracking-utils"
import { TrendingUp, TrendingDown, Minus, Clock, DollarSign, CheckCircle2, Zap } from "lucide-react"
import type { TimeMetrics, ROIReport } from "@/lib/types/time-tracking"

interface StatCardProps {
  title: string
  value: string | number
  change: string
  trend: "up" | "down" | "neutral"
  icon: React.ReactNode
}

function StatCard({ title, value, change, trend, icon }: StatCardProps) {
  const getTrendIcon = () => {
    switch (trend) {
      case "up":
        return <TrendingUp className="h-4 w-4" />
      case "down":
        return <TrendingDown className="h-4 w-4" />
      default:
        return <Minus className="h-4 w-4" />
    }
  }

  const getTrendColor = () => {
    switch (trend) {
      case "up":
        return "text-green-600 dark:text-green-400"
      case "down":
        return "text-red-600 dark:text-red-400"
      default:
        return "text-gray-600 dark:text-gray-400"
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
            {icon}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold">{value}</div>
        <div className={cn("flex items-center gap-1 mt-2 text-sm", getTrendColor())}>
          {getTrendIcon()}
          <span>{change}</span>
        </div>
      </CardContent>
    </Card>
  )
}

interface TimeTrackingStatsProps {
  metrics: TimeMetrics | undefined
  roi: ROIReport | undefined
}

export function TimeTrackingStats({ metrics, roi }: TimeTrackingStatsProps) {
  if (!metrics || !roi) {
    return null
  }

  const getTrend = (value: number): "up" | "down" | "neutral" => {
    if (value > 0) return "up"
    if (value < 0) return "down"
    return "neutral"
  }

  const stats = [
    {
      title: "Time Saved",
      value: `${formatNumber(metrics.time_saved_hours, 1)}h`,
      change: formatPercentage(roi.comparison.change_percent),
      trend: getTrend(roi.comparison.change_percent),
      icon: <Clock className="h-5 w-5" />,
    },
    {
      title: "ROI Percentage",
      value: `${formatNumber(roi.roi_percentage, 0)}%`,
      change: formatPercentage(roi.comparison.change_percent),
      trend: getTrend(roi.comparison.change_percent),
      icon: <DollarSign className="h-5 w-5" />,
    },
    {
      title: "Tasks Completed",
      value: formatNumber(metrics.tasks_completed),
      change: "vs last week",
      trend: "neutral" as "up" | "down" | "neutral",
      icon: <CheckCircle2 className="h-5 w-5" />,
    },
    {
      title: "Efficiency Gain",
      value: `${formatNumber(metrics.efficiency_gain_percent, 1)}%`,
      change: `${formatNumber(roi.productivity_multiplier, 1)}x multiplier`,
      trend: getTrend(metrics.efficiency_gain_percent),
      icon: <Zap className="h-5 w-5" />,
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <StatCard
          key={index}
          title={stat.title}
          value={stat.value}
          change={stat.change}
          trend={stat.trend}
          icon={stat.icon}
        />
      ))}
    </div>
  )
}

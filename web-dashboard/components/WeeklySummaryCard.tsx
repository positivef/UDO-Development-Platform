"use client"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Lightbulb, TrendingUp, Award } from "lucide-react"
import type { WeeklySummary } from "@/lib/types/time-tracking"
import { formatDuration } from "@/lib/time-tracking-utils"

interface WeeklySummaryCardProps {
  summary: WeeklySummary | undefined
}

export function WeeklySummaryCard({ summary }: WeeklySummaryCardProps) {
  if (!summary) {
    return null
  }

  const getGradeColor = (grade: WeeklySummary["overall_grade"]) => {
    if (grade.startsWith("A")) return "bg-green-500/10 text-green-600 dark:text-green-400"
    if (grade.startsWith("B")) return "bg-blue-500/10 text-blue-600 dark:text-blue-400"
    if (grade.startsWith("C")) return "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400"
    return "bg-red-500/10 text-red-600 dark:text-red-400"
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Weekly Summary</CardTitle>
            <CardDescription>{summary.period}</CardDescription>
          </div>
          <div className={`text-3xl font-bold px-4 py-2 rounded-lg ${getGradeColor(summary.overall_grade)}`}>
            {summary.overall_grade}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Highlights */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Award className="h-5 w-5 text-amber-500" />
            <h3 className="font-semibold">Highlights</h3>
          </div>
          <ul className="space-y-2">
            {summary.highlights.map((highlight, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <span className="text-primary mt-0.5">•</span>
                <span>{highlight}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Top Performers */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-5 w-5 text-green-500" />
            <h3 className="font-semibold">Top Performers</h3>
          </div>
          <div className="space-y-2">
            {summary.top_performers.map((performer, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
              >
                <span className="text-sm font-medium">{performer.task_type}</span>
                <Badge variant="secondary">
                  {formatDuration(performer.time_saved)} saved
                </Badge>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="h-5 w-5 text-blue-500" />
            <h3 className="font-semibold">Recommendations</h3>
          </div>
          <ul className="space-y-2">
            {summary.recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-muted-foreground">
                <span className="text-blue-500 mt-0.5">→</span>
                <span>{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}

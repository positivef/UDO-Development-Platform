"use client"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatDuration, getSeverityVariant } from "@/lib/time-tracking-utils"
import type { Bottleneck } from "@/lib/types/time-tracking"
import { AlertTriangle } from "lucide-react"

interface BottlenecksTableProps {
  bottlenecks: Bottleneck[]
}

export function BottlenecksTable({ bottlenecks }: BottlenecksTableProps) {
  if (bottlenecks.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active Bottlenecks</CardTitle>
          <CardDescription>Tasks taking longer than baseline</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <CheckCircle2 className="h-12 w-12 mb-4" />
            <p>No bottlenecks detected</p>
            <p className="text-sm">All tasks are performing within baseline expectations</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-500" />
          <CardTitle>Active Bottlenecks</CardTitle>
        </div>
        <CardDescription>
          {bottlenecks.length} task{bottlenecks.length !== 1 ? "s" : ""} taking longer than baseline
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Task Type</TableHead>
              <TableHead>Avg Duration</TableHead>
              <TableHead>Baseline</TableHead>
              <TableHead>Overrun</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead className="text-right">Count</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {bottlenecks.map((bottleneck, index) => (
              <TableRow key={index}>
                <TableCell className="font-medium">
                  {bottleneck.task_type}
                </TableCell>
                <TableCell>{formatDuration(bottleneck.avg_duration)}</TableCell>
                <TableCell className="text-muted-foreground">
                  {formatDuration(bottleneck.baseline)}
                </TableCell>
                <TableCell className="text-red-600 dark:text-red-400">
                  +{formatDuration(bottleneck.overrun)}
                </TableCell>
                <TableCell>
                  <Badge variant={getSeverityVariant(bottleneck.severity)}>
                    {bottleneck.severity}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">{bottleneck.count}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

function CheckCircle2({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  )
}

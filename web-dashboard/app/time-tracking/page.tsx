"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Clock, RefreshCw, Calendar, TrendingUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { TimeTrackingStats } from "@/components/TimeTrackingStats"
import { TimeSavedChart } from "@/components/TimeSavedChart"
import { TasksByPhaseChart } from "@/components/TasksByPhaseChart"
import { AIPerformanceChart } from "@/components/AIPerformanceChart"
import { BottlenecksTable } from "@/components/BottlenecksTable"
import { WeeklySummaryCard } from "@/components/WeeklySummaryCard"
import { UncertaintyMap } from "@/components/dashboard/uncertainty-map"
import { useTimeTracking } from "@/lib/hooks/useTimeTracking"
import { useUncertainty } from "@/hooks/useUncertainty"
import { format } from "date-fns"
import { toast } from "sonner"
import { useTranslations } from "next-intl"

export default function TimeTrackingPage() {
  const t = useTranslations('timeTracking')
  const [period, setPeriod] = useState<"day" | "week" | "month">("week")
  const { metrics, roi, bottlenecks, trends, summary, isLoading, isError, refetch } = useTimeTracking(period)
  const { data: uncertaintyData, isLoading: uncertaintyLoading, isError: uncertaintyError } = useUncertainty()

  const handleRefresh = () => {
    refetch()
    toast.success(t('refreshed'))
  }

  const getDateRange = () => {
    if (!metrics?.date_range) return t('loading')
    return `${format(new Date(metrics.date_range.start), "MMM dd")} - ${format(new Date(metrics.date_range.end), "MMM dd, yyyy")}`
  }

  if (isError) {
    return (
      <div className="min-h-screen p-6 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-7xl mx-auto"
        >
          <Card className="border-red-500/50 bg-red-500/10">
            <CardContent className="flex items-center justify-center py-12">
              <div className="text-center">
                <h2 className="text-xl font-bold text-red-500 mb-2">{t('failedToLoad')}</h2>
                <p className="text-muted-foreground mb-4">
                  {t('unableToConnect')}
                </p>
                <Button onClick={handleRefresh} variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  {t('retry')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
        >
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                <Clock className="h-8 w-8 text-blue-500" />
                {t('title')}
              </h1>
              <div className="flex items-center gap-2 mt-2 text-gray-400">
                <Calendar className="h-4 w-4" />
                <span suppressHydrationWarning>{getDateRange()}</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Tabs value={period} onValueChange={(v) => setPeriod(v as typeof period)}>
                <TabsList>
                  <TabsTrigger value="day">{t('periods.day')}</TabsTrigger>
                  <TabsTrigger value="week">{t('periods.week')}</TabsTrigger>
                  <TabsTrigger value="month">{t('periods.month')}</TabsTrigger>
                </TabsList>
              </Tabs>
              <Button
                onClick={handleRefresh}
                variant="outline"
                size="icon"
                className="text-blue-400 border-blue-500/50 hover:bg-blue-500/10"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Hero Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
          ) : (
            <TimeTrackingStats metrics={metrics} roi={roi} />
          )}
        </motion.div>

        {/* Uncertainty Map Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          {uncertaintyLoading ? (
            <Skeleton className="h-[600px]" />
          ) : uncertaintyError ? (
            <Card className="border-yellow-500/50 bg-yellow-500/10">
              <CardContent className="flex items-center justify-center py-8">
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-yellow-500 mb-2">
                    {t('uncertaintyUnavailable')}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {t('uncertaintyOffline')}
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : uncertaintyData ? (
            <UncertaintyMap
              state={uncertaintyData.state}
              confidence={uncertaintyData.confidence_score}
              prediction={uncertaintyData.prediction}
              mitigations={uncertaintyData.mitigations}
              vector={uncertaintyData.vector}
              isLoading={uncertaintyLoading}
            />
          ) : null}
        </motion.div>

        {/* Charts Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6"
        >
          {isLoading ? (
            <>
              <Skeleton className="h-[400px] lg:col-span-2" />
              <Skeleton className="h-[400px]" />
            </>
          ) : (
            <>
              <div className="lg:col-span-2">
                <TimeSavedChart data={trends} />
              </div>
              <TasksByPhaseChart tasksByPhase={metrics?.tasks_by_phase} />
            </>
          )}
        </motion.div>

        {/* AI Performance and Bottlenecks */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6"
        >
          {isLoading ? (
            <>
              <Skeleton className="h-[400px]" />
              <Skeleton className="h-[400px]" />
            </>
          ) : (
            <>
              <AIPerformanceChart aiPerformance={metrics?.ai_performance} />
              <BottlenecksTable bottlenecks={bottlenecks as any} />
            </>
          )}
        </motion.div>

        {/* Weekly Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
        >
          {isLoading ? (
            <Skeleton className="h-[500px]" />
          ) : (
            <WeeklySummaryCard summary={summary as any} />
          )}
        </motion.div>
      </div>
    </div>
  )
}

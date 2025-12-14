"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Activity, RefreshCw, Gauge, Target, TrendingUp, Shield, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BayesianConfidence } from "@/components/dashboard/bayesian-confidence"
import { useConfidence, useConfidenceMutation } from "@/hooks/useConfidence"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

const phases = [
  { value: "ideation", label: "Ideation", threshold: 60 },
  { value: "design", label: "Design", threshold: 65 },
  { value: "mvp", label: "MVP", threshold: 65 },
  { value: "implementation", label: "Implementation", threshold: 70 },
  { value: "testing", label: "Testing", threshold: 70 },
]

export default function ConfidencePage() {
  const [selectedPhase, setSelectedPhase] = useState("implementation")
  const { data, isLoading, isError, refetch } = useConfidence(selectedPhase)
  const mutation = useConfidenceMutation()

  const handleRefresh = () => {
    refetch()
    toast.success("Confidence data refreshed")
  }

  const handlePhaseChange = (phase: string) => {
    setSelectedPhase(phase)
  }

  const currentPhase = phases.find(p => p.value === selectedPhase)
  const confidenceScore = data?.confidence_score ?? 0
  const meetsThreshold = currentPhase ? (confidenceScore * 100) >= currentPhase.threshold : false

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
                <Activity className="h-12 w-12 text-red-500 mx-auto mb-4" />
                <h2 className="text-xl font-bold text-red-500 mb-2">Confidence API Unavailable</h2>
                <p className="text-muted-foreground mb-4">
                  Unable to connect to the Bayesian Confidence API.
                </p>
                <Button onClick={handleRefresh} variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry
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
                <Gauge className="h-8 w-8 text-blue-500" />
                Bayesian Confidence Dashboard
              </h1>
              <p className="text-gray-400 mt-1">
                Phase-aware confidence scoring with Beta-Binomial inference
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Tabs value={selectedPhase} onValueChange={handlePhaseChange}>
                <TabsList>
                  {phases.map(phase => (
                    <TabsTrigger key={phase.value} value={phase.value}>
                      {phase.label}
                    </TabsTrigger>
                  ))}
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

        {/* Summary Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          {isLoading ? (
            [...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-28" />
            ))
          ) : (
            <>
              {/* Confidence Score */}
              <Card className={cn(
                "border",
                meetsThreshold ? "border-green-500/30 bg-green-500/10" : "border-red-500/30 bg-red-500/10"
              )}>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Gauge className={cn(
                      "h-8 w-8",
                      meetsThreshold ? "text-green-400" : "text-red-400"
                    )} />
                    <div>
                      <p className="text-sm text-gray-400">Confidence Score</p>
                      <p className={cn(
                        "text-2xl font-bold",
                        meetsThreshold ? "text-green-400" : "text-red-400"
                      )}>
                        {Math.round(confidenceScore * 100)}%
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Threshold: {currentPhase?.threshold}%
                  </p>
                </CardContent>
              </Card>

              {/* Decision */}
              <Card className={cn(
                "border",
                data?.decision === "GO" ? "border-green-500/30 bg-green-500/10" :
                  data?.decision === "GO_WITH_CHECKPOINTS" ? "border-yellow-500/30 bg-yellow-500/10" :
                    "border-red-500/30 bg-red-500/10"
              )}>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Target className={cn(
                      "h-8 w-8",
                      data?.decision === "GO" ? "text-green-400" :
                        data?.decision === "GO_WITH_CHECKPOINTS" ? "text-yellow-400" : "text-red-400"
                    )} />
                    <div>
                      <p className="text-sm text-gray-400">Decision</p>
                      <p className={cn(
                        "text-xl font-bold",
                        data?.decision === "GO" ? "text-green-400" :
                          data?.decision === "GO_WITH_CHECKPOINTS" ? "text-yellow-400" : "text-red-400"
                      )}>
                        {data?.decision?.replace(/_/g, " ") || "N/A"}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Risk Level */}
              <Card className="border-gray-700">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Shield className={cn(
                      "h-8 w-8",
                      data?.risk_level === "low" ? "text-green-400" :
                        data?.risk_level === "medium" ? "text-yellow-400" :
                          data?.risk_level === "high" ? "text-orange-400" : "text-red-400"
                    )} />
                    <div>
                      <p className="text-sm text-gray-400">Risk Level</p>
                      <p className={cn(
                        "text-xl font-bold capitalize",
                        data?.risk_level === "low" ? "text-green-400" :
                          data?.risk_level === "medium" ? "text-yellow-400" :
                            data?.risk_level === "high" ? "text-orange-400" : "text-red-400"
                      )}>
                        {data?.risk_level || "N/A"}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recommendations */}
              <Card className="border-gray-700">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Zap className="h-8 w-8 text-purple-400" />
                    <div>
                      <p className="text-sm text-gray-400">Actions</p>
                      <p className="text-xl font-bold text-purple-400">
                        {data?.recommendations?.length || 0} Recommended
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </motion.div>

        {/* Phase Thresholds */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-gray-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-400" />
                Phase Confidence Thresholds
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {phases.map((phase) => {
                  const isActive = phase.value === selectedPhase
                  const score = isActive ? confidenceScore * 100 : phase.threshold - 5 + Math.random() * 20
                  const meets = score >= phase.threshold

                  return (
                    <div key={phase.value} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className={cn(
                          "font-medium",
                          isActive ? "text-blue-400" : "text-gray-400"
                        )}>
                          {phase.label} {isActive && "(Current)"}
                        </span>
                        <span className={cn(
                          "font-medium",
                          meets ? "text-green-400" : "text-red-400"
                        )}>
                          {isActive ? Math.round(score) : "-"}% / {phase.threshold}%
                        </span>
                      </div>
                      <div className="h-2 bg-gray-700 rounded-full overflow-hidden relative">
                        {/* Threshold marker */}
                        <div
                          className="absolute h-full w-0.5 bg-white/50 z-10"
                          style={{ left: `${phase.threshold}%` }}
                        />
                        {isActive && (
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${score}%` }}
                            transition={{ duration: 0.5 }}
                            className={cn(
                              "h-full",
                              meets ? "bg-green-500" : "bg-red-500"
                            )}
                          />
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Main Bayesian Component */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          {isLoading ? (
            <Skeleton className="h-[500px]" />
          ) : data ? (
            <BayesianConfidence
              decision={data.decision}
              confidence_score={data.confidence_score}
              state={data.state}
              risk_level={data.risk_level}
              monitoring_level={data.monitoring_level}
              dominant_dimension={data.dominant_dimension}
              recommendations={data.recommendations}
              bayesian_details={data.metadata}
              isLoading={isLoading}
            />
          ) : null}
        </motion.div>
      </div>
    </div>
  )
}

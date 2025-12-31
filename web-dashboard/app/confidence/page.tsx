"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Activity, RefreshCw, Gauge, Target, TrendingUp, Shield, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BayesianConfidence } from "@/components/dashboard/bayesian-confidence"
import { EvidenceInputModal } from "@/components/confidence/EvidenceInputModal"
import { EvidenceBreakdown } from "@/components/confidence/EvidenceBreakdown"
import { ConfidenceTrendChart } from "@/components/confidence/ConfidenceTrendChart"
import { InteractiveRecommendations } from "@/components/confidence/InteractiveRecommendations"
import { useConfidence, useConfidenceMutation } from "@/hooks/useConfidence"
import { useConfidenceWebSocket } from "@/hooks/useConfidenceWebSocket"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { Wifi, WifiOff } from "lucide-react"
import { useTranslations } from "next-intl"

export default function ConfidencePage() {
  const t = useTranslations('confidence')

  const phases = [
    { value: "ideation", label: t('phases.ideation'), threshold: 60 },
    { value: "design", label: t('phases.design'), threshold: 65 },
    { value: "mvp", label: t('phases.mvp'), threshold: 65 },
    { value: "implementation", label: t('phases.implementation'), threshold: 70 },
    { value: "testing", label: t('phases.testing'), threshold: 70 },
  ]
  const [selectedPhase, setSelectedPhase] = useState("implementation")
  const [showEvidenceModal, setShowEvidenceModal] = useState(false)
  const { data, isLoading, isError, refetch } = useConfidence(selectedPhase)
  const mutation = useConfidenceMutation()

  // WebSocket for real-time updates
  const { isConnected, connectionStatus, requestRecalculation } = useConfidenceWebSocket({
    phase: selectedPhase,
    enabled: true,
    onConfidenceUpdate: () => {
      toast.info(t('updatedRealtime'))
    },
    onThresholdCrossed: (update) => {
      if (update.threshold_crossed === 'above') {
        toast.success(`${t('thresholdCrossedAbove')} ${(update.confidence_score * 100).toFixed(1)}%`)
      } else {
        toast.warning(`${t('droppedBelowThreshold')} ${(update.confidence_score * 100).toFixed(1)}%`)
      }
    },
    onDecisionChanged: (update) => {
      toast.info(`${t('decisionChanged')} ${update.decision.replace(/_/g, ' ')}`)
    },
  })

  const handleRefresh = () => {
    refetch()
    toast.success(t('refreshed'))
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
                <h2 className="text-xl font-bold text-red-500 mb-2">{t('apiUnavailable')}</h2>
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
                <Gauge className="h-8 w-8 text-blue-500" />
                {t('title')}
              </h1>
              <p className="text-gray-400 mt-1">
                {t('description')}
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
                onClick={() => setShowEvidenceModal(true)}
                variant="outline"
                className="text-purple-400 border-purple-500/50 hover:bg-purple-500/10"
              >
                <Zap className="h-4 w-4 mr-2" />
                {t('customEvidence')}
              </Button>
              <Button
                onClick={handleRefresh}
                variant="outline"
                size="icon"
                className="text-blue-400 border-blue-500/50 hover:bg-blue-500/10"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
              {/* WebSocket connection status */}
              <div
                className={cn(
                  "flex items-center gap-1.5 px-2 py-1 rounded-full text-xs",
                  isConnected
                    ? "bg-green-500/20 text-green-400"
                    : connectionStatus === 'connecting'
                      ? "bg-yellow-500/20 text-yellow-400"
                      : "bg-red-500/20 text-red-400"
                )}
                title={`WebSocket: ${connectionStatus}`}
              >
                {isConnected ? (
                  <Wifi className="h-3 w-3" />
                ) : (
                  <WifiOff className="h-3 w-3" />
                )}
                <span className="hidden sm:inline">
                  {isConnected ? t('live') : connectionStatus === 'connecting' ? "..." : t('offline')}
                </span>
              </div>
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
                      <p className="text-sm text-gray-400">{t('confidenceScore')}</p>
                      <p className={cn(
                        "text-2xl font-bold",
                        meetsThreshold ? "text-green-400" : "text-red-400"
                      )}>
                        {Math.round(confidenceScore * 100)}%
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {t('threshold')}: {currentPhase?.threshold}%
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
                      <p className="text-sm text-gray-400">{t('decision')}</p>
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
                      <p className="text-sm text-gray-400">{t('riskLevel')}</p>
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
                      <p className="text-sm text-gray-400">{t('actions')}</p>
                      <p className="text-xl font-bold text-purple-400">
                        {data?.recommendations?.length || 0} {t('recommended')}
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
                {t('phaseThresholds')}
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
                          {phase.label} {isActive && `(${t('current')})`}
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

        {/* Evidence Breakdown Chart */}
        {!isLoading && (
          <EvidenceBreakdown
            breakdown={data?.evidence_breakdown}
            evidenceStrength={data?.evidence_strength}
            isLoading={isLoading}
          />
        )}

        {/* Confidence Trend Chart */}
        {!isLoading && (
          <ConfidenceTrendChart
            currentConfidence={confidenceScore}
            currentPhase={selectedPhase}
            phaseThreshold={currentPhase?.threshold || 70}
            isLoading={isLoading}
          />
        )}

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

        {/* Interactive Recommendations */}
        {!isLoading && data?.recommendations && (
          <InteractiveRecommendations
            recommendations={data.recommendations}
            currentPhase={selectedPhase}
            isLoading={isLoading}
          />
        )}

        {/* Evidence Input Modal */}
        <EvidenceInputModal
          open={showEvidenceModal}
          onClose={() => setShowEvidenceModal(false)}
          currentPhase={selectedPhase}
        />
      </div>
    </div>
  )
}

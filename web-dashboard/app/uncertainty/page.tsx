"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { AlertTriangle, RefreshCw, Activity, TrendingUp, Shield, Zap, Wifi, WifiOff } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { UncertaintyMap } from "@/components/dashboard/uncertainty-map"
import { UncertaintyPredictionChart } from "@/components/dashboard/uncertainty-prediction-chart"
import { ContextAnalysisModal } from "@/components/uncertainty/ContextAnalysisModal"
import { useUncertainty } from "@/hooks/useUncertainty"
import { useUncertaintyWebSocket } from "@/lib/hooks/useUncertaintyWebSocket"
import { useWsStatus } from "@/lib/stores/uncertainty-store"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { useTranslations } from "next-intl"

export default function UncertaintyPage() {
  const t = useTranslations('uncertainty')
  const { data: uncertaintyData, isLoading, isError, refetch } = useUncertainty()
  const [isAcking, setIsAcking] = useState(false)
  const [showContextModal, setShowContextModal] = useState(false)

  // WebSocket connection for real-time uncertainty updates
  const [wsEnabled, setWsEnabled] = useState(true)
  const { connect, disconnect, isConnected } = useUncertaintyWebSocket({
    autoConnect: wsEnabled,
  })
  const wsStatus = useWsStatus()

  useEffect(() => {
    // WebSocket is now enabled - /ws/uncertainty endpoint is implemented
  }, [])

  const handleRefresh = () => {
    refetch()
    toast.success(t('refreshed'))
  }

  const handleAcknowledge = async (mitigation: any) => {
    setIsAcking(true)
    try {
      const response = await fetch(`http://localhost:8000/api/uncertainty/ack/${mitigation.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mitigation_id: mitigation.id,
          applied_impact: mitigation.estimated_impact,
          dimension: null, // Will use dominant dimension from backend
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to acknowledge mitigation: ${response.statusText}`)
      }

      const result = await response.json()
      toast.success(`"${mitigation.action}" ${t('mitigationApplied')}`)
      toast.info(`${t('updatedState')}: ${result.updated_state} (${t('confidence')}: ${Math.round(result.confidence_score * 100)}%)`)

      // Refetch to get updated uncertainty data
      await refetch()
    } catch (error) {
      console.error('Acknowledgment error:', error)
      toast.error(t('ackFailed'))
    } finally {
      setIsAcking(false)
    }
  }

  // State configuration for summary cards
  const getStateInfo = (state?: string) => {
    const normalized = (state || "").toLowerCase()
    const configs: Record<string, { color: string; icon: string; bgColor: string }> = {
      deterministic: { color: "text-green-400", icon: "✅", bgColor: "bg-green-500/10 border-green-500/30" },
      probabilistic: { color: "text-blue-400", icon: "📊", bgColor: "bg-blue-500/10 border-blue-500/30" },
      quantum: { color: "text-purple-400", icon: "⚛️", bgColor: "bg-purple-500/10 border-purple-500/30" },
      chaotic: { color: "text-orange-400", icon: "🌪️", bgColor: "bg-orange-500/10 border-orange-500/30" },
      void: { color: "text-red-400", icon: "⚫", bgColor: "bg-red-500/10 border-red-500/30" },
    }
    return configs[normalized] || { color: "text-gray-400", icon: "❓", bgColor: "bg-gray-500/10 border-gray-500/30" }
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
                <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                <h2 className="text-xl font-bold text-red-500 mb-2">{t('unavailable')}</h2>
                <p className="text-muted-foreground mb-4">
                  {t('backendOffline')}
                </p>
                <Button onClick={handleRefresh} variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  {t('retryConnection')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  const stateInfo = getStateInfo(uncertaintyData?.state)
  const confidence = uncertaintyData?.confidence_score ?? 0
  const vector = uncertaintyData?.vector

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
                <AlertTriangle className="h-8 w-8 text-yellow-500" />
                {t('title')}
              </h1>
              <p className="text-gray-400 mt-1">
                {t('description')}
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => setShowContextModal(true)}
                variant="outline"
                className="text-purple-400 border-purple-500/50 hover:bg-purple-500/10"
              >
                <Zap className="h-4 w-4 mr-2" />
                {t('analyzeContext')}
              </Button>
              <Button
                onClick={handleRefresh}
                variant="outline"
                className="text-blue-400 border-blue-500/50 hover:bg-blue-500/10"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                {t('refresh')}
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
              {/* Current State */}
              <Card className={cn("border", stateInfo.bgColor)}>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{stateInfo.icon}</span>
                    <div>
                      <p className="text-sm text-gray-400">{t('currentState')}</p>
                      <p className={cn("text-xl font-bold capitalize", stateInfo.color)}>
                        {uncertaintyData?.state || "Unknown"}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Confidence Score */}
              <Card className="border-gray-700">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Shield className={cn(
                      "h-8 w-8",
                      confidence > 0.7 ? "text-green-400" :
                        confidence > 0.4 ? "text-yellow-400" : "text-red-400"
                    )} />
                    <div>
                      <p className="text-sm text-gray-400">{t('confidence')}</p>
                      <p className={cn(
                        "text-xl font-bold",
                        confidence > 0.7 ? "text-green-400" :
                          confidence > 0.4 ? "text-yellow-400" : "text-red-400"
                      )}>
                        {Math.round(confidence * 100)}%
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Dominant Dimension */}
              <Card className="border-gray-700">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <Activity className="h-8 w-8 text-purple-400" />
                    <div>
                      <p className="text-sm text-gray-400">{t('dominantFactor')}</p>
                      <p className="text-xl font-bold text-purple-400 capitalize">
                        {vector?.dominant_dimension || "N/A"}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Trend */}
              <Card className="border-gray-700">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <TrendingUp className={cn(
                      "h-8 w-8",
                      uncertaintyData?.prediction?.trend === "increasing" ? "text-green-400" :
                        uncertaintyData?.prediction?.trend === "decreasing" ? "text-red-400" : "text-blue-400"
                    )} />
                    <div>
                      <p className="text-sm text-gray-400">{t('trend24h')}</p>
                      <p className={cn(
                        "text-xl font-bold capitalize",
                        uncertaintyData?.prediction?.trend === "increasing" ? "text-green-400" :
                          uncertaintyData?.prediction?.trend === "decreasing" ? "text-red-400" : "text-blue-400"
                      )}>
                        {uncertaintyData?.prediction?.trend || "Unknown"}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </motion.div>

        {/* Vector Breakdown */}
        {!isLoading && vector && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Activity className="h-5 w-5 text-blue-400" />
                  {t('vectorBreakdown')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                  {[
                    { key: "technical", label: t('dimensions.technical'), value: vector.technical },
                    { key: "market", label: t('dimensions.market'), value: vector.market },
                    { key: "resource", label: t('dimensions.resource'), value: vector.resource },
                    { key: "timeline", label: t('dimensions.timeline'), value: vector.timeline },
                    { key: "quality", label: t('dimensions.quality'), value: vector.quality },
                  ].map(({ key, label, value }) => (
                    <div key={key} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">{label}</span>
                        <span className={cn(
                          "font-medium",
                          (value || 0) < 0.3 ? "text-green-400" :
                            (value || 0) < 0.6 ? "text-yellow-400" : "text-red-400"
                        )}>
                          {Math.round((value || 0) * 100)}%
                        </span>
                      </div>
                      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${(value || 0) * 100}%` }}
                          transition={{ duration: 0.5, delay: 0.3 }}
                          className={cn(
                            "h-full",
                            (value || 0) < 0.3 ? "bg-green-500" :
                              (value || 0) < 0.6 ? "bg-yellow-500" : "bg-red-500"
                          )}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t border-gray-700 flex justify-between text-sm">
                  <span className="text-gray-400">{t('totalMagnitude')}</span>
                  <span className={cn(
                    "font-bold",
                    (vector.magnitude || 0) < 0.3 ? "text-green-400" :
                      (vector.magnitude || 0) < 0.6 ? "text-yellow-400" : "text-red-400"
                  )}>
                    {Math.round((vector.magnitude || 0) * 100)}%
                  </span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* 24-Hour Prediction Chart */}
        {!isLoading && uncertaintyData && (
          <UncertaintyPredictionChart
            currentConfidence={uncertaintyData.confidence_score}
            prediction={uncertaintyData.prediction}
            vector={uncertaintyData.vector}
          />
        )}

        {/* Main Uncertainty Map */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          {isLoading ? (
            <Skeleton className="h-[600px]" />
          ) : uncertaintyData ? (
            <UncertaintyMap
              state={uncertaintyData.state}
              confidence={uncertaintyData.confidence_score}
              prediction={uncertaintyData.prediction}
              mitigations={uncertaintyData.mitigations}
              vector={uncertaintyData.vector}
              isLoading={isLoading}
              onAcknowledge={handleAcknowledge}
              isAcking={isAcking}
            />
          ) : null}
        </motion.div>

        {/* Context Analysis Modal */}
        <ContextAnalysisModal
          open={showContextModal}
          onClose={() => setShowContextModal(false)}
        />
      </div>
    </div>
  )
}

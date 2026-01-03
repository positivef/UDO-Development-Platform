"use client"

/**
 * InteractiveRecommendations - Actionable recommendation cards
 *
 * Features:
 * - Priority-sorted recommendation list
 * - Click to apply/acknowledge recommendations
 * - Impact estimation display
 * - Animated transitions on state changes
 * - Local storage persistence for applied actions
 */

import { memo, useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Zap,
  ChevronRight,
  RotateCcw,
  TrendingUp,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface Recommendation {
  action: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  reason: string
  estimated_impact?: number
}

interface InteractiveRecommendationsProps {
  recommendations: Recommendation[]
  currentPhase: string
  isLoading?: boolean
}

const priorityConfig = {
  critical: {
    color: 'text-red-400',
    bg: 'bg-red-500/20 border-red-500/50',
    icon: AlertCircle,
    label: 'Critical',
    order: 0,
  },
  high: {
    color: 'text-orange-400',
    bg: 'bg-orange-500/20 border-orange-500/50',
    icon: Zap,
    label: 'High',
    order: 1,
  },
  medium: {
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/20 border-yellow-500/50',
    icon: Clock,
    label: 'Medium',
    order: 2,
  },
  low: {
    color: 'text-green-400',
    bg: 'bg-green-500/20 border-green-500/50',
    icon: CheckCircle2,
    label: 'Low',
    order: 3,
  },
}

const STORAGE_KEY = 'applied-recommendations'

export const InteractiveRecommendations = memo(function InteractiveRecommendations({
  recommendations,
  currentPhase,
  isLoading = false,
}: InteractiveRecommendationsProps) {
  const [appliedActions, setAppliedActions] = useState<Set<string>>(new Set())
  const [expandedAction, setExpandedAction] = useState<string | null>(null)

  // Load applied actions from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        setAppliedActions(new Set(parsed))
      } catch {
        // Ignore parse errors
      }
    }
  }, [])

  // Save applied actions to localStorage
  const saveAppliedActions = (actions: Set<string>) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...actions]))
  }

  const handleApply = (action: string) => {
    const newApplied = new Set(appliedActions)
    newApplied.add(action)
    setAppliedActions(newApplied)
    saveAppliedActions(newApplied)
  }

  const handleUndo = (action: string) => {
    const newApplied = new Set(appliedActions)
    newApplied.delete(action)
    setAppliedActions(newApplied)
    saveAppliedActions(newApplied)
  }

  const handleResetAll = () => {
    setAppliedActions(new Set())
    localStorage.removeItem(STORAGE_KEY)
  }

  // Sort recommendations by priority
  const sortedRecommendations = [...recommendations].sort(
    (a, b) => priorityConfig[a.priority].order - priorityConfig[b.priority].order
  )

  const appliedCount = recommendations.filter((r) =>
    appliedActions.has(r.action)
  ).length
  const totalCount = recommendations.length

  if (isLoading) {
    return (
      <Card className="border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-400" />
            Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-700 rounded w-1/3"></div>
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (recommendations.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="border-gray-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-400" />
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-gray-400">
              <CheckCircle2 className="h-12 w-12 text-green-400 mb-4" />
              <p className="text-lg font-medium">No Actions Required</p>
              <p className="text-sm text-gray-500">
                Your {currentPhase} phase is on track!
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
    >
      <Card className="border-gray-700">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-400" />
              Recommendations
            </CardTitle>
            <div className="flex items-center gap-3">
              <Badge
                variant="outline"
                className={cn(
                  'text-xs',
                  appliedCount === totalCount
                    ? 'bg-green-500/20 border-green-500/50 text-green-400'
                    : 'bg-gray-500/20 border-gray-500/50 text-gray-400'
                )}
              >
                {appliedCount}/{totalCount} Applied
              </Badge>
              {appliedCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleResetAll}
                  className="text-xs text-gray-400 hover:text-white"
                >
                  <RotateCcw className="h-3 w-3 mr-1" />
                  Reset
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Progress bar */}
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(appliedCount / totalCount) * 100}%` }}
              transition={{ duration: 0.5 }}
              className="h-full bg-green-500"
            />
          </div>

          {/* Recommendations list */}
          <AnimatePresence mode="popLayout">
            {sortedRecommendations.map((rec, index) => {
              const config = priorityConfig[rec.priority]
              const PriorityIcon = config.icon
              const isApplied = appliedActions.has(rec.action)
              const isExpanded = expandedAction === rec.action

              return (
                <motion.div
                  key={rec.action}
                  layout
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.1 }}
                  className={cn(
                    'border rounded-lg p-4 transition-all duration-300',
                    isApplied
                      ? 'bg-green-500/10 border-green-500/30'
                      : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'
                  )}
                >
                  <div
                    className="flex items-start justify-between cursor-pointer"
                    onClick={() =>
                      setExpandedAction(isExpanded ? null : rec.action)
                    }
                  >
                    <div className="flex items-start gap-3 flex-1">
                      <div
                        className={cn(
                          'p-2 rounded-lg',
                          isApplied ? 'bg-green-500/20' : config.bg
                        )}
                      >
                        {isApplied ? (
                          <CheckCircle2 className="h-4 w-4 text-green-400" />
                        ) : (
                          <PriorityIcon
                            className={cn('h-4 w-4', config.color)}
                          />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className={cn(
                              'font-medium',
                              isApplied
                                ? 'text-green-400 line-through'
                                : 'text-white'
                            )}
                          >
                            {rec.action}
                          </span>
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              isApplied
                                ? 'bg-green-500/20 border-green-500/50 text-green-400'
                                : config.bg,
                              isApplied ? '' : config.color
                            )}
                          >
                            {isApplied ? 'Done' : config.label}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-400 line-clamp-1">
                          {rec.reason}
                        </p>
                      </div>
                    </div>
                    <ChevronRight
                      className={cn(
                        'h-5 w-5 text-gray-500 transition-transform',
                        isExpanded && 'rotate-90'
                      )}
                    />
                  </div>

                  {/* Expanded content */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-4 mt-4 border-t border-gray-700 space-y-4">
                          <div>
                            <h4 className="text-xs font-medium text-gray-400 mb-1">
                              Reason
                            </h4>
                            <p className="text-sm text-gray-300">{rec.reason}</p>
                          </div>

                          {rec.estimated_impact && (
                            <div className="flex items-center gap-2">
                              <TrendingUp className="h-4 w-4 text-blue-400" />
                              <span className="text-sm text-gray-400">
                                Estimated Impact:
                              </span>
                              <span className="text-sm font-medium text-blue-400">
                                +{(rec.estimated_impact * 100).toFixed(1)}%
                                confidence
                              </span>
                            </div>
                          )}

                          <div className="flex gap-2">
                            {isApplied ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleUndo(rec.action)
                                }}
                                className="text-yellow-400 border-yellow-500/50 hover:bg-yellow-500/10"
                              >
                                <RotateCcw className="h-3 w-3 mr-1" />
                                Undo
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleApply(rec.action)
                                }}
                                className="bg-green-600 hover:bg-green-700"
                              >
                                <CheckCircle2 className="h-3 w-3 mr-1" />
                                Mark as Applied
                              </Button>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )
            })}
          </AnimatePresence>

          {/* Summary footer */}
          {appliedCount === totalCount && totalCount > 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center justify-center gap-2 p-4 bg-green-500/10 border border-green-500/30 rounded-lg"
            >
              <CheckCircle2 className="h-5 w-5 text-green-400" />
              <span className="text-green-400 font-medium">
                All recommendations applied!
              </span>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
})

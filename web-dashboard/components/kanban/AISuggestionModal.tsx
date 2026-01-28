"use client"

/**
 * AISuggestionModal - AI-powered task suggestion modal
 *
 * Week 6 Day 3: AI Task Suggestion implementation
 * Implements Q2: AI Hybrid (suggest + approve) with Constitutional compliance (P1-P17)
 *
 * Features:
 * - Request AI suggestions with context and phase
 * - Display suggestions with confidence scores
 * - Approve/modify/reject suggestions
 * - Rate limit status display
 * - Constitutional compliance indicators
 */

import { useState, useCallback, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Sparkles,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  Brain,
  Shield,
  ChevronDown,
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  Edit3,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  suggestTasks,
  approveSuggestion,
  getRateLimitStatus,
  getConfidenceColor,
  getConfidenceLabel,
  formatResetTime,
  KanbanAIError,
  RateLimitError,
  type PhaseName,
  type TaskSuggestion,
  type TaskSuggestionResponse,
  type RateLimitStatus,
} from '@/lib/api/kanban-ai'

interface AISuggestionModalProps {
  open: boolean
  onClose: () => void
  onTaskCreated?: (taskId: string) => void
  defaultPhase?: PhaseName
  projectId?: string
}

const PHASES: { value: PhaseName; label: string; description: string }[] = [
  { value: 'ideation', label: '아이디어', description: '브레인스토밍 및 컨셉 탐색' },
  { value: 'design', label: '설계', description: '아키텍처 및 기술 설계' },
  { value: 'mvp', label: 'MVP', description: '최소 기능 제품 개발' },
  { value: 'implementation', label: '구현', description: '전체 기능 구현' },
  { value: 'testing', label: '테스트', description: '품질 보증 및 테스트' },
]

const priorityColors = {
  low: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  medium: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20',
  high: 'bg-orange-500/10 text-orange-600 border-orange-500/20',
  critical: 'bg-red-500/10 text-red-600 border-red-500/20',
}

export function AISuggestionModal({
  open,
  onClose,
  onTaskCreated,
  defaultPhase = 'implementation',
  projectId,
}: AISuggestionModalProps) {
  // Form state
  const [phase, setPhase] = useState<PhaseName>(defaultPhase)
  const [context, setContext] = useState('')
  const [numSuggestions, setNumSuggestions] = useState(3)

  // Response state
  const [suggestions, setSuggestions] = useState<TaskSuggestion[]>([])
  const [response, setResponse] = useState<TaskSuggestionResponse | null>(null)
  const [rateLimit, setRateLimit] = useState<RateLimitStatus | null>(null)

  // UI state
  const [isGenerating, setIsGenerating] = useState(false)
  const [isApproving, setIsApproving] = useState<string | null>(null)
  const [expandedSuggestion, setExpandedSuggestion] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [isLoadingRateLimit, setIsLoadingRateLimit] = useState(false)

  // Fetch rate limit status on open
  useEffect(() => {
    if (open) {
      fetchRateLimitStatus()
    }
  }, [open])

  const fetchRateLimitStatus = async () => {
    setIsLoadingRateLimit(true)
    try {
      const status = await getRateLimitStatus()
      setRateLimit(status)
    } catch (err) {
      console.error('Failed to fetch rate limit:', err)
      // Set default rate limit on error to show fallback UI
      setRateLimit({
        user_id: 'unknown',
        is_limited: false,
        suggestions_used_today: 0,
        suggestions_remaining: 10,
        limit_per_period: 10,
        period_reset_at: new Date(Date.now() + 86400000).toISOString(),
      })
    } finally {
      setIsLoadingRateLimit(false)
    }
  }

  const handleGenerate = async () => {
    if (!context.trim()) {
      setError('AI 제안을 위한 상황 설명을 입력해주세요')
      return
    }

    if (rateLimit?.is_limited) {
      setError(`일일 제한 초과. 초기화: ${formatResetTime(rateLimit.period_reset_at)}`)
      return
    }

    setIsGenerating(true)
    setError(null)
    setSuccessMessage(null)
    setSuggestions([])

    try {
      const result = await suggestTasks({
        project_id: projectId,
        phase_name: phase,
        context: context.trim(),
        num_suggestions: numSuggestions,
        include_dependencies: true,
      })

      setResponse(result)
      setSuggestions(result.suggestions)
      setRateLimit((prev) => prev ? {
        ...prev,
        suggestions_used_today: prev.suggestions_used_today + 1,
        suggestions_remaining: result.remaining_suggestions_today,
        is_limited: result.remaining_suggestions_today <= 0,
      } : null)

      if (result.suggestions.length > 0) {
        setExpandedSuggestion(result.suggestions[0].suggestion_id)
      }
    } catch (err) {
      if (err instanceof RateLimitError) {
        setRateLimit(err.status)
        setError(`일일 제한 초과. 초기화: ${formatResetTime(err.status.period_reset_at)}`)
      } else if (err instanceof KanbanAIError) {
        setError(err.message)
      } else {
        setError('제안 생성에 실패했습니다. 다시 시도해주세요.')
      }
    } finally {
      setIsGenerating(false)
    }
  }

  const handleApprove = async (suggestion: TaskSuggestion) => {
    setIsApproving(suggestion.suggestion_id)
    setError(null)

    try {
      const result = await approveSuggestion(suggestion.suggestion_id, {
        suggestion_id: suggestion.suggestion_id,
        approval_notes: 'Approved from AI Suggestion Modal',
      })

      if (result.success) {
        setSuccessMessage(`"${suggestion.title}" 작업이 생성되었습니다!`)
        // Remove approved suggestion from list
        setSuggestions((prev) => prev.filter((s) => s.suggestion_id !== suggestion.suggestion_id))
        onTaskCreated?.(result.task_id)

        // If no more suggestions, close after delay
        if (suggestions.length <= 1) {
          setTimeout(() => {
            handleClose()
          }, 1500)
        }
      } else {
        setError(result.message || '제안 승인에 실패했습니다')
      }
    } catch (err) {
      if (err instanceof KanbanAIError) {
        setError(err.message)
      } else {
        setError('제안 승인에 실패했습니다. 다시 시도해주세요.')
      }
    } finally {
      setIsApproving(null)
    }
  }

  const handleReject = (suggestionId: string) => {
    setSuggestions((prev) => prev.filter((s) => s.suggestion_id !== suggestionId))
  }

  const handleClose = useCallback(() => {
    setContext('')
    setSuggestions([])
    setResponse(null)
    setError(null)
    setSuccessMessage(null)
    setExpandedSuggestion(null)
    onClose()
  }, [onClose])

  const toggleExpand = (suggestionId: string) => {
    setExpandedSuggestion((prev) => prev === suggestionId ? null : suggestionId)
  }

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && handleClose()}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            AI 작업 제안
            <Badge variant="outline" className="ml-2 bg-purple-500/10 text-purple-600 border-purple-500/20">
              Q2: AI 하이브리드
            </Badge>
          </DialogTitle>
          <DialogDescription>
            Claude AI가 상황에 맞는 작업을 제안합니다. AI가 제안한 작업을 검토하고 승인하거나 수정할 수 있습니다.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col gap-4 py-4">
          {/* Rate Limit Status */}
          {isLoadingRateLimit ? (
            <div className="flex items-center justify-center p-3 rounded-lg text-sm bg-gray-50 dark:bg-gray-900/20 border border-gray-200 dark:border-gray-800">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
                <span className="text-gray-600 dark:text-gray-400">사용량 확인 중...</span>
              </div>
            </div>
          ) : rateLimit ? (
            <div className={cn(
              'flex items-center justify-between p-3 rounded-lg text-sm',
              rateLimit.is_limited
                ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                : 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
            )}>
              <div className="flex items-center gap-2">
                <Clock className={cn('h-4 w-4', rateLimit.is_limited ? 'text-red-500' : 'text-blue-500')} />
                <span>
                  제안 가능: {rateLimit.suggestions_remaining} / {rateLimit.limit_per_period}
                </span>
              </div>
              {rateLimit.is_limited && (
                <span className="text-red-600 dark:text-red-400">
                  초기화: {formatResetTime(rateLimit.period_reset_at)}
                </span>
              )}
            </div>
          ) : null}

          {/* Error/Success Messages */}
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
              <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
              <span className="text-sm text-red-700 dark:text-red-300">{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
              <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
              <span className="text-sm text-green-700 dark:text-green-300">{successMessage}</span>
            </div>
          )}

          {/* Input Form */}
          {suggestions.length === 0 && (
            <div className="space-y-4">
              {/* Phase Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>개발 단계</Label>
                  <Select value={phase} onValueChange={(v) => setPhase(v as PhaseName)}>
                    <SelectTrigger>
                      <SelectValue placeholder="단계 선택" />
                    </SelectTrigger>
                    <SelectContent>
                      {PHASES.map((p) => (
                        <SelectItem key={p.value} value={p.value}>
                          <div className="flex flex-col">
                            <span>{p.label}</span>
                            <span className="text-xs text-muted-foreground">{p.description}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>제안 개수</Label>
                  <Select value={String(numSuggestions)} onValueChange={(v) => setNumSuggestions(Number(v))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[1, 2, 3, 4, 5].map((n) => (
                        <SelectItem key={n} value={String(n)}>
                          {n}개
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Context Input */}
              <div className="space-y-2">
                <Label htmlFor="context" className="flex items-center gap-2">
                  <Brain className="h-4 w-4" />
                  AI에게 알려줄 상황
                </Label>
                <Textarea
                  id="context"
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  placeholder="현재 진행 중인 작업, 어려운 점, 필요한 작업 종류 등을 설명해주세요..."
                  rows={4}
                  disabled={isGenerating}
                />
                <p className="text-xs text-muted-foreground">
                  상세한 상황 설명을 제공하면 더 나은 제안을 받을 수 있습니다. 프로젝트 목표, 현재 상태, 제약사항을 포함해주세요.
                </p>
              </div>

              {/* Generate Button */}
              <Button
                onClick={handleGenerate}
                disabled={isGenerating || !context.trim() || rateLimit?.is_limited}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    제안 생성 중...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    제안 받기
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Suggestions List */}
          {suggestions.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-medium flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-purple-500" />
                  제안 {suggestions.length}개 생성됨
                </h3>
                {response && (
                  <span className="text-xs text-muted-foreground">
                    {response.model_used}로 {response.generation_time_ms}ms에 생성
                  </span>
                )}
              </div>

              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-3">
                  {suggestions.map((suggestion) => {
                    const isExpanded = expandedSuggestion === suggestion.suggestion_id
                    const isApprovingThis = isApproving === suggestion.suggestion_id

                    return (
                      <Card
                        key={suggestion.suggestion_id}
                        className={cn(
                          'p-4 transition-all',
                          isExpanded && 'ring-2 ring-purple-500/50'
                        )}
                      >
                        {/* Header */}
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-medium text-sm truncate">{suggestion.title}</h4>
                              <Badge variant="outline" className={cn('text-xs', priorityColors[suggestion.priority])}>
                                {suggestion.priority}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {suggestion.description}
                            </p>
                          </div>

                          {/* Confidence Badge */}
                          <Badge
                            variant="outline"
                            className={cn('text-xs flex-shrink-0', getConfidenceColor(suggestion.confidence))}
                          >
                            {getConfidenceLabel(suggestion.confidence)}
                          </Badge>
                        </div>

                        {/* Expand/Collapse Button */}
                        <button
                          type="button"
                          onClick={() => toggleExpand(suggestion.suggestion_id)}
                          className="w-full flex items-center justify-center gap-1 mt-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="h-3 w-3" />
                              간략히
                            </>
                          ) : (
                            <>
                              <ChevronDown className="h-3 w-3" />
                              상세히
                            </>
                          )}
                        </button>

                        {/* Expanded Details */}
                        {isExpanded && (
                          <div className="mt-4 pt-4 border-t space-y-4">
                            {/* Reasoning */}
                            <div className="space-y-1">
                              <Label className="text-xs text-muted-foreground">AI 판단 근거</Label>
                              <p className="text-sm bg-muted/50 p-2 rounded">{suggestion.reasoning}</p>
                            </div>

                            {/* Metadata Grid */}
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <Label className="text-xs text-muted-foreground">단계</Label>
                                <p className="capitalize">{suggestion.phase_name}</p>
                              </div>
                              {suggestion.estimated_hours && (
                                <div>
                                  <Label className="text-xs text-muted-foreground">예상 시간</Label>
                                  <p>{suggestion.estimated_hours}시간</p>
                                </div>
                              )}
                            </div>

                            {/* Dependencies */}
                            {suggestion.suggested_dependencies.length > 0 && (
                              <div className="space-y-1">
                                <Label className="text-xs text-muted-foreground">권장 의존 관계</Label>
                                <div className="flex flex-wrap gap-1">
                                  {suggestion.suggested_dependencies.map((dep, i) => (
                                    <Badge key={i} variant="secondary" className="text-xs">
                                      {dep}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Constitutional Compliance */}
                            <div className="space-y-1">
                              <Label className="text-xs text-muted-foreground flex items-center gap-1">
                                <Shield className="h-3 w-3" />
                                헌법 준수 (P1-P17)
                              </Label>
                              <div className="flex flex-wrap gap-1">
                                {Object.entries(suggestion.constitutional_compliance).map(([key, value]) => (
                                  <Badge
                                    key={key}
                                    variant="outline"
                                    className={cn(
                                      'text-xs',
                                      value
                                        ? 'bg-green-500/10 text-green-600 border-green-500/20'
                                        : 'bg-red-500/10 text-red-600 border-red-500/20'
                                    )}
                                  >
                                    {key}: {value ? '✓' : '✗'}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex items-center gap-2 mt-4 pt-4 border-t">
                          <Button
                            size="sm"
                            onClick={() => handleApprove(suggestion)}
                            disabled={isApprovingThis}
                            className="flex-1"
                          >
                            {isApprovingThis ? (
                              <>
                                <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                                생성 중...
                              </>
                            ) : (
                              <>
                                <ThumbsUp className="mr-2 h-3 w-3" />
                                승인하고 생성
                              </>
                            )}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleReject(suggestion.suggestion_id)}
                            disabled={isApprovingThis}
                          >
                            <ThumbsDown className="mr-2 h-3 w-3" />
                            거부
                          </Button>
                        </div>
                      </Card>
                    )
                  })}
                </div>
              </ScrollArea>

              {/* Back to Input Button */}
              <Button
                variant="outline"
                onClick={() => setSuggestions([])}
                className="w-full"
              >
                <Edit3 className="mr-2 h-4 w-4" />
                새 제안 받기
              </Button>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            <X className="mr-2 h-4 w-4" />
            닫기
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

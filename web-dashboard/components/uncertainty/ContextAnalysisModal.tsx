"use client"

/**
 * ContextAnalysisModal - Custom context analysis modal
 *
 * Features:
 * - Custom project context input form
 * - Phase, team size, timeline, validation score inputs
 * - Real-time uncertainty prediction
 * - Results display with mitigation strategies
 */

import { useState, useEffect } from 'react'
import { useUncertaintyStore } from '@/lib/stores/uncertainty-store'
import type { ContextAnalysisRequest } from '@/lib/api/uncertainty'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import {
  Zap,
  AlertCircle,
  CheckCircle,
  Users,
  Calendar,
  Code,
  Target,
} from 'lucide-react'

interface ContextAnalysisModalProps {
  open: boolean
  onClose: () => void
}

const PHASES = [
  { value: 'ideation', label: 'Ideation' },
  { value: 'design', label: 'Design' },
  { value: 'mvp', label: 'MVP' },
  { value: 'implementation', label: 'Implementation' },
  { value: 'testing', label: 'Testing' },
] as const

export function ContextAnalysisModal({ open, onClose }: ContextAnalysisModalProps) {
  const { analyzeCustomContext, isLoading, error, clearError, uncertaintyData } = useUncertaintyStore()

  // Form state
  const [phase, setPhase] = useState<string>('implementation')
  const [hasCode, setHasCode] = useState(true)
  const [validationScore, setValidationScore] = useState<number>(0.7)
  const [teamSize, setTeamSize] = useState<number>(5)
  const [timelineWeeks, setTimelineWeeks] = useState<number>(8)

  // UI state
  const [showResults, setShowResults] = useState(false)

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setShowResults(false)
      clearError()
    }
  }, [open, clearError])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()

    const context: ContextAnalysisRequest = {
      phase: phase as any,
      has_code: hasCode,
      validation_score: validationScore,
      team_size: teamSize,
      timeline_weeks: timelineWeeks,
    }

    await analyzeCustomContext(context)
    setShowResults(true)
  }

  const handleClose = () => {
    setShowResults(false)
    clearError()
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            Custom Context Analysis
          </DialogTitle>
          <DialogDescription>
            Provide project context to predict uncertainty and receive tailored mitigation strategies
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Phase Selection */}
          <div className="space-y-2">
            <Label htmlFor="phase" className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              Development Phase
            </Label>
            <Select value={phase} onValueChange={setPhase}>
              <SelectTrigger id="phase">
                <SelectValue placeholder="Select phase" />
              </SelectTrigger>
              <SelectContent>
                {PHASES.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Has Code Toggle */}
          <div className="flex items-center justify-between">
            <Label htmlFor="has-code" className="flex items-center gap-2 cursor-pointer">
              <Code className="h-4 w-4" />
              Code Available
            </Label>
            <Switch
              id="has-code"
              checked={hasCode}
              onCheckedChange={setHasCode}
            />
          </div>

          {/* Validation Score Slider */}
          <div className="space-y-2">
            <Label htmlFor="validation-score" className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Validation Score: {validationScore.toFixed(2)}
            </Label>
            <Slider
              id="validation-score"
              min={0}
              max={1}
              step={0.05}
              value={[validationScore]}
              onValueChange={(values) => setValidationScore(values[0])}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              0.0 = No validation, 1.0 = Fully validated
            </p>
          </div>

          {/* Team Size */}
          <div className="space-y-2">
            <Label htmlFor="team-size" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Team Size
            </Label>
            <Input
              id="team-size"
              type="number"
              min={1}
              value={teamSize}
              onChange={(e) => setTeamSize(parseInt(e.target.value) || 1)}
              className="w-full"
            />
          </div>

          {/* Timeline Weeks */}
          <div className="space-y-2">
            <Label htmlFor="timeline-weeks" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Timeline (Weeks)
            </Label>
            <Input
              id="timeline-weeks"
              type="number"
              min={1}
              value={timelineWeeks}
              onChange={(e) => setTimelineWeeks(parseInt(e.target.value) || 1)}
              className="w-full"
            />
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error.message}</AlertDescription>
            </Alert>
          )}

          {/* Results Summary */}
          {showResults && uncertaintyData && !isLoading && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-semibold">Analysis Complete</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>State: <span className="font-mono">{uncertaintyData.state}</span></div>
                    <div>Confidence: <span className="font-mono">{(uncertaintyData.confidence_score * 100).toFixed(1)}%</span></div>
                    <div>Mitigations: <span className="font-mono">{uncertaintyData.mitigations.length}</span></div>
                    <div>Trend: <span className="font-mono">{uncertaintyData.prediction.trend}</span></div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Close this modal to view detailed results on the main dashboard.
                  </p>
                </div>
              </AlertDescription>
            </Alert>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Zap className="mr-2 h-4 w-4" />
                  Analyze Context
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

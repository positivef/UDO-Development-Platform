"use client"

/**
 * EvidenceInputModal - Custom confidence evidence input
 *
 * Features:
 * - Test metrics: passing rate, code coverage
 * - Review metrics: approval count
 * - Dependency health score
 * - Historical outcomes editor
 * - Real-time confidence calculation
 */

import { useState, useEffect } from 'react'
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
  CheckCircle,
  AlertCircle,
  Target,
  Code,
  GitBranch,
  Users,
  Calendar,
  Activity,
} from 'lucide-react'
import { useConfidenceMutation } from '@/hooks/useConfidence'

interface EvidenceInputModalProps {
  open: boolean
  onClose: () => void
  currentPhase: string
}

const PHASES = [
  { value: 'ideation', label: 'Ideation' },
  { value: 'design', label: 'Design' },
  { value: 'mvp', label: 'MVP' },
  { value: 'implementation', label: 'Implementation' },
  { value: 'testing', label: 'Testing' },
] as const

export function EvidenceInputModal({ open, onClose, currentPhase }: EvidenceInputModalProps) {
  const { mutateAsync, isPending, isError, error } = useConfidenceMutation()

  // Phase context
  const [phase, setPhase] = useState<string>(currentPhase)
  const [hasCode, setHasCode] = useState(true)
  const [validationScore, setValidationScore] = useState<number>(0.7)
  const [teamSize, setTeamSize] = useState<number>(3)
  const [timelineWeeks, setTimelineWeeks] = useState<number>(8)

  // Evidence metrics
  const [testPassingRate, setTestPassingRate] = useState<number>(0.85)
  const [codeCoverage, setCodeCoverage] = useState<number>(0.75)
  const [reviewApprovalCount, setReviewApprovalCount] = useState<number>(5)
  const [dependencyHealthScore, setDependencyHealthScore] = useState<number>(0.8)

  // Historical outcomes
  const [historicalOutcomes, setHistoricalOutcomes] = useState<boolean[]>([
    true, true, false, true, true
  ])

  // UI state
  const [showResults, setShowResults] = useState(false)
  const [result, setResult] = useState<any>(null)

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setPhase(currentPhase)
      setShowResults(false)
      setResult(null)
    }
  }, [open, currentPhase])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const request = {
      phase,
      context: {
        phase,
        has_code: hasCode,
        validation_score: validationScore,
        team_size: teamSize,
        timeline_weeks: timelineWeeks,
      },
      evidence: {
        test_passing_rate: testPassingRate,
        code_coverage: codeCoverage,
        review_approval_count: reviewApprovalCount,
        dependency_health_score: dependencyHealthScore,
      },
      historical_outcomes: historicalOutcomes,
      use_fast_mode: false // Use accurate mode for custom evidence
    }

    try {
      const data = await mutateAsync(request as any)
      setResult(data)
      setShowResults(true)
    } catch (err) {
      console.error('Failed to calculate confidence:', err)
    }
  }

  const handleClose = () => {
    setShowResults(false)
    setResult(null)
    onClose()
  }

  const toggleHistoricalOutcome = (index: number) => {
    const newOutcomes = [...historicalOutcomes]
    newOutcomes[index] = !newOutcomes[index]
    setHistoricalOutcomes(newOutcomes)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Custom Confidence Evidence
          </DialogTitle>
          <DialogDescription>
            Provide project metrics to calculate Bayesian confidence with real evidence
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

          {/* Project Context */}
          <div className="grid grid-cols-2 gap-4">
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
              />
            </div>

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
              />
            </div>

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
              />
            </div>
          </div>

          {/* Evidence Metrics */}
          <div className="space-y-4 pt-4 border-t">
            <h3 className="text-sm font-semibold text-gray-300">Evidence Metrics</h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-400" />
                  Test Passing Rate: {(testPassingRate * 100).toFixed(0)}%
                </Label>
                <Slider
                  min={0}
                  max={1}
                  step={0.01}
                  value={[testPassingRate]}
                  onValueChange={(values) => setTestPassingRate(values[0])}
                />
                <p className="text-xs text-muted-foreground">
                  Percentage of tests passing (0-100%)
                </p>
              </div>

              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Code className="h-4 w-4 text-blue-400" />
                  Code Coverage: {(codeCoverage * 100).toFixed(0)}%
                </Label>
                <Slider
                  min={0}
                  max={1}
                  step={0.01}
                  value={[codeCoverage]}
                  onValueChange={(values) => setCodeCoverage(values[0])}
                />
                <p className="text-xs text-muted-foreground">
                  Percentage of code covered by tests (0-100%)
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="review-count" className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-purple-400" />
                  Review Approvals: {reviewApprovalCount}
                </Label>
                <Input
                  id="review-count"
                  type="number"
                  min={0}
                  value={reviewApprovalCount}
                  onChange={(e) => setReviewApprovalCount(parseInt(e.target.value) || 0)}
                />
                <p className="text-xs text-muted-foreground">
                  Number of code review approvals
                </p>
              </div>

              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-yellow-400" />
                  Dependency Health: {(dependencyHealthScore * 100).toFixed(0)}%
                </Label>
                <Slider
                  min={0}
                  max={1}
                  step={0.01}
                  value={[dependencyHealthScore]}
                  onValueChange={(values) => setDependencyHealthScore(values[0])}
                />
                <p className="text-xs text-muted-foreground">
                  Overall health of project dependencies (0-100%)
                </p>
              </div>
            </div>
          </div>

          {/* Historical Outcomes */}
          <div className="space-y-3 pt-4 border-t">
            <Label className="text-sm font-semibold text-gray-300">
              Historical Outcomes (Last 5 Iterations)
            </Label>
            <div className="flex gap-2">
              {historicalOutcomes.map((outcome, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => toggleHistoricalOutcome(idx)}
                  className={`flex-1 p-3 rounded-lg border-2 transition-colors ${
                    outcome
                      ? 'bg-green-500/20 border-green-500/50 text-green-400'
                      : 'bg-red-500/20 border-red-500/50 text-red-400'
                  }`}
                >
                  {outcome ? '✓ Success' : '✗ Failure'}
                </button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              Click to toggle success/failure for each iteration
            </p>
          </div>

          {/* Error Display */}
          {isError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {error?.message || 'Failed to calculate confidence'}
              </AlertDescription>
            </Alert>
          )}

          {/* Results Summary */}
          {showResults && result && !isPending && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-semibold">Analysis Complete</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>Confidence: <span className="font-mono">{(result.confidence_score * 100).toFixed(1)}%</span></div>
                    <div>Decision: <span className="font-mono">{result.decision}</span></div>
                    <div>Risk Level: <span className="font-mono">{result.risk_level}</span></div>
                    <div>Actions: <span className="font-mono">{result.recommendations.length}</span></div>
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
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isPending}
            >
              {isPending ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
                  Calculating...
                </>
              ) : (
                <>
                  <Activity className="mr-2 h-4 w-4" />
                  Calculate Confidence
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

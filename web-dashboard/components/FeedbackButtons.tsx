/**
 * FeedbackButtons Component - Knowledge Reuse Feedback
 *
 * Week 6 Day 4: Knowledge Reuse Accuracy Tracking
 *
 * Benchmarking:
 * - Notion AI: 👍/👎 simple feedback
 * - Linear: Helpful/Not helpful with reason
 * - GitHub Copilot: Implicit accept/reject
 *
 * Features:
 * - Explicit feedback (👍/👎 buttons)
 * - Optional reason input
 * - Thank you message after submission
 * - Tracks both explicit and implicit signals
 */

"use client"

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ThumbsUp, ThumbsDown, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FeedbackButtonsProps {
  documentId: string
  searchQuery: string
  sessionId?: string
  onFeedbackSubmit?: (isHelpful: boolean) => void
  className?: string
}

interface FeedbackPayload {
  document_id: string
  search_query: string
  is_helpful: boolean
  reason?: string
  session_id?: string
  implicit_accept?: boolean
}

// Mock API client (replace with real backend)
const feedbackAPI = {
  submitFeedback: async (payload: FeedbackPayload): Promise<void> => {
    // POST /api/knowledge/feedback
    console.log('Submitting feedback:', payload)
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500))
    return Promise.resolve()
  },
}

export function FeedbackButtons({
  documentId,
  searchQuery,
  sessionId,
  onFeedbackSubmit,
  className,
}: FeedbackButtonsProps) {
  const queryClient = useQueryClient()
  const [feedbackGiven, setFeedbackGiven] = useState(false)
  const [showReasonDialog, setShowReasonDialog] = useState(false)
  const [selectedFeedback, setSelectedFeedback] = useState<boolean | null>(null)
  const [reason, setReason] = useState('')

  // Submit feedback mutation
  const feedbackMutation = useMutation({
    mutationFn: feedbackAPI.submitFeedback,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-metrics'] })
      setFeedbackGiven(true)
      setShowReasonDialog(false)
      setReason('')

      // Auto-hide thank you message after 3 seconds
      setTimeout(() => {
        setFeedbackGiven(false)
      }, 3000)
    },
  })

  const handleFeedback = (isHelpful: boolean) => {
    setSelectedFeedback(isHelpful)

    // If not helpful, ask for reason (optional)
    if (!isHelpful) {
      setShowReasonDialog(true)
    } else {
      // Helpful feedback submitted immediately
      submitFeedback(isHelpful)
    }
  }

  const submitFeedback = (isHelpful: boolean, optionalReason?: string) => {
    feedbackMutation.mutate({
      document_id: documentId,
      search_query: searchQuery,
      is_helpful: isHelpful,
      reason: optionalReason || reason || undefined,
      session_id: sessionId,
    })

    // Notify parent component
    onFeedbackSubmit?.(isHelpful)
  }

  const handleSubmitReason = () => {
    if (selectedFeedback !== null) {
      submitFeedback(selectedFeedback, reason)
    }
  }

  const handleSkipReason = () => {
    if (selectedFeedback !== null) {
      submitFeedback(selectedFeedback)
    }
  }

  // Already gave feedback - show thank you
  if (feedbackGiven) {
    return (
      <div className={cn("flex items-center gap-2 text-sm text-green-600", className)}>
        <CheckCircle2 className="h-4 w-4" />
        <span>Thank you for your feedback!</span>
      </div>
    )
  }

  return (
    <>
      <div className={cn("flex items-center gap-2", className)}>
        <span className="text-sm text-muted-foreground">Was this helpful?</span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleFeedback(true)}
          disabled={feedbackMutation.isPending}
          className="gap-1"
        >
          <ThumbsUp className="h-4 w-4" />
          <span className="hidden sm:inline">Yes</span>
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleFeedback(false)}
          disabled={feedbackMutation.isPending}
          className="gap-1"
        >
          <ThumbsDown className="h-4 w-4" />
          <span className="hidden sm:inline">No</span>
        </Button>
      </div>

      {/* Reason Dialog (for negative feedback) */}
      <Dialog open={showReasonDialog} onOpenChange={setShowReasonDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Help us improve</DialogTitle>
            <DialogDescription>
              What went wrong? (Optional - helps us improve search quality)
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <Textarea
              placeholder="e.g., The solution didn't work for my setup, Outdated information, Wrong topic..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              className="resize-none"
            />

            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                onClick={handleSkipReason}
                disabled={feedbackMutation.isPending}
              >
                Skip
              </Button>
              <Button
                onClick={handleSubmitReason}
                disabled={feedbackMutation.isPending}
              >
                {feedbackMutation.isPending ? 'Submitting...' : 'Submit'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}

/**
 * Implicit Feedback Tracker
 *
 * Usage: Track implicit signals (copy, dismiss, session duration)
 *
 * Example:
 * ```tsx
 * useImplicitFeedback({
 *   documentId: 'doc-123',
 *   searchQuery: 'auth 401',
 *   onCopy: () => trackImplicitAccept(),
 *   onDismiss: () => trackImplicitReject(),
 * })
 * ```
 */
export function useImplicitFeedback(options: {
  documentId: string
  searchQuery: string
  sessionId?: string
}) {
  const trackImplicitAccept = () => {
    // User copied the solution → Implicit accept
    feedbackAPI.submitFeedback({
      document_id: options.documentId,
      search_query: options.searchQuery,
      is_helpful: true,
      session_id: options.sessionId,
      implicit_accept: true,
    })
  }

  const trackImplicitReject = () => {
    // User dismissed without using → Implicit reject
    feedbackAPI.submitFeedback({
      document_id: options.documentId,
      search_query: options.searchQuery,
      is_helpful: false,
      session_id: options.sessionId,
      implicit_accept: false,
    })
  }

  return {
    trackImplicitAccept,
    trackImplicitReject,
  }
}

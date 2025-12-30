"use client"

/**
 * TaskCard - Individual task card component for Kanban Board
 *
 * Features:
 * - Draggable with @dnd-kit
 * - Priority color coding
 * - Tags display
 * - Click to view details
 * - React.memo for performance optimization
 * - Dependencies/Blocked indicator (Q7: Hard Block)
 *
 * Week 6 Day 2: Added Dependencies visualization
 */

import { memo, useMemo, useRef, useCallback, useEffect } from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import type { KanbanTask } from '@/lib/types/kanban'
import { AlertCircle, Clock, Layers, Link2, AlertTriangle, Calendar, MessageSquare } from 'lucide-react'
import { cn } from '@/lib/utils'

// Due date helpers
const isDueSoon = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  return diffDays <= 3 && diffDays >= 0
}

const isOverdue = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  return date < now
}

const formatDueDateShort = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
}

interface TaskCardProps {
  task: KanbanTask
  onClick?: () => void
  onDoubleClick?: () => void  // Q4: Double-click for context auto-load
}

const priorityColors = {
  low: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  medium: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20',
  high: 'bg-orange-500/10 text-orange-600 border-orange-500/20',
  critical: 'bg-red-500/10 text-red-600 border-red-500/20',
}

const priorityBorderColors = {
  low: 'border-l-blue-500',
  medium: 'border-l-yellow-500',
  high: 'border-l-orange-500',
  critical: 'border-l-red-500',
}

function TaskCardComponent({ task, onClick, onDoubleClick }: TaskCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id })

  // Q4: Click delay to distinguish single vs double click
  const clickTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const CLICK_DELAY = 250 // ms to wait before registering single click

  const handleClick = useCallback(() => {
    // Clear any existing timeout
    if (clickTimeoutRef.current) {
      clearTimeout(clickTimeoutRef.current)
    }
    // Set a delayed single-click handler
    clickTimeoutRef.current = setTimeout(() => {
      onClick?.()
    }, CLICK_DELAY)
  }, [onClick])

  const handleDoubleClick = useCallback(() => {
    // Cancel the pending single-click
    if (clickTimeoutRef.current) {
      clearTimeout(clickTimeoutRef.current)
      clickTimeoutRef.current = null
    }
    // Execute double-click handler
    onDoubleClick?.()
  }, [onDoubleClick])

  // Keyboard accessibility: Enter for detail, Ctrl+C for context
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.ctrlKey) {
      e.preventDefault()
      onClick?.()
    } else if ((e.key === 'c' || e.key === 'C') && e.ctrlKey) {
      e.preventDefault()
      onDoubleClick?.()
    }
  }, [onClick, onDoubleClick])

  // Cleanup timeout on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      if (clickTimeoutRef.current) {
        clearTimeout(clickTimeoutRef.current)
      }
    }
  }, [])

  // Memoize style object to prevent unnecessary re-renders
  const style = useMemo(() => ({
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }), [transform, transition, isDragging])

  // Memoize visible tags to prevent unnecessary recalculation
  const visibleTags = useMemo(
    () => task.tags?.slice(0, 3) || [],
    [task.tags]
  )
  const remainingTagsCount = useMemo(
    () => (task.tags?.length || 0) - 3,
    [task.tags]
  )

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label={`${task.title}. 클릭하면 상세보기, 더블클릭 또는 Ctrl+C로 컨텍스트 열기`}
      className="cursor-pointer task-card"
      data-testid="task-card"
    >
      <Card
        className={cn(
          'p-4 border-l-4 hover:shadow-md transition-shadow',
          priorityBorderColors[task.priority]
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-medium text-sm flex-1">{task.title}</h3>
          <Badge
            variant="outline"
            className={cn('text-xs ml-2', priorityColors[task.priority])}
          >
            {task.priority}
          </Badge>
        </div>

        {/* Description */}
        {task.description && (
          <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
            {task.description}
          </p>
        )}

        {/* Tags */}
        {visibleTags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {visibleTags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
            {remainingTagsCount > 0 && (
              <Badge variant="secondary" className="text-xs">
                +{remainingTagsCount}
              </Badge>
            )}
          </div>
        )}

        {/* Dependencies/Blocked indicator (Q7) */}
        {(task.blocked_by && task.blocked_by.length > 0) && (
          <div className="flex items-center gap-1 mb-2 text-xs text-red-500 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">
            <AlertTriangle className="h-3 w-3 flex-shrink-0" />
            <span className="truncate">
              Blocked by {task.blocked_by.length} task{task.blocked_by.length > 1 ? 's' : ''}
            </span>
          </div>
        )}

        {/* Dependencies indicator */}
        {(task.dependencies && task.dependencies.length > 0) && (
          <div className="flex items-center gap-1 mb-2 text-xs text-blue-500 bg-blue-50 dark:bg-blue-900/20 px-2 py-1 rounded">
            <Link2 className="h-3 w-3 flex-shrink-0" />
            <span className="truncate">
              Depends on {task.dependencies.length} task{task.dependencies.length > 1 ? 's' : ''}
            </span>
          </div>
        )}

        {/* Footer metadata */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
          {/* Phase */}
          <div className="flex items-center gap-1">
            <Layers className="h-3 w-3" />
            <span className="capitalize">{task.phase}</span>
          </div>

          {/* Due date (Week 6 Day 4) */}
          {task.due_date && (
            <div
              className={cn(
                'flex items-center gap-1',
                isOverdue(task.due_date) && 'text-red-500',
                isDueSoon(task.due_date) && !isOverdue(task.due_date) && 'text-yellow-600'
              )}
            >
              <Calendar className="h-3 w-3" />
              <span>{formatDueDateShort(task.due_date)}</span>
              {isOverdue(task.due_date) && (
                <AlertTriangle className="h-3 w-3" />
              )}
            </div>
          )}

          {/* Estimated hours */}
          {task.estimated_hours && (
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{task.estimated_hours}h</span>
            </div>
          )}

          {/* Comments count (Week 6 Day 4) */}
          {task.comments && task.comments.length > 0 && (
            <div className="flex items-center gap-1">
              <MessageSquare className="h-3 w-3" />
              <span>{task.comments.length}</span>
            </div>
          )}

          {/* Blocked status indicator */}
          {task.status === 'blocked' && (
            <div className="flex items-center gap-1 text-red-500">
              <AlertCircle className="h-3 w-3" />
              <span>Blocked</span>
            </div>
          )}

          {/* AI suggested indicator */}
          {task.ai_suggested && (
            <Badge variant="outline" className="text-xs bg-purple-500/10 text-purple-600 border-purple-500/20">
              AI
            </Badge>
          )}
        </div>
      </Card>
    </div>
  )
}

// Memoize component to prevent unnecessary re-renders
export const TaskCard = memo(TaskCardComponent)

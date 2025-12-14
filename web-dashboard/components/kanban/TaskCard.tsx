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
 */

import { memo, useMemo } from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import type { KanbanTask } from '@/lib/types/kanban'
import { AlertCircle, Clock, Layers } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TaskCardProps {
  task: KanbanTask
  onClick?: () => void
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

function TaskCardComponent({ task, onClick }: TaskCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id })

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
      onClick={onClick}
      className="cursor-pointer"
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

        {/* Footer metadata */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {/* Phase */}
          <div className="flex items-center gap-1">
            <Layers className="h-3 w-3" />
            <span className="capitalize">{task.phase}</span>
          </div>

          {/* Estimated hours */}
          {task.estimated_hours && (
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{task.estimated_hours}h</span>
            </div>
          )}

          {/* Blocked indicator */}
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

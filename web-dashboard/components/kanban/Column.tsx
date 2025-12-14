"use client"

/**
 * Column - Kanban column component for grouping tasks by status
 *
 * Features:
 * - Droppable area for @dnd-kit
 * - Task count display
 * - Scrollable task list
 * - Status-based color coding
 */

import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TaskCard } from './TaskCard'
import type { KanbanColumn, KanbanTask } from '@/lib/types/kanban'
import { cn } from '@/lib/utils'

interface ColumnProps {
  column: KanbanColumn
  onTaskClick?: (task: KanbanTask) => void
}

const columnColors = {
  pending: 'border-t-blue-500 bg-blue-50/5',
  in_progress: 'border-t-yellow-500 bg-yellow-50/5',
  blocked: 'border-t-red-500 bg-red-50/5',
  completed: 'border-t-green-500 bg-green-50/5',
}

const columnBadgeColors = {
  pending: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  in_progress: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20',
  blocked: 'bg-red-500/10 text-red-600 border-red-500/20',
  completed: 'bg-green-500/10 text-green-600 border-green-500/20',
}

export function Column({ column, onTaskClick }: ColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: column.id,
  })

  const taskIds = column.tasks.map((task) => task.id)

  return (
    <div className="flex-1 min-w-[300px]">
      <Card
        className={cn(
          'border-t-4 h-full flex flex-col',
          columnColors[column.id],
          isOver && 'bg-primary/5'
        )}
      >
        {/* Column Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-lg">{column.title}</h2>
            <Badge
              variant="outline"
              className={cn('text-sm', columnBadgeColors[column.id])}
            >
              {column.tasks.length}
            </Badge>
          </div>
        </div>

        {/* Droppable Task List */}
        <div
          ref={setNodeRef}
          className="flex-1 p-4 space-y-3 overflow-y-auto min-h-[200px]"
        >
          <SortableContext items={taskIds} strategy={verticalListSortingStrategy}>
            {column.tasks.length === 0 ? (
              <div className="text-center text-muted-foreground text-sm py-8">
                No tasks
              </div>
            ) : (
              column.tasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onClick={() => onTaskClick?.(task)}
                />
              ))
            )}
          </SortableContext>
        </div>
      </Card>
    </div>
  )
}

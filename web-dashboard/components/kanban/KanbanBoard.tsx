"use client"

/**
 * KanbanBoard - Main Kanban Board component with drag & drop
 *
 * Features:
 * - Drag & drop with @dnd-kit
 * - Optimistic updates with rollback on error
 * - Task detail modal
 * - Real-time synchronization with Zustand store
 * - Backend API integration
 */

import { useState, useCallback, useMemo } from 'react'
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import { Column } from './Column'
import { TaskCard } from './TaskCard'
import { TaskDetailModal } from './TaskDetailModal'
import { ContextBriefing } from './ContextBriefing'
import { useKanbanStore, useColumns } from '@/lib/stores/kanban-store'
import { kanbanAPI } from '@/lib/api/kanban'
import type { KanbanTask, TaskStatus, KanbanColumn } from '@/lib/types/kanban'

interface KanbanBoardProps {
  /** Optional filtered tasks. If provided, columns will be computed from these tasks instead of store */
  tasks?: KanbanTask[]
  /** WebSocket broadcast functions for real-time updates */
  onBroadcastTaskMoved?: (taskId: string, oldStatus: TaskStatus, newStatus: TaskStatus) => void
  onBroadcastTaskUpdated?: (taskId: string, updates: Partial<KanbanTask>) => void
  onBroadcastTaskDeleted?: (taskId: string) => void
  onBroadcastTaskArchived?: (taskId: string) => void
}

// Column definitions (same as store)
const columnDefinitions: { id: TaskStatus; title: string }[] = [
  { id: 'pending', title: 'To Do' },
  { id: 'in_progress', title: 'In Progress' },
  { id: 'blocked', title: 'Blocked' },
  { id: 'completed', title: 'Done' },
]

export function KanbanBoard({
  tasks: filteredTasks,
  onBroadcastTaskMoved,
  onBroadcastTaskUpdated,
  onBroadcastTaskDeleted,
  onBroadcastTaskArchived,
}: KanbanBoardProps = {}) {
  const storeColumns = useColumns()
  const { moveTask, selectedTask, setSelectedTask, updateTask: updateTaskInStore } = useKanbanStore()

  // Compute columns from filtered tasks if provided, otherwise use store columns
  const columns = useMemo((): KanbanColumn[] => {
    if (!filteredTasks) {
      return storeColumns
    }
    // Build columns from filtered tasks
    return columnDefinitions.map((col) => ({
      id: col.id,
      title: col.title,
      tasks: filteredTasks.filter((task) => task.status === col.id),
    }))
  }, [filteredTasks, storeColumns])
  const [activeTask, setActiveTask] = useState<KanbanTask | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  // Q4: Context Briefing state for double-click auto-load
  const [isContextBriefingOpen, setIsContextBriefingOpen] = useState(false)
  const [contextBriefingTask, setContextBriefingTask] = useState<KanbanTask | null>(null)

  // Configure drag sensors (memoized to prevent re-creation)
  const pointerSensorConfig = useMemo(() => ({
    activationConstraint: {
      distance: 8, // 8px movement before drag starts
    },
  }), [])

  const keyboardSensorConfig = useMemo(() => ({
    coordinateGetter: sortableKeyboardCoordinates,
  }), [])

  const sensors = useSensors(
    useSensor(PointerSensor, pointerSensorConfig),
    useSensor(KeyboardSensor, keyboardSensorConfig)
  )

  // Memoize all tasks for efficient lookup
  const allTasks = useMemo(() =>
    columns.flatMap((col) => col.tasks),
    [columns]
  )

  const handleDragStart = useCallback((event: any) => {
    const { active } = event
    // Find the task being dragged
    const task = allTasks.find((task) => task.id === active.id)
    setActiveTask(task || null)
  }, [allTasks])

  const handleDragEnd = useCallback(async (event: DragEndEvent) => {
    const { active, over } = event
    setActiveTask(null)

    if (!over || isUpdating) return

    const taskId = active.id as string
    const newStatus = over.id as TaskStatus

    // Find the original task to preserve state for rollback
    const originalTask = allTasks.find((task) => task.id === taskId)

    if (!originalTask || originalTask.status === newStatus) return

    const previousStatus = originalTask.status

    // Optimistic update (immediate UI feedback)
    moveTask(taskId, newStatus)

    setIsUpdating(true)

    try {
      // Persist to backend with rollback on error
      const updatedTask = await kanbanAPI.updateTaskStatus(taskId, newStatus)

      // Update store with server response (for timestamp, etc.)
      updateTaskInStore(taskId, updatedTask)

      // Broadcast to other users via WebSocket (Stage 2)
      if (onBroadcastTaskMoved) {
        onBroadcastTaskMoved(taskId, previousStatus, newStatus)
      }

      console.log(`✅ Task ${taskId} moved to ${newStatus}`)
    } catch (error) {
      console.error('Failed to update task status:', error)

      // Rollback optimistic update
      moveTask(taskId, previousStatus)

      // Show error to user (TODO: Replace with toast notification in Week 3)
      alert(
        `Failed to move task: ${
          error instanceof Error ? error.message : 'Unknown error'
        }\n\nThe change has been reverted.`
      )
    } finally {
      setIsUpdating(false)
    }
  }, [allTasks, isUpdating, moveTask, updateTaskInStore, onBroadcastTaskMoved])

  const handleTaskClick = useCallback((task: KanbanTask) => {
    setSelectedTask(task)
    setIsModalOpen(true)
  }, [setSelectedTask])

  const handleModalClose = useCallback(() => {
    setIsModalOpen(false)
    setSelectedTask(null)
  }, [setSelectedTask])

  // Q4: Double-click handler for Context Briefing
  const handleTaskDoubleClick = useCallback((task: KanbanTask) => {
    setContextBriefingTask(task)
    setIsContextBriefingOpen(true)
  }, [])

  const handleContextBriefingClose = useCallback(() => {
    setIsContextBriefingOpen(false)
    setContextBriefingTask(null)
  }, [])

  return (
    <>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 h-full overflow-x-auto pb-4">
          {columns.map((column) => (
            <Column
              key={column.id}
              column={column}
              onTaskClick={handleTaskClick}
              onTaskDoubleClick={handleTaskDoubleClick}
            />
          ))}
        </div>

        {/* Drag Overlay */}
        <DragOverlay>
          {activeTask ? (
            <div className="opacity-80 rotate-3">
              <TaskCard task={activeTask} />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* Task Detail Modal */}
      <TaskDetailModal
        task={selectedTask}
        open={isModalOpen}
        onClose={handleModalClose}
        onBroadcastTaskUpdated={onBroadcastTaskUpdated}
        onBroadcastTaskDeleted={onBroadcastTaskDeleted}
        onBroadcastTaskArchived={onBroadcastTaskArchived}
      />

      {/* Q4: Context Briefing Modal (double-click auto-load) */}
      {contextBriefingTask && (
        <ContextBriefing
          taskId={contextBriefingTask.id}
          taskTitle={contextBriefingTask.title}
          isOpen={isContextBriefingOpen}
          onClose={handleContextBriefingClose}
        />
      )}
    </>
  )
}

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

import { useState, useEffect } from 'react'
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
import { useKanbanStore, useColumns } from '@/lib/stores/kanban-store'
import { kanbanAPI } from '@/lib/api/kanban'
import type { KanbanTask, TaskStatus } from '@/lib/types/kanban'

export function KanbanBoard() {
  const columns = useColumns()
  const { moveTask, selectedTask, setSelectedTask, updateTask: updateTaskInStore } = useKanbanStore()
  const [activeTask, setActiveTask] = useState<KanbanTask | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Configure drag sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement before drag starts
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragStart = (event: any) => {
    const { active } = event
    // Find the task being dragged
    const task = columns
      .flatMap((col) => col.tasks)
      .find((task) => task.id === active.id)
    setActiveTask(task || null)
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event
    setActiveTask(null)

    if (!over || isUpdating) return

    const taskId = active.id as string
    const newStatus = over.id as TaskStatus

    // Find the original task to preserve state for rollback
    const originalTask = columns
      .flatMap((col) => col.tasks)
      .find((task) => task.id === taskId)

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
  }

  const handleTaskClick = (task: KanbanTask) => {
    setSelectedTask(task)
    setIsModalOpen(true)
  }

  const handleModalClose = () => {
    setIsModalOpen(false)
    setSelectedTask(null)
  }

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
      />
    </>
  )
}

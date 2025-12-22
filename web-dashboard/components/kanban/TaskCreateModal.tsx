"use client"

/**
 * TaskCreateModal - Create new task modal
 *
 * Features:
 * - Form validation (title, description, phase required)
 * - Phase, priority, status selection
 * - Tags input
 * - Time estimation
 * - Context notes
 * - Dependencies selection (Q7: Hard Block support)
 * - API integration with useCreateTask hook
 *
 * Week 6 Day 2: Added Dependencies UI
 */

import { useState, useCallback } from 'react'
import { useCreateTask } from '@/hooks/useKanban'
import type { Phase, Priority, TaskStatus, KanbanTask } from '@/lib/types/kanban'
import type { CreateTaskRequest } from '@/lib/api/kanban'
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
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Plus,
  X,
  Loader2,
  AlertCircle,
  Link2,
  Calendar,
} from 'lucide-react'
import { TaskDependencySelect } from './TaskDependencySelect'

interface TaskCreateModalProps {
  open: boolean
  onClose: () => void
  onSuccess?: () => void
  defaultPhase?: Phase
  defaultStatus?: TaskStatus
  /** Available tasks for dependency selection */
  availableTasks?: KanbanTask[]
  /** WebSocket broadcast function for real-time updates */
  onBroadcastTaskCreated?: (task: KanbanTask) => void
}

interface FormData {
  title: string
  description: string
  phase: Phase
  priority: Priority
  status: TaskStatus
  tags: string
  estimated_hours: string
  due_date: string  // Week 6 Day 4: Due date support
  context_notes: string
  dependencies: string[]  // Q7: Task IDs this task depends on
}

interface FormErrors {
  title?: string
  description?: string
  phase?: string
}

const PHASES: { value: Phase; label: string }[] = [
  { value: 'ideation', label: 'Ideation' },
  { value: 'design', label: 'Design' },
  { value: 'mvp', label: 'MVP' },
  { value: 'implementation', label: 'Implementation' },
  { value: 'testing', label: 'Testing' },
]

const PRIORITIES: { value: Priority; label: string; color: string }[] = [
  { value: 'low', label: 'Low', color: 'text-blue-600' },
  { value: 'medium', label: 'Medium', color: 'text-yellow-600' },
  { value: 'high', label: 'High', color: 'text-orange-600' },
  { value: 'critical', label: 'Critical', color: 'text-red-600' },
]

const STATUSES: { value: TaskStatus; label: string }[] = [
  { value: 'pending', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'blocked', label: 'Blocked' },
  { value: 'completed', label: 'Done' },
]

const initialFormData: FormData = {
  title: '',
  description: '',
  phase: 'implementation',
  priority: 'medium',
  status: 'pending',
  tags: '',
  estimated_hours: '',
  due_date: '',
  context_notes: '',
  dependencies: [],
}

export function TaskCreateModal({
  open,
  onClose,
  onSuccess,
  defaultPhase,
  defaultStatus,
  availableTasks = [],
  onBroadcastTaskCreated,
}: TaskCreateModalProps) {
  const createTaskMutation = useCreateTask()

  const [formData, setFormData] = useState<FormData>({
    ...initialFormData,
    phase: defaultPhase || initialFormData.phase,
    status: defaultStatus || initialFormData.status,
  })
  const [errors, setErrors] = useState<FormErrors>({})

  // Reset form when modal opens
  const handleOpenChange = useCallback((isOpen: boolean) => {
    if (!isOpen) {
      onClose()
    } else {
      setFormData({
        ...initialFormData,
        phase: defaultPhase || initialFormData.phase,
        status: defaultStatus || initialFormData.status,
      })
      setErrors({})
    }
  }, [onClose, defaultPhase, defaultStatus])

  // Form validation
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required'
    } else if (formData.title.length < 3) {
      newErrors.title = 'Title must be at least 3 characters'
    } else if (formData.title.length > 200) {
      newErrors.title = 'Title must be less than 200 characters'
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required'
    } else if (formData.description.length < 10) {
      newErrors.description = 'Description must be at least 10 characters'
    }

    if (!formData.phase) {
      newErrors.phase = 'Phase is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Handle form submission
  const handleSubmit = async () => {
    if (!validateForm()) return

    const taskData: CreateTaskRequest = {
      title: formData.title.trim(),
      description: formData.description.trim(),
      phase: formData.phase,
      priority: formData.priority,
      status: formData.status,
      tags: formData.tags
        .split(',')
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0),
      estimated_hours: formData.estimated_hours
        ? parseFloat(formData.estimated_hours)
        : undefined,
      // Week 6 Day 4: Due date
      due_date: formData.due_date
        ? new Date(formData.due_date).toISOString()
        : undefined,
      context_notes: formData.context_notes.trim() || undefined,
      // Q7: Hard Block dependencies
      dependencies: formData.dependencies.length > 0 ? formData.dependencies : undefined,
    }

    try {
      const createdTask = await createTaskMutation.mutateAsync(taskData)
      console.log('✅ Task created successfully')

      // Broadcast to other users via WebSocket (Week 7)
      if (onBroadcastTaskCreated) {
        onBroadcastTaskCreated(createdTask)
      }

      // Reset form and close
      setFormData({
        ...initialFormData,
        phase: defaultPhase || initialFormData.phase,
        status: defaultStatus || initialFormData.status,
      })
      setErrors({})

      onSuccess?.()
      onClose()
    } catch (error) {
      console.error('Failed to create task:', error)
      // Error is handled by the mutation
    }
  }

  // Handle input changes
  const handleChange = (
    field: keyof FormData,
    value: string
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Clear error when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }))
    }
  }

  const isSubmitting = createTaskMutation.isPending

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Create New Task
          </DialogTitle>
          <DialogDescription>
            Add a new task to the Kanban board. All fields marked with * are required.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Error Alert */}
          {createTaskMutation.isError && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <span className="text-sm text-red-700">
                Failed to create task:{' '}
                {createTaskMutation.error instanceof Error
                  ? createTaskMutation.error.message
                  : 'Unknown error'}
              </span>
            </div>
          )}

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title" className="flex items-center gap-1">
              Title <span className="text-red-500">*</span>
            </Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => handleChange('title', e.target.value)}
              placeholder="Enter task title"
              className={errors.title ? 'border-red-500' : ''}
              disabled={isSubmitting}
            />
            {errors.title && (
              <p className="text-sm text-red-500">{errors.title}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className="flex items-center gap-1">
              Description <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Describe the task in detail..."
              rows={4}
              className={errors.description ? 'border-red-500' : ''}
              disabled={isSubmitting}
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description}</p>
            )}
          </div>

          {/* Phase, Priority, Status - Grid */}
          <div className="grid grid-cols-3 gap-4">
            {/* Phase */}
            <div className="space-y-2">
              <Label className="flex items-center gap-1">
                Phase <span className="text-red-500">*</span>
              </Label>
              <Select
                value={formData.phase}
                onValueChange={(value) => handleChange('phase', value)}
                disabled={isSubmitting}
              >
                <SelectTrigger className={errors.phase ? 'border-red-500' : ''}>
                  <SelectValue placeholder="Select phase" />
                </SelectTrigger>
                <SelectContent>
                  {PHASES.map((phase) => (
                    <SelectItem key={phase.value} value={phase.value}>
                      {phase.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.phase && (
                <p className="text-sm text-red-500">{errors.phase}</p>
              )}
            </div>

            {/* Priority */}
            <div className="space-y-2">
              <Label>Priority</Label>
              <Select
                value={formData.priority}
                onValueChange={(value) => handleChange('priority', value)}
                disabled={isSubmitting}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent>
                  {PRIORITIES.map((priority) => (
                    <SelectItem
                      key={priority.value}
                      value={priority.value}
                      className={priority.color}
                    >
                      {priority.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Status */}
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={formData.status}
                onValueChange={(value) => handleChange('status', value)}
                disabled={isSubmitting}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  {STATUSES.map((status) => (
                    <SelectItem key={status.value} value={status.value}>
                      {status.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label htmlFor="tags">Tags</Label>
            <Input
              id="tags"
              value={formData.tags}
              onChange={(e) => handleChange('tags', e.target.value)}
              placeholder="frontend, api, bug (comma separated)"
              disabled={isSubmitting}
            />
            <p className="text-xs text-muted-foreground">
              Separate tags with commas
            </p>
          </div>

          {/* Estimated Hours and Due Date - Grid */}
          <div className="grid grid-cols-2 gap-4">
            {/* Estimated Hours */}
            <div className="space-y-2">
              <Label htmlFor="estimated_hours">Estimated Hours</Label>
              <Input
                id="estimated_hours"
                type="number"
                min="0"
                step="0.5"
                value={formData.estimated_hours}
                onChange={(e) => handleChange('estimated_hours', e.target.value)}
                placeholder="e.g., 4"
                disabled={isSubmitting}
              />
            </div>

            {/* Due Date (Week 6 Day 4) */}
            <div className="space-y-2">
              <Label htmlFor="due_date" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Due Date
              </Label>
              <Input
                id="due_date"
                type="date"
                value={formData.due_date}
                onChange={(e) => handleChange('due_date', e.target.value)}
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Dependencies (Q7: Hard Block) */}
          {availableTasks.length > 0 && (
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Link2 className="h-4 w-4" />
                Dependencies
              </Label>
              <TaskDependencySelect
                availableTasks={availableTasks}
                selectedTaskIds={formData.dependencies}
                onSelectionChange={(taskIds) =>
                  setFormData((prev) => ({ ...prev, dependencies: taskIds }))
                }
                placeholder="Select tasks this depends on..."
                disabled={isSubmitting}
              />
              <p className="text-xs text-muted-foreground">
                Q7: Selected tasks must be completed before this task can start
              </p>
            </div>
          )}

          {/* Context Notes */}
          <div className="space-y-2">
            <Label htmlFor="context_notes">Context Notes</Label>
            <Textarea
              id="context_notes"
              value={formData.context_notes}
              onChange={(e) => handleChange('context_notes', e.target.value)}
              placeholder="Additional context or notes..."
              rows={3}
              disabled={isSubmitting}
            />
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isSubmitting}
          >
            <X className="mr-2 h-4 w-4" />
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Plus className="mr-2 h-4 w-4" />
                Create Task
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

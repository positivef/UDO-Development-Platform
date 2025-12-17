"use client"

/**
 * TaskDetailModal - Task detail view and editing modal
 *
 * Features:
 * - View task details
 * - Inline editing
 * - Time tracking
 * - Dependencies display
 * - Context notes
 * - Delete/Archive actions
 */

import { useState, useEffect } from 'react'
import { useKanbanStore } from '@/lib/stores/kanban-store'
import { kanbanAPI } from '@/lib/api/kanban'
import type { KanbanTask, TaskStatus, Priority, Phase } from '@/lib/types/kanban'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  X,
  Save,
  Trash2,
  Archive,
  Clock,
  Tag,
  FileText,
  AlertCircle,
} from 'lucide-react'
import { ContextManager } from './ContextManager'

interface TaskDetailModalProps {
  task: KanbanTask | null
  open: boolean
  onClose: () => void
}

export function TaskDetailModal({ task, open, onClose }: TaskDetailModalProps) {
  const { updateTask: updateTaskInStore, deleteTask } = useKanbanStore()
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  // Form state
  const [formData, setFormData] = useState<Partial<KanbanTask>>({})

  // Initialize form when task changes
  useEffect(() => {
    if (task) {
      setFormData(task)
      setIsEditing(false)
    }
  }, [task])

  if (!task) return null

  const handleSave = async () => {
    if (!task.id || isSaving) return

    setIsSaving(true)

    try {
      // Extract only updatable fields
      const updates = {
        title: formData.title,
        description: formData.description,
        priority: formData.priority,
        tags: formData.tags,
        estimated_hours: formData.estimated_hours,
        actual_hours: formData.actual_hours,
        context_notes: formData.context_notes,
      }

      const updatedTask = await kanbanAPI.updateTask(task.id, updates)
      updateTaskInStore(task.id, updatedTask)

      setIsEditing(false)
      console.log(`✅ Task ${task.id} updated successfully`)
    } catch (error) {
      console.error('Failed to update task:', error)
      alert(
        `Failed to save changes: ${
          error instanceof Error ? error.message : 'Unknown error'
        }`
      )
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!task.id || isDeleting) return

    const confirmed = confirm(
      `Are you sure you want to delete "${task.title}"?\n\nThis action cannot be undone.`
    )

    if (!confirmed) return

    setIsDeleting(true)

    try {
      await kanbanAPI.deleteTask(task.id)
      deleteTask(task.id)
      onClose()
      console.log(`✅ Task ${task.id} deleted successfully`)
    } catch (error) {
      console.error('Failed to delete task:', error)
      alert(
        `Failed to delete task: ${
          error instanceof Error ? error.message : 'Unknown error'
        }`
      )
    } finally {
      setIsDeleting(false)
    }
  }

  const handleCancel = () => {
    setFormData(task)
    setIsEditing(false)
  }

  const getPriorityColor = (priority: Priority) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200'
    }
  }

  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800 border-gray-200'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'blocked':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200'
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            {isEditing ? (
              <Input
                value={formData.title || ''}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                className="text-2xl font-bold"
                placeholder="Task title"
              />
            ) : (
              <span>{task.title}</span>
            )}
            <div className="flex gap-2">
              <Badge className={getPriorityColor(task.priority)}>
                {task.priority.toUpperCase()}
              </Badge>
              <Badge className={getStatusColor(task.status)}>
                {task.status.replace('_', ' ').toUpperCase()}
              </Badge>
            </div>
          </DialogTitle>
          <DialogDescription className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-1">
              <FileText className="h-4 w-4" />
              {task.phase}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              Created: {new Date(task.created_at).toLocaleDateString()}
            </span>
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="details" className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="context">Context</TabsTrigger>
          </TabsList>

          <TabsContent value="details" className="space-y-6 py-4">
          {/* Description */}
          <div>
            <Label>Description</Label>
            {isEditing ? (
              <Textarea
                value={formData.description || ''}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Task description..."
                rows={4}
                className="mt-2"
              />
            ) : (
              <p className="mt-2 text-muted-foreground">{task.description}</p>
            )}
          </div>

          {/* Tags */}
          <div>
            <Label className="flex items-center gap-2">
              <Tag className="h-4 w-4" />
              Tags
            </Label>
            <div className="mt-2 flex flex-wrap gap-2">
              {isEditing ? (
                <Input
                  value={formData.tags?.join(', ') || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      tags: e.target.value.split(',').map((t) => t.trim()),
                    })
                  }
                  placeholder="tag1, tag2, tag3"
                  className="flex-1"
                />
              ) : task.tags && task.tags.length > 0 ? (
                task.tags.map((tag) => (
                  <Badge key={tag} variant="outline">
                    {tag}
                  </Badge>
                ))
              ) : (
                <span className="text-sm text-muted-foreground">No tags</span>
              )}
            </div>
          </div>

          {/* Time Tracking */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Estimated Hours</Label>
              {isEditing ? (
                <Input
                  type="number"
                  value={formData.estimated_hours || 0}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      estimated_hours: parseFloat(e.target.value),
                    })
                  }
                  className="mt-2"
                />
              ) : (
                <p className="mt-2">{task.estimated_hours || 0}h</p>
              )}
            </div>
            <div>
              <Label>Actual Hours</Label>
              {isEditing ? (
                <Input
                  type="number"
                  value={formData.actual_hours || 0}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      actual_hours: parseFloat(e.target.value),
                    })
                  }
                  className="mt-2"
                />
              ) : (
                <p className="mt-2">{task.actual_hours || 0}h</p>
              )}
            </div>
          </div>

          {/* Dependencies (Read-only for now) */}
          {task.dependencies && task.dependencies.length > 0 && (
            <div>
              <Label className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Dependencies
              </Label>
              <div className="mt-2 space-y-1">
                {task.dependencies.map((dep) => (
                  <Badge key={dep} variant="secondary">
                    {dep}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Blocked By (Read-only) */}
          {task.blocked_by && task.blocked_by.length > 0 && (
            <div>
              <Label className="flex items-center gap-2 text-red-600">
                <AlertCircle className="h-4 w-4" />
                Blocked By
              </Label>
              <div className="mt-2 space-y-1">
                {task.blocked_by.map((blocker) => (
                  <Badge key={blocker} variant="destructive">
                    {blocker}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Context Notes */}
          <div>
            <Label>Context Notes</Label>
            {isEditing ? (
              <Textarea
                value={formData.context_notes || ''}
                onChange={(e) =>
                  setFormData({ ...formData, context_notes: e.target.value })
                }
                placeholder="Additional context or notes..."
                rows={3}
                className="mt-2"
              />
            ) : (
              <p className="mt-2 text-sm text-muted-foreground">
                {task.context_notes || 'No context notes'}
              </p>
            )}
          </div>

          {/* AI Metadata (if available) */}
          {task.ai_suggested && (
            <div className="rounded-lg border border-purple-200 bg-purple-50 p-4">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-semibold text-purple-800">
                  AI Suggested
                </span>
                {task.ai_confidence && (
                  <Badge variant="secondary">
                    {Math.round(task.ai_confidence * 100)}% confidence
                  </Badge>
                )}
              </div>
            </div>
          )}
          </TabsContent>

          <TabsContent value="context" className="py-4">
            <ContextManager taskId={task.id} />
          </TabsContent>
        </Tabs>

        <DialogFooter className="gap-2">
          {isEditing ? (
            <>
              <Button variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? (
                  <>
                    <Clock className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Save
                  </>
                )}
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <>
                    <Clock className="mr-2 h-4 w-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </>
                )}
              </Button>
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                Edit
              </Button>
              <Button onClick={onClose}>Close</Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

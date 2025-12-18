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

import { useState, useEffect, useCallback } from 'react'
import { useKanbanStore } from '@/lib/stores/kanban-store'
import { kanbanAPI } from '@/lib/api/kanban'
import type { KanbanTask, TaskStatus, Priority, Phase, TaskComment } from '@/lib/types/kanban'
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
  Calendar,
  MessageSquare,
  Send,
  User,
  AlertTriangle,
} from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ContextManager } from './ContextManager'
import dynamic from 'next/dynamic'

// Dynamic import for DependencyGraph (D3.js) - reduces initial bundle by ~343KB
const DependencyGraph = dynamic(
  () => import('./DependencyGraph').then((mod) => mod.DependencyGraph),
  {
    loading: () => (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    ),
    ssr: false, // D3.js requires window object
  }
)

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

  // Comments state
  const [newComment, setNewComment] = useState('')
  const [isAddingComment, setIsAddingComment] = useState(false)

  // Initialize form when task changes
  useEffect(() => {
    if (task) {
      setFormData(task)
      setIsEditing(false)
      setNewComment('')
    }
  }, [task])

  // Add comment handler
  const handleAddComment = useCallback(async () => {
    if (!newComment.trim() || !task?.id || isAddingComment) return

    setIsAddingComment(true)

    try {
      const comment: TaskComment = {
        id: `comment-${Date.now()}`,
        author: 'Current User', // TODO: Replace with actual user
        content: newComment.trim(),
        created_at: new Date().toISOString(),
      }

      const updatedComments = [...(formData.comments || []), comment]

      // Update task with new comment
      const updatedTask = await kanbanAPI.updateTask(task.id, {
        comments: updatedComments,
      })

      updateTaskInStore(task.id, { ...updatedTask, comments: updatedComments })
      setFormData((prev) => ({ ...prev, comments: updatedComments }))
      setNewComment('')
      console.log(`✅ Comment added to task ${task.id}`)
    } catch (error) {
      console.error('Failed to add comment:', error)
      // Fallback: Update local state only
      const comment: TaskComment = {
        id: `comment-${Date.now()}`,
        author: 'Current User',
        content: newComment.trim(),
        created_at: new Date().toISOString(),
      }
      const updatedComments = [...(formData.comments || []), comment]
      setFormData((prev) => ({ ...prev, comments: updatedComments }))
      setNewComment('')
    } finally {
      setIsAddingComment(false)
    }
  }, [newComment, task?.id, isAddingComment, formData.comments, updateTaskInStore])

  // Due date helpers
  const formatDueDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

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
        due_date: formData.due_date,
        comments: formData.comments,
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
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="comments" className="flex items-center gap-1">
              <MessageSquare className="h-3 w-3" />
              Comments
              {(formData.comments?.length || 0) > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs px-1.5 py-0">
                  {formData.comments?.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="dependencies" className="flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              Dependencies
              {((formData.dependencies?.length || 0) + (formData.blocked_by?.length || 0)) > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs px-1.5 py-0">
                  {(formData.dependencies?.length || 0) + (formData.blocked_by?.length || 0)}
                </Badge>
              )}
            </TabsTrigger>
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

          {/* Due Date (Week 6 Day 4) */}
          <div>
            <Label className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Due Date
            </Label>
            {isEditing ? (
              <Input
                type="date"
                value={formData.due_date ? formData.due_date.split('T')[0] : ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    due_date: e.target.value ? new Date(e.target.value).toISOString() : undefined,
                  })
                }
                className="mt-2 w-[200px]"
              />
            ) : formData.due_date ? (
              <div className="mt-2 flex items-center gap-2">
                <span
                  className={
                    isOverdue(formData.due_date)
                      ? 'text-red-600 font-medium'
                      : isDueSoon(formData.due_date)
                      ? 'text-yellow-600 font-medium'
                      : ''
                  }
                >
                  {formatDueDate(formData.due_date)}
                </span>
                {isOverdue(formData.due_date) && (
                  <Badge variant="destructive" className="text-xs">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    Overdue
                  </Badge>
                )}
                {isDueSoon(formData.due_date) && !isOverdue(formData.due_date) && (
                  <Badge variant="outline" className="text-xs bg-yellow-500/10 text-yellow-600 border-yellow-500/20">
                    <Clock className="h-3 w-3 mr-1" />
                    Due Soon
                  </Badge>
                )}
              </div>
            ) : (
              <p className="mt-2 text-sm text-muted-foreground">No due date set</p>
            )}
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

          {/* Comments Tab (Week 6 Day 4) */}
          <TabsContent value="comments" className="py-4">
            <div className="space-y-4">
              {/* Add Comment Form */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Add Comment
                </Label>
                <div className="flex gap-2">
                  <Textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Write a comment..."
                    rows={2}
                    className="flex-1"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                        handleAddComment()
                      }
                    }}
                  />
                  <Button
                    onClick={handleAddComment}
                    disabled={!newComment.trim() || isAddingComment}
                    className="self-end"
                  >
                    {isAddingComment ? (
                      <Clock className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Press Ctrl+Enter (Cmd+Enter on Mac) to send
                </p>
              </div>

              {/* Comments List */}
              <div className="space-y-2">
                <Label>
                  {(formData.comments?.length || 0) > 0
                    ? `${formData.comments?.length} Comment${(formData.comments?.length || 0) > 1 ? 's' : ''}`
                    : 'No comments yet'}
                </Label>
                {(formData.comments?.length || 0) > 0 && (
                  <ScrollArea className="h-[250px]">
                    <div className="space-y-3 pr-4">
                      {[...(formData.comments || [])].reverse().map((comment) => (
                        <div
                          key={comment.id}
                          className="rounded-lg border bg-muted/30 p-3 space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center">
                                <User className="h-3 w-3 text-primary" />
                              </div>
                              <span className="text-sm font-medium">{comment.author}</span>
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {new Date(comment.created_at).toLocaleDateString('ko-KR', {
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </span>
                          </div>
                          <p className="text-sm whitespace-pre-wrap">{comment.content}</p>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="dependencies" className="py-4">
            <DependencyGraph
              tasks={useKanbanStore.getState().tasks || []}
              currentTaskId={task.id}
              onTaskClick={(taskId) => {
                // Find and select the clicked task
                const clickedTask = useKanbanStore.getState().tasks?.find(t => t.id === taskId)
                if (clickedTask) {
                  useKanbanStore.getState().setSelectedTask(clickedTask)
                }
              }}
              onEmergencyOverride={(taskId, dependencyId) => {
                // Q7: Emergency override implementation
                console.log(`Emergency override: Task ${taskId} unblocked from ${dependencyId}`)
                // TODO: Call API to remove dependency
                // await kanbanAPI.removeDependency(taskId, dependencyId)
              }}
            />
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

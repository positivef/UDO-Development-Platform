"use client"

/**
 * TaskDependencySelect - Multi-select component for task dependencies
 *
 * Week 6 Day 2: Dependencies UI implementation
 * Features:
 * - Search/filter tasks by title
 * - Multi-select with checkboxes
 * - Visual indicator for selected dependencies
 * - Q7: Hard Block dependency support
 */

import { useState, useCallback, useMemo } from 'react'
import { Check, ChevronsUpDown, X, Link2, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import type { KanbanTask } from '@/lib/types/kanban'

interface TaskDependencySelectProps {
  /** All available tasks to select from */
  availableTasks: KanbanTask[]
  /** Currently selected task IDs */
  selectedTaskIds: string[]
  /** Callback when selection changes */
  onSelectionChange: (taskIds: string[]) => void
  /** Current task ID (to exclude from selection) */
  excludeTaskId?: string
  /** Placeholder text */
  placeholder?: string
  /** Disabled state */
  disabled?: boolean
  /** Maximum number of selections */
  maxSelections?: number
}

const priorityColors = {
  low: 'bg-blue-500/10 text-blue-600',
  medium: 'bg-yellow-500/10 text-yellow-600',
  high: 'bg-orange-500/10 text-orange-600',
  critical: 'bg-red-500/10 text-red-600',
}

export function TaskDependencySelect({
  availableTasks,
  selectedTaskIds,
  onSelectionChange,
  excludeTaskId,
  placeholder = 'Select dependencies...',
  disabled = false,
  maxSelections,
}: TaskDependencySelectProps) {
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // Filter out the current task and apply search filter
  const filteredTasks = useMemo(() => {
    return availableTasks.filter((task) => {
      // Exclude current task
      if (excludeTaskId && task.id === excludeTaskId) return false
      // Apply search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        return (
          task.title.toLowerCase().includes(query) ||
          task.description.toLowerCase().includes(query) ||
          task.tags.some(tag => tag.toLowerCase().includes(query))
        )
      }
      return true
    })
  }, [availableTasks, excludeTaskId, searchQuery])

  // Get selected tasks info
  const selectedTasks = useMemo(() => {
    return availableTasks.filter(task => selectedTaskIds.includes(task.id))
  }, [availableTasks, selectedTaskIds])

  // Toggle task selection
  const toggleTask = useCallback((taskId: string) => {
    if (selectedTaskIds.includes(taskId)) {
      onSelectionChange(selectedTaskIds.filter(id => id !== taskId))
    } else {
      // Check max selections
      if (maxSelections && selectedTaskIds.length >= maxSelections) {
        return
      }
      onSelectionChange([...selectedTaskIds, taskId])
    }
  }, [selectedTaskIds, onSelectionChange, maxSelections])

  // Remove a selected task
  const removeTask = useCallback((taskId: string) => {
    onSelectionChange(selectedTaskIds.filter(id => id !== taskId))
  }, [selectedTaskIds, onSelectionChange])

  // Clear all selections
  const clearAll = useCallback(() => {
    onSelectionChange([])
  }, [onSelectionChange])

  return (
    <div className="space-y-2">
      {/* Selected tasks badges */}
      {selectedTasks.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedTasks.map((task) => (
            <Badge
              key={task.id}
              variant="secondary"
              className="flex items-center gap-1 pr-1"
            >
              <Link2 className="h-3 w-3" />
              <span className="max-w-[150px] truncate">{task.title}</span>
              <button
                type="button"
                onClick={() => removeTask(task.id)}
                className="ml-1 rounded-full hover:bg-muted p-0.5"
                disabled={disabled}
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          {selectedTasks.length > 1 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAll}
              disabled={disabled}
              className="h-6 px-2 text-xs"
            >
              Clear all
            </Button>
          )}
        </div>
      )}

      {/* Popover trigger */}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between"
            disabled={disabled}
          >
            <span className="text-muted-foreground">
              {selectedTaskIds.length > 0
                ? `${selectedTaskIds.length} task${selectedTaskIds.length > 1 ? 's' : ''} selected`
                : placeholder}
            </span>
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[400px] p-0" align="start">
          {/* Search input */}
          <div className="p-3 border-b">
            <Input
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-8"
            />
          </div>

          {/* Task list */}
          <ScrollArea className="h-[300px]">
            {filteredTasks.length === 0 ? (
              <div className="p-4 text-center text-sm text-muted-foreground">
                {searchQuery ? 'No tasks found.' : 'No tasks available.'}
              </div>
            ) : (
              <div className="p-2">
                {filteredTasks.map((task) => {
                  const isSelected = selectedTaskIds.includes(task.id)
                  const isBlocked = task.status === 'blocked'
                  const isDisabled = disabled || (!isSelected && !!maxSelections && selectedTaskIds.length >= maxSelections)

                  return (
                    <div
                      key={task.id}
                      className={cn(
                        'flex items-start gap-3 p-2 rounded-md cursor-pointer hover:bg-muted transition-colors',
                        isSelected && 'bg-muted',
                        isDisabled && !isSelected && 'opacity-50 cursor-not-allowed'
                      )}
                      onClick={() => !isDisabled && toggleTask(task.id)}
                    >
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => !isDisabled && toggleTask(task.id)}
                        disabled={Boolean(isDisabled && !isSelected)}
                        className="mt-1"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm truncate">
                            {task.title}
                          </span>
                          {isBlocked && (
                            <AlertTriangle className="h-3 w-3 text-red-500 flex-shrink-0" />
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge
                            variant="outline"
                            className={cn('text-xs', priorityColors[task.priority])}
                          >
                            {task.priority}
                          </Badge>
                          <span className="text-xs text-muted-foreground capitalize">
                            {task.phase}
                          </span>
                          <span className="text-xs text-muted-foreground capitalize">
                            {task.status.replace('_', ' ')}
                          </span>
                        </div>
                        {task.description && (
                          <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
                            {task.description}
                          </p>
                        )}
                      </div>
                      {isSelected && (
                        <Check className="h-4 w-4 text-primary flex-shrink-0 mt-1" />
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </ScrollArea>

          {/* Footer */}
          {maxSelections && (
            <div className="p-2 border-t text-xs text-muted-foreground text-center">
              {selectedTaskIds.length} / {maxSelections} selected
            </div>
          )}
        </PopoverContent>
      </Popover>

      {/* Q7 Hard Block Warning */}
      {selectedTasks.length > 0 && (
        <p className="text-xs text-muted-foreground flex items-center gap-1">
          <Link2 className="h-3 w-3" />
          <span>
            Q7: These tasks must be completed before this task can proceed (Hard Block)
          </span>
        </p>
      )}
    </div>
  )
}

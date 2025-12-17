"use client"

/**
 * FilterPanel - Kanban task filtering controls
 *
 * Features:
 * - Phase filtering (multi-select)
 * - Status filtering (multi-select)
 * - Priority filtering (multi-select)
 * - Active filter count badge
 * - Clear all filters button
 */

import { useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Filter,
  X,
  ChevronDown,
} from 'lucide-react'
import type { Phase, Priority, TaskStatus } from '@/lib/types/kanban'

export interface FilterState {
  phases: Phase[]
  statuses: TaskStatus[]
  priorities: Priority[]
}

interface FilterPanelProps {
  filters: FilterState
  onFiltersChange: (filters: FilterState) => void
}

const PHASES: { value: Phase; label: string; color: string }[] = [
  { value: 'ideation', label: 'Ideation', color: 'bg-purple-100 text-purple-700' },
  { value: 'design', label: 'Design', color: 'bg-blue-100 text-blue-700' },
  { value: 'mvp', label: 'MVP', color: 'bg-cyan-100 text-cyan-700' },
  { value: 'implementation', label: 'Implementation', color: 'bg-green-100 text-green-700' },
  { value: 'testing', label: 'Testing', color: 'bg-orange-100 text-orange-700' },
]

const STATUSES: { value: TaskStatus; label: string; color: string }[] = [
  { value: 'pending', label: 'To Do', color: 'bg-slate-100 text-slate-700' },
  { value: 'in_progress', label: 'In Progress', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'blocked', label: 'Blocked', color: 'bg-red-100 text-red-700' },
  { value: 'completed', label: 'Done', color: 'bg-green-100 text-green-700' },
]

const PRIORITIES: { value: Priority; label: string; color: string }[] = [
  { value: 'low', label: 'Low', color: 'bg-blue-100 text-blue-600' },
  { value: 'medium', label: 'Medium', color: 'bg-yellow-100 text-yellow-600' },
  { value: 'high', label: 'High', color: 'bg-orange-100 text-orange-600' },
  { value: 'critical', label: 'Critical', color: 'bg-red-100 text-red-600' },
]

export function FilterPanel({ filters, onFiltersChange }: FilterPanelProps) {
  const [isOpen, setIsOpen] = useState(false)

  const activeFilterCount =
    filters.phases.length + filters.statuses.length + filters.priorities.length

  const handlePhaseToggle = useCallback(
    (phase: Phase) => {
      const newPhases = filters.phases.includes(phase)
        ? filters.phases.filter((p) => p !== phase)
        : [...filters.phases, phase]
      onFiltersChange({ ...filters, phases: newPhases })
    },
    [filters, onFiltersChange]
  )

  const handleStatusToggle = useCallback(
    (status: TaskStatus) => {
      const newStatuses = filters.statuses.includes(status)
        ? filters.statuses.filter((s) => s !== status)
        : [...filters.statuses, status]
      onFiltersChange({ ...filters, statuses: newStatuses })
    },
    [filters, onFiltersChange]
  )

  const handlePriorityToggle = useCallback(
    (priority: Priority) => {
      const newPriorities = filters.priorities.includes(priority)
        ? filters.priorities.filter((p) => p !== priority)
        : [...filters.priorities, priority]
      onFiltersChange({ ...filters, priorities: newPriorities })
    },
    [filters, onFiltersChange]
  )

  const handleClearAll = useCallback(() => {
    onFiltersChange({ phases: [], statuses: [], priorities: [] })
  }, [onFiltersChange])

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="relative">
          <Filter className="h-4 w-4 mr-2" />
          Filter
          {activeFilterCount > 0 && (
            <Badge
              variant="secondary"
              className="ml-2 h-5 w-5 p-0 flex items-center justify-center text-xs bg-primary text-primary-foreground"
            >
              {activeFilterCount}
            </Badge>
          )}
          <ChevronDown className="h-3 w-3 ml-1" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-4" align="start">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-sm">Filter Tasks</h4>
            {activeFilterCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearAll}
                className="h-auto p-1 text-xs text-muted-foreground hover:text-foreground"
              >
                <X className="h-3 w-3 mr-1" />
                Clear all
              </Button>
            )}
          </div>

          {/* Phase Filter */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Phase
            </label>
            <div className="grid grid-cols-2 gap-2">
              {PHASES.map((phase) => (
                <label
                  key={phase.value}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <Checkbox
                    checked={filters.phases.includes(phase.value)}
                    onCheckedChange={() => handlePhaseToggle(phase.value)}
                  />
                  <span className={`text-xs px-2 py-0.5 rounded ${phase.color}`}>
                    {phase.label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Status Filter */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Status
            </label>
            <div className="grid grid-cols-2 gap-2">
              {STATUSES.map((status) => (
                <label
                  key={status.value}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <Checkbox
                    checked={filters.statuses.includes(status.value)}
                    onCheckedChange={() => handleStatusToggle(status.value)}
                  />
                  <span className={`text-xs px-2 py-0.5 rounded ${status.color}`}>
                    {status.label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Priority Filter */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Priority
            </label>
            <div className="grid grid-cols-2 gap-2">
              {PRIORITIES.map((priority) => (
                <label
                  key={priority.value}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <Checkbox
                    checked={filters.priorities.includes(priority.value)}
                    onCheckedChange={() => handlePriorityToggle(priority.value)}
                  />
                  <span className={`text-xs px-2 py-0.5 rounded ${priority.color}`}>
                    {priority.label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Active Filters Summary */}
          {activeFilterCount > 0 && (
            <div className="pt-2 border-t">
              <p className="text-xs text-muted-foreground">
                {activeFilterCount} filter{activeFilterCount > 1 ? 's' : ''} active
              </p>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}

/**
 * Hook to manage filter state
 */
export function useFilterState() {
  const [filters, setFilters] = useState<FilterState>({
    phases: [],
    statuses: [],
    priorities: [],
  })

  const clearFilters = useCallback(() => {
    setFilters({ phases: [], statuses: [], priorities: [] })
  }, [])

  return {
    filters,
    setFilters,
    clearFilters,
    hasActiveFilters:
      filters.phases.length > 0 ||
      filters.statuses.length > 0 ||
      filters.priorities.length > 0,
  }
}

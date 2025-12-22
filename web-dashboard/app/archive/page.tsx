"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { archiveAPI } from '@/lib/api/kanban-archive'
import type { ArchiveFilter } from '@/lib/api/kanban-archive'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Archive, Clock, CheckCircle2, TrendingUp } from 'lucide-react'
import type { Phase } from '@/lib/types/kanban'

export default function ArchivePage() {
  const [filters, setFilters] = useState<ArchiveFilter>({
    page: 1,
    page_size: 20,
  })

  const { data, isLoading } = useQuery({
    queryKey: ['archive', filters],
    queryFn: () => archiveAPI.fetchArchivedTasks(filters),
  })

  const stats = data?.roi_statistics

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <Archive className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">Archive</h1>
        </div>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-card p-4 rounded-lg border">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Archive className="h-4 w-4" />
                Total Archived
              </div>
              <div className="text-2xl font-bold mt-1">{stats.total_archived}</div>
            </div>
            <div className="bg-card p-4 rounded-lg border">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                Estimated
              </div>
              <div className="text-2xl font-bold mt-1">{stats.total_estimated_hours.toFixed(1)}h</div>
            </div>
            <div className="bg-card p-4 rounded-lg border">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <CheckCircle2 className="h-4 w-4" />
                Actual
              </div>
              <div className="text-2xl font-bold mt-1">{stats.total_actual_hours.toFixed(1)}h</div>
            </div>
            <div className="bg-card p-4 rounded-lg border">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <TrendingUp className="h-4 w-4" />
                Efficiency
              </div>
              <div className="text-2xl font-bold mt-1">
                {stats.total_estimated_hours > 0 ? ((stats.total_actual_hours / stats.total_estimated_hours) * 100).toFixed(0) : 0}%
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-4">
          <Select
            value={filters.phase || 'all'}
            onValueChange={(val) =>
              setFilters({ ...filters, phase: val === 'all' ? undefined : val as Phase, page: 1 })
            }
          >
            <SelectTrigger className="w-48">
              <SelectValue placeholder="All Phases" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Phases</SelectItem>
              <SelectItem value="ideation">Ideation</SelectItem>
              <SelectItem value="design">Design</SelectItem>
              <SelectItem value="mvp">MVP</SelectItem>
              <SelectItem value="implementation">Implementation</SelectItem>
              <SelectItem value="testing">Testing</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="bg-card rounded-lg border">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading...</div>
          ) : !data || data.items.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">No archived tasks</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium">Title</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Phase</th>
                    <th className="px-4 py-3 text-left text-sm font-medium">Priority</th>
                    <th className="px-4 py-3 text-right text-sm font-medium">Hours</th>
                    <th className="px-4 py-3 text-center text-sm font-medium">Obsidian</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {data.items.map((task) => (
                    <tr key={task.id} className="hover:bg-muted/20">
                      <td className="px-4 py-3">
                        <div className="font-medium">{task.title}</div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{task.phase}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={task.priority === 'critical' ? 'destructive' : 'default'}>
                          {task.priority}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right">{task.actual_hours?.toFixed(1) || '0.0'}h</td>
                      <td className="px-4 py-3 text-center">
                        <Badge variant={task.obsidian_synced ? 'default' : 'outline'}>
                          {task.obsidian_synced ? 'Synced' : 'Not Synced'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

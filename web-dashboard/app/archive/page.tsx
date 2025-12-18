"use client"

/**
 * Archive Page - Archived Kanban tasks with AI summarization
 *
 * Week 7 Day 2: Archive View Frontend
 *
 * Features (Q6 implementation):
 * - Paginated archive list
 * - AI-generated summaries (GPT-4o)
 * - ROI metrics display
 * - Obsidian knowledge extraction status
 * - Filter by phase, archiver, AI suggestion, quality score
 * - Restore archived task
 *
 * Backend: Week 3 完了 (kanban_archive router)
 */

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Archive,
  ArrowLeft,
  Filter,
  TrendingUp,
  Brain,
  Clock,
  Award,
  FileText,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { archiveAPI } from '@/lib/api/kanban-archive'
import type { ArchivedTask, ArchiveStats } from '@/lib/api/kanban-archive'

// Types imported from API client

export default function ArchivePage() {
  const router = useRouter()
  const [archives, setArchives] = useState<ArchivedTask[]>([])
  const [stats, setStats] = useState<ArchiveStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [error, setError] = useState<string | null>(null)
  const [useMockData, setUseMockData] = useState(false)

  // Filters
  const [phaseFilter, setPhaseFilter] = useState<string>('all')
  const [aiSuggestedFilter, setAiSuggestedFilter] = useState<string>('all')

  const itemsPerPage = 10

  useEffect(() => {
    fetchArchives()
    fetchStats()
  }, [currentPage, phaseFilter, aiSuggestedFilter])

  const fetchArchives = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const filters = {
        page: currentPage,
        per_page: itemsPerPage,
        ...(phaseFilter !== 'all' && { phase: phaseFilter }),
        ...(aiSuggestedFilter !== 'all' && { ai_suggested: aiSuggestedFilter === 'true' }),
      }

      const response = await archiveAPI.fetchArchiveList(filters)
      setArchives(response.items)
      setTotalPages(response.total_pages)
      setStats(response.statistics)
      setUseMockData(false)
    } catch (error) {
      console.error('Failed to fetch archives:', error)
      setError(error instanceof Error ? error.message : 'Failed to fetch archives')

      // Fallback to mock data on error
      if (archives.length === 0) {
        setArchives(mockArchives)
        setTotalPages(2)
        setUseMockData(true)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const data = await archiveAPI.fetchArchiveStatistics()
      setStats(data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)

      // Fallback to mock stats
      if (!stats) {
        setStats({
          total_count: 15,
          avg_efficiency: 0.87,
          total_time_saved: 42.5,
          avg_quality_score: 0.92,
        })
      }
    }
  }

  const handleRestore = async (archiveId: string) => {
    try {
      await archiveAPI.restoreArchivedTask(archiveId)
      // Refresh archive list after restore
      await fetchArchives()
      await fetchStats()
    } catch (error) {
      console.error('Failed to restore archive:', error)
      setError(error instanceof Error ? error.message : 'Failed to restore task')
    }
  }

  const handleRetryApi = async () => {
    setUseMockData(false)
    setError(null)
    await fetchArchives()
    await fetchStats()
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push('/kanban')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Kanban
          </Button>
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Archive className="h-8 w-8" />
              Archive
            </h1>
            <p className="text-muted-foreground">
              Completed tasks with AI summaries and ROI metrics
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={fetchArchives}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Connection Status Banner */}
      {(useMockData || error) && (
        <div className="mb-4 p-3 rounded-lg bg-yellow-100 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <span className="text-sm text-yellow-700 dark:text-yellow-300">
              Using demo data - Backend API unavailable
              {error && (
                <span className="ml-1 text-xs opacity-75">
                  ({error})
                </span>
              )}
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRetryApi}
            className="text-yellow-700 border-yellow-300 hover:bg-yellow-200"
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            Retry Connection
          </Button>
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Archive className="h-4 w-4" />
                Total Archived
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_count}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Avg Efficiency
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(stats.avg_efficiency * 100).toFixed(0)}%</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Time Saved
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_time_saved.toFixed(1)}h</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Award className="h-4 w-4" />
                Avg Quality
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(stats.avg_quality_score * 100).toFixed(0)}%</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <Select value={phaseFilter} onValueChange={setPhaseFilter}>
          <SelectTrigger className="w-48">
            <Filter className="h-4 w-4 mr-2" />
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
        <Select value={aiSuggestedFilter} onValueChange={setAiSuggestedFilter}>
          <SelectTrigger className="w-48">
            <Brain className="h-4 w-4 mr-2" />
            <SelectValue placeholder="All Tasks" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Tasks</SelectItem>
            <SelectItem value="true">AI Suggested Only</SelectItem>
            <SelectItem value="false">Manual Only</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Archive List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : archives.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Archive className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No Archived Tasks</h3>
            <p className="text-muted-foreground">
              Completed tasks will appear here with AI summaries
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {archives.map((archive) => (
            <Card key={archive.id} className="overflow-hidden">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CardTitle className="text-lg">{archive.title}</CardTitle>
                      <Badge variant="outline">{archive.phase}</Badge>
                      <Badge
                        variant={
                          archive.priority === 'critical'
                            ? 'destructive'
                            : archive.priority === 'high'
                            ? 'default'
                            : 'secondary'
                        }
                      >
                        {archive.priority}
                      </Badge>
                      {archive.was_ai_suggested && (
                        <Badge className="bg-purple-500">
                          AI ({archive.original_confidence ? `${(archive.original_confidence * 100).toFixed(0)}%` : 'N/A'})
                        </Badge>
                      )}
                      {archive.obsidian_knowledge.extracted && (
                        <Badge variant="outline" className="text-green-600 border-green-600">
                          <FileText className="h-3 w-3 mr-1" />
                          Obsidian
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mb-1">{archive.description}</p>
                    <p className="text-xs text-muted-foreground">
                      Archived by {archive.archived_by} • {new Date(archive.archived_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleRestore(archive.id)}
                  >
                    Restore
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* AI Summary */}
                <div className="bg-muted/50 rounded-lg p-4">
                  <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                    <Brain className="h-4 w-4" />
                    AI Summary
                  </h4>
                  <p className="text-sm mb-3">{archive.ai_summary.summary}</p>

                  {archive.ai_summary.key_learnings.length > 0 && (
                    <div className="mb-2">
                      <p className="text-xs font-semibold mb-1">Key Learnings:</p>
                      <ul className="text-xs space-y-1">
                        {archive.ai_summary.key_learnings.map((learning, idx) => (
                          <li key={idx} className="flex items-start gap-1">
                            <span className="text-green-600">•</span>
                            {learning}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {archive.ai_summary.technical_insights.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold mb-1">Technical Insights:</p>
                      <ul className="text-xs space-y-1">
                        {archive.ai_summary.technical_insights.map((insight, idx) => (
                          <li key={idx} className="flex items-start gap-1">
                            <span className="text-blue-600">•</span>
                            {insight}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* ROI Metrics */}
                <div className="grid grid-cols-4 gap-3">
                  <div className="text-center p-3 bg-muted/50 rounded">
                    <TrendingUp className="h-4 w-4 mx-auto mb-1 text-green-600" />
                    <p className="text-xs text-muted-foreground">Efficiency</p>
                    <p className="text-sm font-semibold">
                      {(archive.roi_metrics.efficiency_score * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="text-center p-3 bg-muted/50 rounded">
                    <Clock className="h-4 w-4 mx-auto mb-1 text-blue-600" />
                    <p className="text-xs text-muted-foreground">Time Saved</p>
                    <p className="text-sm font-semibold">
                      {archive.roi_metrics.time_saved_hours.toFixed(1)}h
                    </p>
                  </div>
                  <div className="text-center p-3 bg-muted/50 rounded">
                    <Award className="h-4 w-4 mx-auto mb-1 text-yellow-600" />
                    <p className="text-xs text-muted-foreground">Quality</p>
                    <p className="text-sm font-semibold">
                      {(archive.roi_metrics.quality_score * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="text-center p-3 bg-muted/50 rounded">
                    <FileText className="h-4 w-4 mx-auto mb-1 text-purple-600" />
                    <p className="text-xs text-muted-foreground">Compliance</p>
                    <p className="text-sm font-semibold">
                      {(archive.roi_metrics.constitutional_compliance_rate * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}

// Mock data for development (to be replaced with API)
const mockArchives: ArchivedTask[] = [
  {
    id: 'arch-1',
    task_id: '1',
    title: 'Setup authentication system',
    description: 'Implement JWT-based authentication with refresh tokens',
    phase: 'implementation',
    priority: 'critical',
    status: 'completed',
    archived_by: 'developer',
    archived_at: '2025-12-16T18:00:00Z',
    was_ai_suggested: true,
    original_confidence: 0.85,
    ai_summary: {
      summary: 'Successfully implemented JWT authentication with refresh token rotation. Security best practices applied including HTTP-only cookies and CSRF protection.',
      key_learnings: [
        'JWT token rotation improves security significantly',
        'HTTP-only cookies prevent XSS attacks',
        'Refresh tokens must have shorter expiry than access tokens',
      ],
      technical_insights: [
        'Used jsonwebtoken library with RS256 algorithm',
        'Implemented token blacklist for logout',
        'Added rate limiting to prevent brute force attacks',
      ],
      next_steps_recommendation: [
        'Add 2FA support',
        'Implement OAuth providers',
        'Add session management dashboard',
      ],
    },
    roi_metrics: {
      efficiency_score: 0.92,
      time_saved_hours: 3.5,
      quality_score: 0.95,
      constitutional_compliance_rate: 1.0,
    },
    obsidian_knowledge: {
      extracted: true,
      note_path: '개발일지/2025-12-16/Authentication-Implementation.md',
      tags: ['auth', 'security', 'jwt'],
      linked_concepts: ['JWT', 'OAuth', 'Security Best Practices'],
    },
  },
  {
    id: 'arch-2',
    task_id: '2',
    title: 'Design database schema',
    description: 'Create PostgreSQL schema for user management',
    phase: 'design',
    priority: 'high',
    status: 'completed',
    archived_by: 'tech-lead',
    archived_at: '2025-12-15T17:30:00Z',
    was_ai_suggested: false,
    ai_summary: {
      summary: 'Designed comprehensive PostgreSQL schema with proper normalization and indexes. Followed best practices for scalability.',
      key_learnings: [
        'Proper indexing strategy is crucial for query performance',
        'Foreign key constraints ensure data integrity',
      ],
      technical_insights: [
        'Used composite indexes for frequently queried columns',
        'Implemented soft delete pattern for user records',
      ],
      next_steps_recommendation: [
        'Add database migration scripts',
        'Setup database monitoring',
      ],
    },
    roi_metrics: {
      efficiency_score: 0.88,
      time_saved_hours: 2.0,
      quality_score: 0.90,
      constitutional_compliance_rate: 0.95,
    },
    obsidian_knowledge: {
      extracted: false,
    },
  },
]

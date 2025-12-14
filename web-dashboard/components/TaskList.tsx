"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Terminal, GitBranch, FileText, Clock, AlertCircle, CheckCircle, Play, Rocket, Code2, Zap, TrendingUp, Package, ExternalLink, ChevronRight } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

interface TodoItem {
  title: string
  status: 'completed' | 'in_progress' | 'pending'
  subtasks?: string[]
  acceptance_criteria?: string[]
  files?: string[]
}

interface TodoGroup {
  id: string
  title: string
  status: 'completed' | 'in_progress' | 'pending'
  order: number
  items: TodoItem[]
}

interface Task {
  id: string
  title: string
  description: string
  project: string
  project_id: string
  phase: string
  status: 'in_progress' | 'pending' | 'blocked' | 'completed'
  current_step: {
    group_index: number
    item_index: number
    description: string
  }
  completeness: number
  estimated_hours: number
  actual_hours: number
  git_branch: string
  updated_at: string
  todo_groups?: TodoGroup[]
  last_commit?: string
}

interface TaskContext {
  task_id: string
  command: string
  current_todo?: {
    group: string
    item: string
    subtasks?: string[]
    files?: string[]
  }
  git_branch?: string
  files?: string[]
  prompt_history?: string[]
  checkpoint?: {
    step: string
    next_action: string
    blockers?: string[]
  }
}

export function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [taskContext, setTaskContext] = useState<TaskContext | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    fetchTasks()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const fetchTasks = async () => {
    try {
      const res = await fetch('/api/tasks/')
      if (res.ok) {
        const data = await res.json()
        setTasks(data)
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch tasks",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchTaskDetails = async (taskId: string) => {
    try {
      const [detailRes, contextRes] = await Promise.all([
        fetch(`/api/tasks/${taskId}`),
        fetch(`/api/tasks/${taskId}/context`)
      ])

      if (detailRes.ok && contextRes.ok) {
        const detail = await detailRes.json()
        const context = await contextRes.json()
        setSelectedTask(detail)
        setTaskContext(context)
        setDetailsOpen(true)
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch task details",
        variant: "destructive"
      })
    }
  }

  const continueInCLI = async (taskId: string) => {
    try {
      const res = await fetch(`/api/tasks/${taskId}/context`)
      if (res.ok) {
        const context = await res.json()
        await navigator.clipboard.writeText(context.command)

        toast({
          title: "🚀 Command Copied!",
          description: `터미널에 붙여넣기하세요: ${context.command}`
        })

        try {
          window.location.href = context.command
        } catch (e) {
          // Protocol handler not installed
        }
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to generate CLI command",
        variant: "destructive"
      })
    }
  }

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'in_progress':
        return {
          color: 'from-blue-500 to-cyan-500',
          bgColor: 'bg-blue-500/10',
          borderColor: 'border-blue-500/20',
          textColor: 'text-blue-400',
          icon: <Play className="w-4 h-4" />
        }
      case 'completed':
        return {
          color: 'from-green-500 to-emerald-500',
          bgColor: 'bg-green-500/10',
          borderColor: 'border-green-500/20',
          textColor: 'text-green-400',
          icon: <CheckCircle className="w-4 h-4" />
        }
      case 'blocked':
        return {
          color: 'from-red-500 to-orange-500',
          bgColor: 'bg-red-500/10',
          borderColor: 'border-red-500/20',
          textColor: 'text-red-400',
          icon: <AlertCircle className="w-4 h-4" />
        }
      default:
        return {
          color: 'from-gray-500 to-slate-500',
          bgColor: 'bg-gray-500/10',
          borderColor: 'border-gray-500/20',
          textColor: 'text-gray-400',
          icon: <Clock className="w-4 h-4" />
        }
    }
  }

  const getPhaseIcon = (phase: string) => {
    switch (phase) {
      case 'development':
        return <Code2 className="w-4 h-4" />
      case 'planning':
        return <Package className="w-4 h-4" />
      case 'testing':
        return <Zap className="w-4 h-4" />
      case 'deployment':
        return <Rocket className="w-4 h-4" />
      default:
        return <FileText className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 animate-pulse" />
        <Card className="relative bg-gray-900/50 backdrop-blur-xl border-gray-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-white">
              <Terminal className="w-6 h-6 text-blue-400" />
              Active Development Tasks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex justify-center items-center h-32">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="rounded-full h-12 w-12 border-4 border-blue-500/20 border-t-blue-500"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative overflow-hidden"
      >
        {/* Animated background gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-pink-500/5" />
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-transparent to-purple-500/10"
          animate={{
            x: [-1000, 1000],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear"
          }}
        />

        <Card className="relative bg-gray-900/50 backdrop-blur-xl border-gray-700/50 shadow-2xl">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
                  <Terminal className="w-6 h-6 text-white" />
                </div>
                <div>
                  <CardTitle className="text-2xl font-bold text-white">
                    Active Development Tasks
                  </CardTitle>
                  <CardDescription className="text-gray-400 mt-1">
                    작업을 클릭하여 상세정보 확인 및 CLI에서 계속하기
                  </CardDescription>
                </div>
              </div>
              <Badge variant="outline" className="px-3 py-1 bg-blue-500/10 border-blue-500/30 text-blue-400">
                <TrendingUp className="w-3 h-3 mr-1" />
                {tasks.length} Tasks
              </Badge>
            </div>
          </CardHeader>

          <CardContent>
            <AnimatePresence mode="popLayout">
              {tasks.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-center py-12"
                >
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-800/50 mb-4">
                    <FileText className="w-8 h-8 text-gray-600" />
                  </div>
                  <p className="text-gray-400">작업이 없습니다</p>
                  <p className="text-gray-600 text-sm mt-1">새로운 개발 작업을 시작하세요</p>
                </motion.div>
              ) : (
                <div className="space-y-3">
                  {tasks.map((task, index) => {
                    const statusConfig = getStatusConfig(task.status)
                    return (
                      <motion.div
                        key={task.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        whileHover={{ scale: 1.01, y: -2 }}
                        className="group"
                      >
                        <Card className={cn(
                          "relative overflow-hidden bg-gray-800/40 backdrop-blur border-gray-700/50",
                          "hover:border-gray-600 hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300"
                        )}>
                          {/* Status accent bar */}
                          <div className={cn("absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b", statusConfig.color)} />

                          {/* Hover gradient effect */}
                          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/5 to-purple-500/0 opacity-0 group-hover:opacity-100 transition-opacity" />

                          <CardContent className="p-5 relative">
                            <div className="flex justify-between items-start gap-4">
                              <div className="flex-1 min-w-0">
                                {/* Header */}
                                <div className="flex items-start gap-3 mb-3">
                                  <div className={cn("p-2 rounded-lg mt-1", statusConfig.bgColor)}>
                                    {getPhaseIcon(task.phase)}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-2">
                                      <h3 className="font-semibold text-lg text-white truncate">
                                        {task.title}
                                      </h3>
                                      <Badge className={cn(
                                        "px-2 py-0.5 text-xs font-medium border",
                                        statusConfig.bgColor,
                                        statusConfig.borderColor,
                                        statusConfig.textColor
                                      )}>
                                        <span className="flex items-center gap-1">
                                          {statusConfig.icon}
                                          {task.status.replace('_', ' ')}
                                        </span>
                                      </Badge>
                                    </div>

                                    <p className="text-sm text-gray-400 line-clamp-2 mb-3">
                                      {task.description}
                                    </p>

                                    {/* Meta information */}
                                    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
                                      <span className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-800/50">
                                        <FileText className="w-3 h-3 text-blue-400" />
                                        {task.project}
                                      </span>
                                      <span className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-800/50">
                                        <GitBranch className="w-3 h-3 text-green-400" />
                                        {task.git_branch}
                                      </span>
                                      <span className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-800/50">
                                        <Clock className="w-3 h-3 text-orange-400" />
                                        {task.actual_hours}h / {task.estimated_hours}h
                                      </span>
                                    </div>
                                  </div>
                                </div>

                                {/* Progress section */}
                                <div className="space-y-2 mt-4">
                                  <div className="flex justify-between items-center text-xs">
                                    <span className="text-gray-400 font-medium">Progress</span>
                                    <span className="text-blue-400 font-semibold">{task.completeness}%</span>
                                  </div>
                                  <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
                                    <motion.div
                                      initial={{ width: 0 }}
                                      animate={{ width: `${task.completeness}%` }}
                                      transition={{ duration: 1, delay: index * 0.1 }}
                                      className={cn("h-full bg-gradient-to-r", statusConfig.color)}
                                    />
                                    {/* Animated shimmer effect */}
                                    <motion.div
                                      className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                                      animate={{
                                        x: [-100, 300],
                                      }}
                                      transition={{
                                        duration: 2,
                                        repeat: Infinity,
                                        ease: "linear",
                                        delay: index * 0.2
                                      }}
                                    />
                                  </div>
                                  <p className="text-xs text-gray-500 flex items-center gap-1.5">
                                    <ChevronRight className="w-3 h-3" />
                                    {task.current_step.description}
                                  </p>
                                </div>
                              </div>

                              {/* Action buttons */}
                              <div className="flex flex-col gap-2 shrink-0">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => fetchTaskDetails(task.id)}
                                  className="bg-gray-800/50 border-gray-700 hover:bg-gray-700 hover:border-gray-600 text-gray-300"
                                >
                                  <ExternalLink className="w-3 h-3 mr-1.5" />
                                  Details
                                </Button>
                                <Button
                                  size="sm"
                                  onClick={() => continueInCLI(task.id)}
                                  className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white border-0 shadow-lg shadow-blue-500/20"
                                >
                                  <Terminal className="w-3 h-3 mr-1.5" />
                                  Continue
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    )
                  })}
                </div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
      </motion.div>

      {/* Enhanced Task Details Dialog */}
      <Dialog open={detailsOpen} onOpenChange={setDetailsOpen}>
        <DialogContent className="max-w-5xl max-h-[85vh] overflow-hidden bg-gray-900/95 backdrop-blur-xl border-gray-700/50 text-white">
          <DialogHeader className="pb-4 border-b border-gray-800">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500">
                <Code2 className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <DialogTitle className="text-2xl font-bold">{selectedTask?.title}</DialogTitle>
                <DialogDescription className="text-gray-400 mt-1">
                  {selectedTask?.description}
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          {selectedTask && taskContext && (
            <Tabs defaultValue="todo" className="mt-4">
              <TabsList className="bg-gray-800/50 border border-gray-700">
                <TabsTrigger value="todo" className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-400">
                  <CheckCircle className="w-4 h-4 mr-2" />
                  TODO List
                </TabsTrigger>
                <TabsTrigger value="context" className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-400">
                  <Terminal className="w-4 h-4 mr-2" />
                  Context
                </TabsTrigger>
                <TabsTrigger value="history" className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-400">
                  <Clock className="w-4 h-4 mr-2" />
                  History
                </TabsTrigger>
              </TabsList>

              <ScrollArea className="h-[450px] mt-4">
                <TabsContent value="todo" className="mt-0 space-y-4">
                  {selectedTask.todo_groups?.map((group, index) => {
                    const statusConfig = getStatusConfig(group.status)
                    return (
                      <motion.div
                        key={group.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                      >
                        <Card className="bg-gray-800/30 border-gray-700/50">
                          <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                              <h4 className="font-semibold text-white flex items-center gap-2">
                                {group.title}
                              </h4>
                              <Badge variant="outline" className={cn(statusConfig.bgColor, statusConfig.borderColor, statusConfig.textColor)}>
                                {group.status.replace('_', ' ')}
                              </Badge>
                            </div>
                          </CardHeader>
                          <CardContent className="space-y-2">
                            {group.items.map((item, idx) => (
                              <div key={idx} className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-700/30 transition-colors">
                                <input
                                  type="checkbox"
                                  checked={item.status === 'completed'}
                                  readOnly
                                  className="mt-1 w-4 h-4 rounded border-gray-600 bg-gray-800 checked:bg-blue-500"
                                />
                                <div className="flex-1">
                                  <p className={cn(
                                    "text-sm",
                                    item.status === 'completed' ? 'text-gray-500 line-through' : 'text-gray-300'
                                  )}>
                                    {item.title}
                                  </p>
                                  {item.subtasks && (
                                    <ul className="text-xs text-gray-500 mt-1 ml-4 space-y-0.5">
                                      {item.subtasks.map((subtask, sidx) => (
                                        <li key={sidx} className="flex items-center gap-1.5">
                                          <div className="w-1 h-1 rounded-full bg-gray-600" />
                                          {subtask}
                                        </li>
                                      ))}
                                    </ul>
                                  )}
                                </div>
                              </div>
                            ))}
                          </CardContent>
                        </Card>
                      </motion.div>
                    )
                  })}
                </TabsContent>

                <TabsContent value="context" className="mt-0 space-y-4">
                  {/* Current TODO */}
                  <Card className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border-blue-500/20">
                    <CardHeader>
                      <h4 className="font-semibold text-white flex items-center gap-2">
                        <Zap className="w-4 h-4 text-yellow-400" />
                        Current TODO
                      </h4>
                    </CardHeader>
                    <CardContent>
                      <p className="font-medium text-blue-300">{taskContext.current_todo?.group}</p>
                      <p className="text-sm mt-1 text-gray-300">{taskContext.current_todo?.item}</p>
                      {taskContext.current_todo?.subtasks && (
                        <ul className="text-xs text-gray-400 mt-2 ml-4 space-y-1">
                          {taskContext.current_todo.subtasks.map((subtask, idx) => (
                            <li key={idx} className="flex items-center gap-2">
                              <ChevronRight className="w-3 h-3" />
                              {subtask}
                            </li>
                          ))}
                        </ul>
                      )}
                    </CardContent>
                  </Card>

                  {/* Git Branch */}
                  <div>
                    <h4 className="font-semibold mb-2 text-white flex items-center gap-2">
                      <GitBranch className="w-4 h-4 text-green-400" />
                      Git Branch
                    </h4>
                    <Badge variant="secondary" className="font-mono px-3 py-1.5 bg-gray-800/50 text-green-400 border-green-500/20">
                      {taskContext.git_branch}
                    </Badge>
                  </div>

                  {/* Related Files */}
                  <div>
                    <h4 className="font-semibold mb-2 text-white flex items-center gap-2">
                      <FileText className="w-4 h-4 text-blue-400" />
                      Related Files
                    </h4>
                    <ScrollArea className="h-[180px]">
                      <div className="space-y-1">
                        {taskContext.files?.map((file, idx) => (
                          <div key={idx} className="text-sm font-mono p-2 hover:bg-gray-700/30 rounded-md text-gray-400 transition-colors">
                            {file}
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>

                  {/* Checkpoint */}
                  {taskContext.checkpoint && (
                    <Card className="bg-gray-800/30 border-gray-700/50">
                      <CardHeader>
                        <h4 className="font-semibold text-white">Checkpoint</h4>
                      </CardHeader>
                      <CardContent className="space-y-2 text-sm">
                        <div>
                          <span className="font-medium text-gray-400">Current Step:</span>
                          <p className="text-gray-300 mt-1">{taskContext.checkpoint.step}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-400">Next Action:</span>
                          <p className="text-gray-300 mt-1">{taskContext.checkpoint.next_action}</p>
                        </div>
                        {taskContext.checkpoint.blockers && (
                          <div>
                            <span className="font-medium text-red-400">Blockers:</span>
                            <ul className="text-xs text-red-400 mt-1 ml-4 space-y-1">
                              {taskContext.checkpoint.blockers.map((blocker, idx) => (
                                <li key={idx} className="flex items-center gap-2">
                                  <AlertCircle className="w-3 h-3" />
                                  {blocker}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="history" className="mt-0">
                  <div className="space-y-2">
                    {taskContext.prompt_history?.map((prompt, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.05 }}
                      >
                        <Card className="bg-gray-800/30 border-gray-700/50 hover:border-gray-600/50 transition-colors">
                          <CardContent className="p-3">
                            <div className="flex items-start gap-3">
                              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-xs font-semibold text-blue-400">
                                {idx + 1}
                              </div>
                              <p className="text-sm font-mono text-gray-300 flex-1">{prompt}</p>
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    ))}
                  </div>
                </TabsContent>
              </ScrollArea>
            </Tabs>
          )}

          <Separator className="bg-gray-800" />

          <CardFooter className="flex justify-end gap-3 pt-4">
            <Button
              variant="outline"
              onClick={() => setDetailsOpen(false)}
              className="bg-gray-800/50 border-gray-700 hover:bg-gray-700 hover:border-gray-600"
            >
              Close
            </Button>
            <Button
              onClick={() => selectedTask && continueInCLI(selectedTask.id)}
              className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 shadow-lg shadow-blue-500/20"
            >
              <Terminal className="w-4 h-4 mr-2" />
              Continue in CLI
            </Button>
          </CardFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

"use client"

import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  Package,
  Lock,
  CheckCircle2,
  AlertCircle,
  Clock,
  User,
  GitBranch,
  Play,
  Pause,
  RefreshCcw,
  TrendingUp,
  AlertTriangle,
  Code,
  TestTube,
  Eye
} from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"

interface ModuleDefinition {
  id: string
  name: string
  description: string
  type: "feature" | "bugfix" | "refactor"
  priority: "high" | "medium" | "low"
  estimated_hours: number
  dependencies: string[]
}

interface ModuleOwnership {
  module_id: string
  developer: string
  status: "planning" | "coding" | "testing" | "review" | "completed"
  progress: number
  started_at: string
  estimated_completion: string
  warnings: string[]
}

interface ModuleBoard {
  active: Array<ModuleOwnership & { name: string }>
  available: Array<ModuleDefinition>
  blocked: Array<ModuleDefinition & { blocked_by: string[] }>
  completed: Array<{ module_id: string; name: string }>
}

export function ModuleDashboard() {
  const [selectedModule, setSelectedModule] = useState<string | null>(null)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const queryClient = useQueryClient()

  // 현재 세션 정보 (실제로는 context나 props로 전달)
  const [currentSession] = useState(() => ({
    id: `web_${Date.now()}`,
    developer: "Current Developer"
  }))

  // 모듈 현황 가져오기
  const { data: boardData, isLoading } = useQuery<ModuleBoard>({
    queryKey: ["module-board"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/modules/board`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json()
    },
    refetchInterval: 5000, // 5초마다 새로고침
    refetchOnWindowFocus: true
  })

  // WebSocket 연결
  useEffect(() => {
    const socket = new WebSocket(`${WS_URL}/ws/modules`)

    socket.onopen = () => {
      console.log("Module dashboard WebSocket connected")
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleModuleEvent(data)
    }

    socket.onerror = (error) => {
      console.error("WebSocket error:", error)
    }

    socket.onclose = () => {
      console.log("Module dashboard WebSocket disconnected")
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setWs(socket)

    return () => {
      socket.close()
    }
  }, [])

  const handleModuleEvent = (event: {
    type: string
    module_id?: string
    developer?: string
    new_status?: string
    progress?: number
    completed?: string
  }) => {
    const { type } = event

    switch (type) {
      case "module_claimed":
        toast.info(`${event.developer}님이 ${event.module_id} 모듈 개발 시작`)
        queryClient.invalidateQueries({ queryKey: ["module-board"] })
        break

      case "module_status_changed":
        toast.success(`${event.module_id} 상태: ${event.new_status} (${event.progress}%)`)
        queryClient.invalidateQueries({ queryKey: ["module-board"] })
        break

      case "module_released":
        toast.info(`${event.module_id} 모듈이 해제되었습니다`)
        queryClient.invalidateQueries({ queryKey: ["module-board"] })
        break

      case "module_available":
        if (event.module_id) {
          toast.success(`🎯 ${event.module_id} 모듈을 이제 개발할 수 있습니다!`, {
            duration: 10000,
            action: {
              label: "점유하기",
              onClick: () => claimModule(event.module_id as string)
            }
          })
        }
        break

      case "dependency_completed":
        toast.info(`${event.completed} 완료로 ${event.module_id} 개발 가능`)
        queryClient.invalidateQueries({ queryKey: ["module-board"] })
        break
    }
  }

  // 모듈 점유 mutation
  const claimModuleMutation = useMutation({
    mutationFn: async (moduleId: string) => {
      const res = await fetch(`${API_URL}/api/modules/claim`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          module_id: moduleId,
          session_id: currentSession.id,
          developer_name: currentSession.developer
        })
      })
      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || "Failed to claim module")
      }
      return res.json()
    },
    onSuccess: (data, moduleId) => {
      toast.success(`✅ ${moduleId} 모듈 점유 성공!`)
      queryClient.invalidateQueries({ queryKey: ["module-board"] })
    },
    onError: (error: Error) => {
      toast.error(error.message)
    }
  })

  // 모듈 상태 업데이트 mutation
  const updateStatusMutation = useMutation({
    mutationFn: async ({ moduleId, status }: { moduleId: string; status: string }) => {
      const res = await fetch(`${API_URL}/api/modules/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          module_id: moduleId,
          session_id: currentSession.id,
          new_status: status
        })
      })
      if (!res.ok) throw new Error("Failed to update status")
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["module-board"] })
    }
  })

  // 모듈 해제 mutation
  const releaseModuleMutation = useMutation({
    mutationFn: async (moduleId: string) => {
      const res = await fetch(`${API_URL}/api/modules/release`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          module_id: moduleId,
          session_id: currentSession.id
        })
      })
      if (!res.ok) throw new Error("Failed to release module")
      return res.json()
    },
    onSuccess: (data, moduleId) => {
      toast.info(`${moduleId} 모듈이 해제되었습니다`)
      queryClient.invalidateQueries({ queryKey: ["module-board"] })
    }
  })

  const claimModule = (moduleId: string) => {
    claimModuleMutation.mutate(moduleId)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "planning": return "text-yellow-400 bg-yellow-500/20"
      case "coding": return "text-blue-400 bg-blue-500/20"
      case "testing": return "text-purple-400 bg-purple-500/20"
      case "review": return "text-orange-400 bg-orange-500/20"
      case "completed": return "text-green-400 bg-green-500/20"
      default: return "text-gray-400 bg-gray-500/20"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "planning": return <Clock className="h-4 w-4" />
      case "coding": return <Code className="h-4 w-4" />
      case "testing": return <TestTube className="h-4 w-4" />
      case "review": return <Eye className="h-4 w-4" />
      case "completed": return <CheckCircle2 className="h-4 w-4" />
      default: return <Package className="h-4 w-4" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "text-red-400 border-red-500/30"
      case "medium": return "text-yellow-400 border-yellow-500/30"
      case "low": return "text-green-400 border-green-500/30"
      default: return "text-gray-400 border-gray-500/30"
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCcw className="h-8 w-8 text-purple-400 animate-spin" />
      </div>
    )
  }

  const board = boardData || {
    active: [],
    available: [],
    blocked: [],
    completed: []
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <Package className="h-7 w-7 text-purple-400" />
              Module Development Board
              <span className="text-sm px-2 py-1 bg-blue-500/20 text-blue-400 rounded">
                Standard Level
              </span>
            </h2>
            <p className="text-gray-400 mt-1">
              모듈 단위 개발 조정 시스템 - 충돌 방지 및 협업 관리
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-400">
              Active: {board.active.length} |
              Available: {board.available.length} |
              Blocked: {board.blocked.length}
            </div>
            <button
              onClick={() => queryClient.invalidateQueries({ queryKey: ["module-board"] })}
              className="p-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              <RefreshCcw className="h-5 w-5 text-gray-400" />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">

        {/* 개발 중인 모듈 */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-400" />
            개발 중 ({board.active.length})
          </h3>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {board.active.map((module) => (
              <motion.div
                key={module.module_id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="p-4 rounded-lg bg-gray-900/50 border border-gray-700"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">
                        {module.name}
                      </span>
                      <span className={cn(
                        "px-2 py-0.5 text-xs rounded flex items-center gap-1",
                        getStatusColor(module.status)
                      )}>
                        {getStatusIcon(module.status)}
                        {module.status}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center gap-2 text-xs text-gray-400">
                      <User className="h-3 w-3" />
                      <span>{module.developer}</span>
                    </div>
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                        <span>Progress</span>
                        <span>{module.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-1.5">
                        <div
                          className="bg-blue-500 h-1.5 rounded-full transition-all"
                          style={{ width: `${module.progress}%` }}
                        />
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                      완료 예상: {new Date(module.estimated_completion).toLocaleTimeString()}
                    </div>
                    {module.warnings.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {module.warnings.map((warning, idx) => (
                          <div key={idx} className="flex items-center gap-1 text-xs text-yellow-400">
                            <AlertTriangle className="h-3 w-3" />
                            <span>{warning}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setSelectedModule(module.module_id)}
                    className="p-1.5 rounded hover:bg-gray-700"
                  >
                    <Play className="h-4 w-4 text-gray-400" />
                  </button>
                </div>
              </motion.div>
            ))}

            {board.active.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                개발 중인 모듈이 없습니다
              </div>
            )}
          </div>
        </motion.div>

        {/* 개발 가능한 모듈 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-400" />
            개발 가능 ({board.available.length})
          </h3>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {board.available.map((module) => (
              <motion.div
                key={module.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                whileHover={{ scale: 1.02 }}
                className={cn(
                  "p-4 rounded-lg bg-gray-900/50 border cursor-pointer",
                  getPriorityColor(module.priority)
                )}
                onClick={() => claimModule(module.id)}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-sm font-medium text-white">
                      {module.name}
                    </span>
                    <div className="mt-1 text-xs text-gray-400">
                      {module.description}
                    </div>
                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {module.estimated_hours}h
                      </span>
                      <span className={`px-2 py-0.5 rounded ${
                        module.type === "feature" ? "bg-blue-500/20 text-blue-400" :
                        module.type === "bugfix" ? "bg-red-500/20 text-red-400" :
                        "bg-purple-500/20 text-purple-400"
                      }`}>
                        {module.type}
                      </span>
                    </div>
                  </div>
                  <Lock className="h-4 w-4 text-gray-600" />
                </div>
              </motion.div>
            ))}

            {board.available.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                현재 개발 가능한 모듈이 없습니다
              </div>
            )}
          </div>
        </motion.div>

        {/* 대기 중/차단된 모듈 */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-400" />
            대기 중 ({board.blocked.length})
          </h3>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {board.blocked.map((module) => (
              <motion.div
                key={module.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="p-4 rounded-lg bg-gray-900/50 border border-yellow-500/20"
              >
                <div>
                  <span className="text-sm font-medium text-white">
                    {module.name}
                  </span>
                  <div className="mt-2 space-y-1">
                    {module.blocked_by.map((dep, idx) => (
                      <div key={idx} className="flex items-center gap-1 text-xs text-yellow-400">
                        <GitBranch className="h-3 w-3" />
                        <span>대기: {dep}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}

            {board.blocked.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                대기 중인 모듈이 없습니다
              </div>
            )}
          </div>

          {/* 완료된 모듈 */}
          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-400 mb-3">
              최근 완료 ({board.completed.length})
            </h4>
            <div className="space-y-2">
              {board.completed.slice(0, 3).map((module) => (
                <div
                  key={module.module_id}
                  className="flex items-center gap-2 text-xs text-gray-500"
                >
                  <CheckCircle2 className="h-3 w-3 text-green-400" />
                  <span>{module.name}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Standard Level 규칙 안내 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4"
      >
        <h4 className="text-sm font-medium text-blue-400 mb-2">
          📋 Standard Level 규칙
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-gray-400">
          <div>
            <strong className="text-blue-400">필수 (강제)</strong>
            <ul className="mt-1 space-y-1">
              <li>• 모듈 점유 후 작업</li>
              <li>• 테스트 통과 후 푸시</li>
            </ul>
          </div>
          <div>
            <strong className="text-yellow-400">권장 (경고)</strong>
            <ul className="mt-1 space-y-1">
              <li>• feature/module-id 브랜치</li>
              <li>• 8시간 내 완료</li>
            </ul>
          </div>
          <div>
            <strong className="text-green-400">자동화</strong>
            <ul className="mt-1 space-y-1">
              <li>• Git hooks 검증</li>
              <li>• 상태 자동 업데이트</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
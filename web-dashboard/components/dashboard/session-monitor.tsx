"use client"

import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  Users,
  Lock,
  AlertTriangle,
  Terminal,
  Activity,
  GitBranch,
  FileEdit,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCcw
} from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"

interface Session {
  id: string
  terminal_id: string
  project_id: string | null
  user_id: string
  status: "active" | "idle" | "locked" | "waiting"
  started_at: string
  last_active: string
  is_primary: boolean
  locks: Array<{
    resource: string
    type: string
    acquired_at: string
  }>
  current_branch: string | null
  working_directory: string | null
}

interface Conflict {
  id: string
  type: "file_edit" | "git_merge" | "resource_lock"
  sessions: string[]
  resource: string
  detected_at: string
  resolved: boolean
  resolution_strategy: string | null
}

export function SessionMonitor() {
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [sessionId] = useState(() => `web_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const [conflicts, setConflicts] = useState<Conflict[]>([])
  const [realTimeUpdates, setRealTimeUpdates] = useState<Array<Record<string, unknown>>>([])

  // Fetch active sessions
  const { data: sessionsData, isLoading, refetch } = useQuery({
    queryKey: ["sessions"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/ws/sessions/active`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json()
    },
    refetchInterval: 10000, // Refetch every 10s
    refetchOnWindowFocus: true
  })

  // WebSocket connection for real-time updates
  useEffect(() => {
    const projectId = localStorage.getItem("udo_current_project_id")
    const wsUrl = `${WS_URL}/ws/session?session_id=${sessionId}${projectId ? `&project_id=${projectId}` : ""}`

    const socket = new WebSocket(wsUrl)

    socket.onopen = () => {
      console.log("Session monitor WebSocket connected")
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    }

    socket.onerror = (error) => {
      console.error("WebSocket error:", error)
    }

    socket.onclose = () => {
      console.log("Session monitor WebSocket disconnected")
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setWs(socket)

    return () => {
      socket.close()
    }
  }, [sessionId])

  const handleWebSocketMessage = (data: {
    type: string
    session_id?: string
    id?: string
    conflict_id?: string
    conflict_type?: "file_edit" | "git_merge" | "resource_lock"
    sessions?: string[]
    resource?: string
    timestamp?: string
    resolution_strategy?: string | null
    file_path?: string
    [key: string]: unknown
  }) => {
    const { type } = data

    switch (type) {
      case "session_connected":
        if (data.session_id) {
          toast.success(`New session connected: ${data.session_id.substr(0, 8)}`)
        }
        refetch()
        break

      case "session_disconnected":
        if (data.session_id) {
          toast.info(`Session disconnected: ${data.session_id.substr(0, 8)}`)
        }
        refetch()
        break

      case "lock_acquired":
        setRealTimeUpdates(prev => [{
          ...data,
          timestamp: new Date().toISOString()
        }, ...prev.slice(0, 9)])
        break

      case "lock_released":
        setRealTimeUpdates(prev => [{
          ...data,
          timestamp: new Date().toISOString()
        }, ...prev.slice(0, 9)])
        break

      case "conflict_detected":
        if (data.id && data.conflict_type && data.sessions && data.resource && data.timestamp) {
          const newConflict: Conflict = {
            id: data.id,
            type: data.conflict_type,
            sessions: data.sessions,
            resource: data.resource,
            detected_at: data.timestamp,
            resolved: false,
            resolution_strategy: data.resolution_strategy || null
          }
          setConflicts(prev => [newConflict, ...prev])
          toast.error(`Conflict detected: ${data.resource}`)
        }
        break

      case "conflict_resolved":
        if (data.conflict_id) {
          setConflicts(prev =>
            prev.map(c => c.id === data.conflict_id ? { ...c, resolved: true } : c)
          )
          toast.success(`Conflict resolved: ${data.conflict_id}`)
        }
        break

      case "file_changed":
        setRealTimeUpdates(prev => [{
          ...data,
          timestamp: new Date().toISOString()
        }, ...prev.slice(0, 9)])
        break
    }
  }

  const resolveConflict = (conflictId: string, resolution: string) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: "conflict_resolved",
        conflict_id: conflictId,
        resolution
      }))
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "text-green-400 bg-green-500/20"
      case "idle": return "text-yellow-400 bg-yellow-500/20"
      case "locked": return "text-red-400 bg-red-500/20"
      case "waiting": return "text-blue-400 bg-blue-500/20"
      default: return "text-gray-400 bg-gray-500/20"
    }
  }

  const getConflictIcon = (type: string) => {
    switch (type) {
      case "file_edit": return <FileEdit className="h-4 w-4" />
      case "git_merge": return <GitBranch className="h-4 w-4" />
      case "resource_lock": return <Lock className="h-4 w-4" />
      default: return <AlertTriangle className="h-4 w-4" />
    }
  }

  const sessions = sessionsData?.sessions || []
  const activeCount = sessions.filter((s: Session) => s.status === "active").length
  const unresolvedConflicts = conflicts.filter(c => !c.resolved)

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Users className="h-6 w-6 text-purple-400" />
            <h2 className="text-xl font-bold text-white">Session Monitor</h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-green-500/20">
              <Activity className="h-4 w-4 text-green-400" />
              <span className="text-sm text-green-400">{activeCount} Active</span>
            </div>
            {unresolvedConflicts.length > 0 && (
              <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-red-500/20">
                <AlertTriangle className="h-4 w-4 text-red-400" />
                <span className="text-sm text-red-400">{unresolvedConflicts.length} Conflicts</span>
              </div>
            )}
            <button
              onClick={() => refetch()}
              className="p-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              <RefreshCcw className="h-4 w-4 text-gray-400" />
            </button>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Sessions */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Terminal className="h-5 w-5 text-purple-400" />
            Active Sessions
          </h3>

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 text-purple-400 animate-spin" />
            </div>
          ) : sessions.length > 0 ? (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {sessions.map((session: Session) => (
                <motion.div
                  key={session.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="p-3 rounded-lg bg-gray-900/50 border border-gray-700"
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white">
                          {session.terminal_id.substr(0, 12)}...
                        </span>
                        {session.is_primary && (
                          <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded">
                            Primary
                          </span>
                        )}
                        <span className={cn(
                          "px-2 py-0.5 text-xs rounded",
                          getStatusColor(session.status)
                        )}>
                          {session.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-400">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {new Date(session.started_at).toLocaleTimeString()}
                        </span>
                        {session.current_branch && (
                          <span className="flex items-center gap-1">
                            <GitBranch className="h-3 w-3" />
                            {session.current_branch}
                          </span>
                        )}
                      </div>
                    </div>
                    {session.locks.length > 0 && (
                      <div className="flex items-center gap-1">
                        <Lock className="h-4 w-4 text-yellow-400" />
                        <span className="text-xs text-yellow-400">{session.locks.length}</span>
                      </div>
                    )}
                  </div>
                  {session.locks.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {session.locks.map((lock, idx) => (
                        <div key={idx} className="text-xs text-gray-500 pl-4">
                          • {lock.type}: {lock.resource}
                        </div>
                      ))}
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              No active sessions
            </div>
          )}
        </motion.div>

        {/* Conflicts & Real-time Updates */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-400" />
            Conflicts & Updates
          </h3>

          {/* Conflicts */}
          {unresolvedConflicts.length > 0 && (
            <div className="mb-4 space-y-2">
              <h4 className="text-sm font-medium text-red-400">Active Conflicts</h4>
              {unresolvedConflicts.map((conflict) => (
                <motion.div
                  key={conflict.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="p-3 rounded-lg bg-red-500/10 border border-red-500/20"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getConflictIcon(conflict.type)}
                      <span className="text-sm text-white">{conflict.resource}</span>
                    </div>
                    <button
                      onClick={() => resolveConflict(conflict.id, "manual")}
                      className="px-2 py-1 text-xs bg-green-500/20 text-green-400 rounded hover:bg-green-500/30"
                    >
                      Resolve
                    </button>
                  </div>
                  <div className="mt-2 text-xs text-gray-400">
                    Sessions: {conflict.sessions.map(s => s.substr(0, 8)).join(", ")}
                  </div>
                  {conflict.resolution_strategy && (
                    <div className="mt-1 text-xs text-yellow-400">
                      Strategy: {conflict.resolution_strategy}
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}

          {/* Real-time Updates */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-400">Recent Activity</h4>
            <div className="space-y-1 max-h-64 overflow-y-auto">
              <AnimatePresence>
                {realTimeUpdates.map((update, idx) => (
                  <motion.div
                    key={`${update.type}_${update.timestamp}_${idx}`}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                    className="text-xs text-gray-500 flex items-center gap-2"
                  >
                    {update.type === "lock_acquired" && (
                      <>
                        <Lock className="h-3 w-3 text-yellow-400" />
                        <span>Lock acquired: {String(update.resource_id || '')}</span>
                      </>
                    )}
                    {update.type === "lock_released" && (
                      <>
                        <CheckCircle2 className="h-3 w-3 text-green-400" />
                        <span>Lock released: {String(update.resource_id || '')}</span>
                      </>
                    )}
                    {update.type === "file_changed" && (
                      <>
                        <FileEdit className="h-3 w-3 text-blue-400" />
                        <span>{String(update.change_type || '')}: {String(update.file_path || '')}</span>
                      </>
                    )}
                    <span className="text-gray-600 ml-auto">
                      {new Date(String(update.timestamp || Date.now())).toLocaleTimeString()}
                    </span>
                  </motion.div>
                ))}
              </AnimatePresence>
              {realTimeUpdates.length === 0 && (
                <div className="text-center py-4 text-gray-600">
                  No recent activity
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

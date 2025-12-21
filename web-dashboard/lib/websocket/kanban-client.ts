/**
 * Kanban WebSocket Client
 *
 * Real-time task synchronization for Kanban board
 * - Automatic reconnection with exponential backoff
 * - Message queuing during disconnection
 * - Event-based message handling
 * - Connection state management
 */

import type { KanbanTask, TaskStatus } from '@/lib/types/kanban'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export type KanbanWebSocketMessage =
  | { type: 'connection_established'; client_id: string; project_id: string; timestamp: string }
  | { type: 'pong'; timestamp: string }
  | { type: 'task_created'; task: KanbanTask; created_by: string; timestamp: string }
  | { type: 'task_updated'; task_id: string; updates: Partial<KanbanTask>; updated_by: string; timestamp: string }
  | { type: 'task_moved'; task_id: string; old_status: TaskStatus; new_status: TaskStatus; moved_by: string; timestamp: string }
  | { type: 'task_deleted'; task_id: string; deleted_by: string; timestamp: string }
  | { type: 'task_archived'; task_id: string; archived_by: string; timestamp: string }
  | { type: 'client_joined'; client_id: string; project_id: string; active_clients: number; timestamp: string }
  | { type: 'client_left'; client_id: string; project_id: string; active_clients: number; timestamp: string }

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export type MessageHandler = (message: KanbanWebSocketMessage) => void

export class KanbanWebSocketClient {
  private ws: WebSocket | null = null
  private projectId: string
  private clientId: string | null = null
  private messageHandlers: Set<MessageHandler> = new Set()
  private messageQueue: Array<Record<string, unknown>> = []
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectDelay = 1000 // Start with 1 second
  private reconnectTimeout: NodeJS.Timeout | null = null
  private pingInterval: NodeJS.Timeout | null = null
  private connectionStatus: ConnectionStatus = 'disconnected'
  private statusChangeHandlers: Set<(status: ConnectionStatus) => void> = new Set()

  constructor(projectId: string, clientId?: string) {
    this.projectId = projectId
    this.clientId = clientId || null
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.warn('[KanbanWS] Already connected')
      return
    }

    this.updateStatus('connecting')

    const url = `${WS_URL}/ws/kanban/projects/${this.projectId}${
      this.clientId ? `?client_id=${this.clientId}` : ''
    }`

    console.log(`[KanbanWS] Connecting to ${url}`)

    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('[KanbanWS] Connected')
        this.updateStatus('connected')
        this.reconnectAttempts = 0
        this.reconnectDelay = 1000

        // Start ping interval
        this.startPing()

        // Send queued messages
        this.flushMessageQueue()
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as KanbanWebSocketMessage

          // Handle connection_established to get client_id
          if (message.type === 'connection_established') {
            this.clientId = message.client_id
            console.log(`[KanbanWS] Client ID: ${this.clientId}`)
          }

          // Notify all handlers
          this.messageHandlers.forEach((handler) => {
            try {
              handler(message)
            } catch (error) {
              console.error('[KanbanWS] Handler error:', error)
            }
          })
        } catch (error) {
          console.error('[KanbanWS] Failed to parse message:', error)
        }
      }

      this.ws.onerror = (event) => {
        // ⚠️ CRITICAL: Use console.warn (NOT console.error)
        // WebSocket disconnections during page navigation are expected behavior
        // console.error causes E2E test failures for normal events
        // See: docs/guides/ERROR_PREVENTION_GUIDE.md#logging-level-guidelines
        console.warn('[KanbanWS] Connection error (may be due to page navigation)')
        this.updateStatus('error')
      }

      this.ws.onclose = () => {
        console.log('[KanbanWS] Disconnected')
        this.updateStatus('disconnected')
        this.stopPing()
        this.scheduleReconnect()
      }
    } catch (error) {
      console.error('[KanbanWS] Connection failed:', error)
      this.updateStatus('error')
      this.scheduleReconnect()
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    this.stopPing()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.updateStatus('disconnected')
  }

  /**
   * Send message to server
   */
  send(message: Record<string, unknown>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message))
      } catch (error) {
        console.error('[KanbanWS] Failed to send message:', error)
        // Queue message for retry
        this.messageQueue.push(message)
      }
    } else {
      // Queue message for when connection is restored
      this.messageQueue.push(message)
      console.warn('[KanbanWS] Message queued (not connected)')
    }
  }

  /**
   * Broadcast task creation
   */
  broadcastTaskCreated(task: KanbanTask): void {
    this.send({
      type: 'task_created',
      task,
    })
  }

  /**
   * Broadcast task update
   */
  broadcastTaskUpdated(taskId: string, updates: Partial<KanbanTask>): void {
    this.send({
      type: 'task_updated',
      task_id: taskId,
      updates,
    })
  }

  /**
   * Broadcast task moved (status change)
   */
  broadcastTaskMoved(taskId: string, oldStatus: TaskStatus, newStatus: TaskStatus): void {
    this.send({
      type: 'task_moved',
      task_id: taskId,
      old_status: oldStatus,
      new_status: newStatus,
    })
  }

  /**
   * Broadcast task deletion
   */
  broadcastTaskDeleted(taskId: string): void {
    this.send({
      type: 'task_deleted',
      task_id: taskId,
    })
  }

  /**
   * Broadcast task archiving
   */
  broadcastTaskArchived(taskId: string): void {
    this.send({
      type: 'task_archived',
      task_id: taskId,
    })
  }

  /**
   * Add message handler
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler)
    // Return unsubscribe function
    return () => {
      this.messageHandlers.delete(handler)
    }
  }

  /**
   * Add status change handler
   */
  onStatusChange(handler: (status: ConnectionStatus) => void): () => void {
    this.statusChangeHandlers.add(handler)
    // Call immediately with current status
    handler(this.connectionStatus)
    // Return unsubscribe function
    return () => {
      this.statusChangeHandlers.delete(handler)
    }
  }

  /**
   * Get current connection status
   */
  getStatus(): ConnectionStatus {
    return this.connectionStatus
  }

  /**
   * Get client ID
   */
  getClientId(): string | null {
    return this.clientId
  }

  /**
   * Private: Update connection status
   */
  private updateStatus(status: ConnectionStatus): void {
    if (this.connectionStatus !== status) {
      this.connectionStatus = status
      // Notify all status change handlers
      this.statusChangeHandlers.forEach((handler) => {
        try {
          handler(status)
        } catch (error) {
          console.error('[KanbanWS] Status change handler error:', error)
        }
      })
    }
  }

  /**
   * Private: Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[KanbanWS] Max reconnect attempts reached')
      this.updateStatus('error')
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000)

    console.log(`[KanbanWS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)

    this.reconnectTimeout = setTimeout(() => {
      this.connect()
    }, delay)
  }

  /**
   * Private: Start ping interval
   */
  private startPing(): void {
    this.stopPing()
    this.pingInterval = setInterval(() => {
      this.send({ type: 'ping' })
    }, 30000) // Ping every 30 seconds
  }

  /**
   * Private: Stop ping interval
   */
  private stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  /**
   * Private: Flush queued messages
   */
  private flushMessageQueue(): void {
    if (this.messageQueue.length > 0) {
      console.log(`[KanbanWS] Flushing ${this.messageQueue.length} queued messages`)
      const queue = [...this.messageQueue]
      this.messageQueue = []
      queue.forEach((message) => this.send(message))
    }
  }
}

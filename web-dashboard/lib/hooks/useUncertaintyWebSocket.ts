/**
 * useUncertaintyWebSocket - Real-time WebSocket hook for Uncertainty updates
 *
 * Features:
 * - Auto-connect on mount
 * - Auto-reconnect on disconnect (exponential backoff)
 * - Heartbeat/ping-pong for connection health
 * - Integration with uncertainty store
 */

import { useEffect, useRef, useCallback } from 'react'
import { useUncertaintyStore } from '@/lib/stores/uncertainty-store'
import type { UncertaintyStatusResponse } from '@/types/uncertainty'

interface WebSocketConfig {
  url?: string
  sessionId?: string
  projectId?: string
  autoConnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  heartbeatInterval?: number
}

const DEFAULT_CONFIG: Required<Omit<WebSocketConfig, 'url' | 'sessionId' | 'projectId'>> = {
  autoConnect: true,
  reconnectInterval: 3000, // 3 seconds
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000, // 30 seconds
}

export function useUncertaintyWebSocket(config: WebSocketConfig = {}) {
  const {
    url = `ws://localhost:8000/ws/uncertainty`,
    sessionId = `session-${Date.now()}`,
    projectId,
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
  } = { ...DEFAULT_CONFIG, ...config }

  // Refs
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)

  // Store actions
  const {
    setWsConnected,
    setWsError,
    handleWsUpdate,
  } = useUncertaintyStore()

  // Cleanup function
  const cleanup = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  // Send heartbeat ping
  const sendHeartbeat = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }))
    }
  }, [])

  // Start heartbeat interval
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
    }
    heartbeatIntervalRef.current = setInterval(sendHeartbeat, heartbeatInterval)
  }, [sendHeartbeat, heartbeatInterval])

  // Stop heartbeat interval
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
  }, [])

  // Reconnect with exponential backoff
  const reconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      setWsError(`Maximum reconnect attempts (${maxReconnectAttempts}) reached`)
      setWsConnected(false)
      return
    }

    reconnectAttemptsRef.current += 1
    const delay = reconnectInterval * Math.pow(2, reconnectAttemptsRef.current - 1)

    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`)

    reconnectTimeoutRef.current = setTimeout(() => {
      connect()
    }, delay)
  }, [maxReconnectAttempts, reconnectInterval, setWsError, setWsConnected])

  // Connect to WebSocket
  const connect = useCallback(() => {
    try {
      // Cleanup existing connection
      cleanup()

      // Build WebSocket URL with query params
      const wsUrl = new URL(url)
      wsUrl.searchParams.set('session_id', sessionId)
      if (projectId) {
        wsUrl.searchParams.set('project_id', projectId)
      }

      // Create WebSocket connection
      const ws = new WebSocket(wsUrl.toString())
      wsRef.current = ws

      // Connection opened
      ws.onopen = () => {
        console.log('WebSocket connected')
        setWsConnected(true)
        setWsError(null)
        reconnectAttemptsRef.current = 0 // Reset reconnect counter
        startHeartbeat()
      }

      // Message received
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)

          // Handle different message types
          switch (message.type) {
            case 'pong':
              // Heartbeat response
              break

            case 'uncertainty_update':
              // Uncertainty status update
              if (message.data) {
                handleWsUpdate(message.data as UncertaintyStatusResponse)
              }
              break

            case 'error':
              console.error('WebSocket error message:', message.error)
              setWsError(message.error)
              break

            default:
              console.log('Unknown message type:', message.type)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      // Connection closed
      ws.onclose = (event) => {
        console.log(`WebSocket closed (code: ${event.code})`)
        setWsConnected(false)
        stopHeartbeat()

        // Attempt reconnect if not a normal closure
        if (event.code !== 1000 && autoConnect) {
          reconnect()
        }
      }

      // Connection error
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setWsError('WebSocket connection error')
        setWsConnected(false)
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      setWsError('Failed to create WebSocket connection')
      setWsConnected(false)
    }
  }, [url, sessionId, projectId, autoConnect, cleanup, setWsConnected, setWsError, handleWsUpdate, startHeartbeat, stopHeartbeat, reconnect])

  // Send message to WebSocket
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
      return true
    } else {
      console.warn('WebSocket not connected, cannot send message')
      return false
    }
  }, [])

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    cleanup()
    setWsConnected(false)
  }, [cleanup, setWsConnected])

  // Effect: Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    // Cleanup on unmount
    return () => {
      cleanup()
    }
  }, [autoConnect, connect, cleanup])

  return {
    connect,
    disconnect,
    sendMessage,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  }
}

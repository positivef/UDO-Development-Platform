/**
 * useUncertaintyWebSocket - Real-time WebSocket hook for Uncertainty updates
 *
 * Features:
 * - Auto-connect on mount
 * - Auto-reconnect on disconnect (exponential backoff)
 * - Heartbeat/ping-pong for connection health
 * - Integration with uncertainty store
 * - JWT token authentication
 */

import { useEffect, useRef, useCallback } from 'react'
import { useUncertaintyStore } from '@/lib/stores/uncertainty-store'
import { getAuthToken, isDevelopmentMode } from '@/lib/auth/token-utils'
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
  // Use useRef for sessionId to ensure stability across re-renders
  const sessionIdRef = useRef(config.sessionId || `session-${Date.now()}`)

  const {
    url = `ws://localhost:8000/ws/uncertainty`,
    projectId,
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
  } = { ...DEFAULT_CONFIG, ...config }

  // Use stable sessionId from ref
  const sessionId = sessionIdRef.current

  // Refs
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const isMountedRef = useRef(true) // Track if component is mounted

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
      // Use code 1000 for normal closure to prevent error logs
      if (wsRef.current.readyState === WebSocket.OPEN ||
          wsRef.current.readyState === WebSocket.CONNECTING) {
        wsRef.current.close(1000, 'Component unmounted')
      }
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

  // Ref to hold the connect function for stable reference
  const connectRef = useRef<() => void>(() => {})

  // Connect to WebSocket (defined first, then stored in ref)
  const connectImpl = useCallback(() => {
    try {
      // Cleanup existing connection inline to avoid dependency
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

      // Build WebSocket URL with query params
      const wsUrl = new URL(url)
      wsUrl.searchParams.set('session_id', sessionId)
      if (projectId) {
        wsUrl.searchParams.set('project_id', projectId)
      }

      // Add authentication token
      const token = getAuthToken()
      if (token) {
        wsUrl.searchParams.set('token', token)
      } else if (!isDevelopmentMode()) {
        console.warn('[UncertaintyWS] No auth token available, connection may fail')
      }

      // Create WebSocket connection
      console.log(`[UncertaintyWS] Connecting to ${wsUrl.toString().replace(/token=.*?(&|$)/, 'token=***$1')}`)
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

      // Connection closed - use ref to avoid circular dependency
      ws.onclose = (event) => {
        // Don't log or reconnect if component is unmounted
        if (!isMountedRef.current) {
          return
        }

        console.log(`[UncertaintyWS] WebSocket closed (code: ${event.code})`)
        setWsConnected(false)
        stopHeartbeat()

        // Attempt reconnect if not a normal closure and component is still mounted
        if (event.code !== 1000 && autoConnect && isMountedRef.current) {
          if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
            setWsError(`Maximum reconnect attempts (${maxReconnectAttempts}) reached`)
            setWsConnected(false)
            return
          }

          reconnectAttemptsRef.current += 1
          const delay = reconnectInterval * Math.pow(2, reconnectAttemptsRef.current - 1)

          console.log(`[UncertaintyWS] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`)

          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              connectRef.current()
            }
          }, delay)
        }
      }

      // Connection error
      ws.onerror = (error) => {
        // Don't log if component is unmounted
        if (!isMountedRef.current) {
          return
        }
        console.error('[UncertaintyWS] WebSocket error event:', error)
        console.error('[UncertaintyWS] WebSocket readyState:', ws.readyState)
        console.error('[UncertaintyWS] WebSocket URL:', wsUrl.toString().replace(/token=.*?(&|$)/, 'token=***$1'))
        setWsError('WebSocket connection error')
        setWsConnected(false)
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      setWsError('Failed to create WebSocket connection')
      setWsConnected(false)
    }
  }, [url, sessionId, projectId, autoConnect, maxReconnectAttempts, reconnectInterval, setWsConnected, setWsError, handleWsUpdate, startHeartbeat, stopHeartbeat])

  // Update the ref when connect changes
  useEffect(() => {
    connectRef.current = connectImpl
  }, [connectImpl])

  // Stable connect function that uses the ref
  const connect = useCallback(() => {
    connectRef.current()
  }, [])

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
  // Using a ref pattern to avoid infinite re-renders from connect dependency
  useEffect(() => {
    if (autoConnect) {
      // Use setTimeout to ensure connectRef is populated
      const timeoutId = setTimeout(() => {
        if (isMountedRef.current) {
          connectRef.current()
        }
      }, 0)
      return () => clearTimeout(timeoutId)
    }
  }, [autoConnect, url, projectId]) // Note: sessionId is now stable via ref

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
      cleanup()
    }
  }, [cleanup])

  return {
    connect,
    disconnect,
    sendMessage,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  }
}

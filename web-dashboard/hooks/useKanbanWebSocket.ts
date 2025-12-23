'use client';

import { useEffect, useCallback, useRef } from 'react';
import { useToast } from '@/hooks/use-toast';
import type { ConnectionStatus } from '@/lib/websocket/kanban-client';

interface WebSocketMessage {
  type: 'task_created' | 'task_updated' | 'task_deleted' | 'task_archived' | 'task_moved' | 'dependency_changed';
  task_id: string;
  data: any;
  user?: string;
}

interface UseKanbanWebSocketProps {
  projectId?: string;
  enabled?: boolean;
  onStatusChange?: (status: ConnectionStatus) => void;
  onMessage?: (message: any) => void;
  onTaskCreated?: (data: any) => void;
  onTaskUpdated?: (data: any) => void;
  onTaskDeleted?: (taskId: string) => void;
  onTaskArchived?: (data: any) => void;
  onDependencyChanged?: (data: any) => void;
}

export function useKanbanWebSocket({
  projectId,
  enabled = true,
  onStatusChange,
  onMessage,
  onTaskCreated,
  onTaskUpdated,
  onTaskDeleted,
  onTaskArchived,
  onDependencyChanged,
}: UseKanbanWebSocketProps = {}) {
  const { toast } = useToast();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const isConnectingRef = useRef(false);

  // Store callbacks in refs to prevent connect from being recreated
  const onStatusChangeRef = useRef(onStatusChange);
  const onTaskCreatedRef = useRef(onTaskCreated);
  const onTaskUpdatedRef = useRef(onTaskUpdated);
  const onTaskDeletedRef = useRef(onTaskDeleted);
  const onTaskArchivedRef = useRef(onTaskArchived);
  const onDependencyChangedRef = useRef(onDependencyChanged);

  // Update refs when callbacks change
  useEffect(() => {
    onStatusChangeRef.current = onStatusChange;
    onTaskCreatedRef.current = onTaskCreated;
    onTaskUpdatedRef.current = onTaskUpdated;
    onTaskDeletedRef.current = onTaskDeleted;
    onTaskArchivedRef.current = onTaskArchived;
    onDependencyChangedRef.current = onDependencyChanged;
  }, [onStatusChange, onTaskCreated, onTaskUpdated, onTaskDeleted, onTaskArchived, onDependencyChanged]);

  const connect = useCallback(() => {
    // Prevent duplicate connections
    if (isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[KanbanWS] Already connected or connecting, skipping...');
      return;
    }

    try {
      isConnectingRef.current = true;
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const defaultProjectId = projectId || 'default';
      // Use environment variable or default to 8000 (backend API port)
      const wsPort = process.env.NEXT_PUBLIC_WS_PORT || '8000';
      const wsUrl = `${protocol}//${window.location.hostname}:${wsPort}/ws/kanban/projects/${defaultProjectId}`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[KanbanWS] Connected');
        reconnectAttempts.current = 0;
        isConnectingRef.current = false;
        if (onStatusChangeRef.current) {
          onStatusChangeRef.current('connected');
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          // Handle connection/heartbeat messages
          if (message.type === 'connection_established' || message.type === 'pong') {
            return;
          }

          // Backend message format:
          // - task_created: { type, task, created_by, timestamp }
          // - task_updated: { type, task_id, updates, updated_by, timestamp }
          // - task_moved: { type, task_id, old_status, new_status, moved_by, timestamp }
          // - task_deleted: { type, task_id, deleted_by, timestamp }
          // - task_archived: { type, task_id, archived_by, timestamp }

          switch (message.type) {
            case 'task_created':
              if (onTaskCreatedRef.current) {
                onTaskCreatedRef.current(message.task);
              }
              toast({
                title: 'New Task Created',
                description: `Task created by another user`,
              });
              break;

            case 'task_updated':
              if (onTaskUpdatedRef.current) {
                onTaskUpdatedRef.current({
                  task_id: message.task_id,
                  updates: message.updates
                });
              }
              toast({
                title: 'Task Updated',
                description: `Task updated by another user`,
              });
              break;

            case 'task_moved':
              if (onTaskUpdatedRef.current) {
                onTaskUpdatedRef.current({
                  task_id: message.task_id,
                  updates: {
                    status: message.new_status,
                    old_status: message.old_status
                  }
                });
              }
              toast({
                title: 'Task Moved',
                description: `Task moved from ${message.old_status} to ${message.new_status}`,
              });
              break;

            case 'task_deleted':
              if (onTaskDeletedRef.current) {
                onTaskDeletedRef.current(message.task_id);
              }
              toast({
                title: 'Task Deleted',
                description: `Task deleted by another user`,
                variant: 'destructive',
              });
              break;

            case 'task_archived':
              if (onTaskArchivedRef.current) {
                onTaskArchivedRef.current({ task_id: message.task_id });
              }
              toast({
                title: 'Task Archived',
                description: `Task archived by another user`,
              });
              break;

            case 'client_joined':
              console.log(`[KanbanWS] Client joined:`, message.client_id);
              toast({
                title: 'User Joined',
                description: `Active users: ${message.active_clients}`,
              });
              break;

            case 'client_left':
              console.log(`[KanbanWS] Client left:`, message.client_id);
              break;

            default:
              console.warn('[KanbanWS] Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('[KanbanWS] Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[KanbanWS] Error:', error);
        isConnectingRef.current = false;
        if (onStatusChangeRef.current) {
          onStatusChangeRef.current('error');
        }
      };

      ws.onclose = () => {
        console.log('[KanbanWS] Disconnected');
        isConnectingRef.current = false;
        if (onStatusChangeRef.current) {
          onStatusChangeRef.current('disconnected');
        }

        // Only reconnect if enabled
        if (!enabled) {
          console.log('[KanbanWS] Reconnection disabled');
          return;
        }

        // Exponential backoff reconnection
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current += 1;

        if (reconnectAttempts.current <= 10) {
          console.log(`[KanbanWS] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);
          if (onStatusChangeRef.current) {
            onStatusChangeRef.current('connecting');
          }
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      };

    } catch (error) {
      console.error('[KanbanWS] Failed to connect:', error);
      isConnectingRef.current = false;
    }
  }, [projectId, enabled, toast]);

  useEffect(() => {
    if (!enabled) {
      console.log('[KanbanWS] WebSocket disabled');
      return;
    }

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      isConnectingRef.current = false;
    };
  }, [projectId, enabled, connect]);

  const broadcastTaskCreated = useCallback((taskData: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'task_created',
        task: taskData,
      }));
    }
  }, []);

  const broadcastTaskUpdated = useCallback((taskId: string, updates: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'task_updated',
        task_id: taskId,
        updates: updates,
      }));
    }
  }, []);

  const broadcastTaskDeleted = useCallback((taskId: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'task_deleted',
        task_id: taskId,
      }));
    }
  }, []);

  const broadcastTaskArchived = useCallback((taskId: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'task_archived',
        task_id: taskId,
      }));
    }
  }, []);

  const broadcastTaskMoved = useCallback((taskId: string, oldStatus: string, newStatus: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'task_moved',
        task_id: taskId,
        old_status: oldStatus,
        new_status: newStatus,
      }));
    }
  }, []);

  return {
    broadcastTaskCreated,
    broadcastTaskUpdated,
    broadcastTaskMoved,
    broadcastTaskDeleted,
    broadcastTaskArchived,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
}

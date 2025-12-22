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

  const connect = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.hostname}:8081/ws/kanban`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[KanbanWS] Connected');
        reconnectAttempts.current = 0;
        if (onStatusChange) {
          onStatusChange('connected');
        }
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          switch (message.type) {
            case 'task_created':
              if (onTaskCreated) {
                onTaskCreated(message.data);
              }
              toast({
                title: 'New Task Created',
                description: `${message.user || 'Someone'} created a task`,
              });
              break;

            case 'task_updated':
              if (onTaskUpdated) {
                onTaskUpdated(message.data);
              }
              toast({
                title: 'Task Updated',
                description: `${message.user || 'Someone'} updated a task`,
              });
              break;

            case 'task_deleted':
              if (onTaskDeleted) {
                onTaskDeleted(message.task_id);
              }
              toast({
                title: 'Task Deleted',
                description: `${message.user || 'Someone'} deleted a task`,
                variant: 'destructive',
              });
              break;

            case 'task_archived':
              if (onTaskArchived) {
                onTaskArchived(message.data);
              }
              toast({
                title: 'Task Archived',
                description: `${message.user || 'Someone'} archived a task`,
              });
              break;

            case 'dependency_changed':
              if (onDependencyChanged) {
                onDependencyChanged(message.data);
              }
              toast({
                title: 'Dependencies Changed',
                description: `${message.user || 'Someone'} modified task dependencies`,
              });
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
        if (onStatusChange) {
          onStatusChange('error');
        }
      };

      ws.onclose = () => {
        console.log('[KanbanWS] Disconnected');
        if (onStatusChange) {
          onStatusChange('disconnected');
        }

        // Exponential backoff reconnection
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current += 1;

        if (reconnectAttempts.current <= 10) {
          console.log(`[KanbanWS] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);
          if (onStatusChange) {
            onStatusChange('connecting');
          }
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      };

    } catch (error) {
      console.error('[KanbanWS] Failed to connect:', error);
    }
  }, [onStatusChange, onTaskCreated, onTaskUpdated, onTaskDeleted, onTaskArchived, onDependencyChanged, toast]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const broadcastTaskCreated = useCallback((taskData: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'task_created',
        data: taskData,
      }));
    }
  }, []);

  const broadcastTaskUpdated = useCallback((taskData: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'task_updated',
        data: taskData,
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

  const broadcastTaskArchived = useCallback((taskData: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'task_archived',
        data: taskData,
      }));
    }
  }, []);

  const broadcastTaskMoved = useCallback((taskId: string, oldStatus: string, newStatus: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'task_moved',
        task_id: taskId,
        data: { oldStatus, newStatus },
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

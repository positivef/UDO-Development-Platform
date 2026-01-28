/**
 * Kanban WebSocket Hook (P0-3: Offline/Error Handling)
 *
 * React hook for real-time Kanban updates with automatic reconnection
 */

import { useEffect, useRef, useState } from 'react';
import {
  KanbanWebSocketClient,
  createKanbanWebSocketClient,
  ConnectionStatus,
  KanbanMessage,
  MessageHandler,
} from '../websocket/kanban-client';

export interface UseKanbanWebSocketOptions {
  url: string;
  enabled?: boolean;
  onMessage?: MessageHandler;
  onStatusChange?: (status: ConnectionStatus) => void;
}

export function useKanbanWebSocket(options: UseKanbanWebSocketOptions) {
  const { url, enabled = true, onMessage, onStatusChange } = options;
  const clientRef = useRef<KanbanWebSocketClient | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Create WebSocket client
    const client = createKanbanWebSocketClient(url);
    clientRef.current = client;

    // Subscribe to status changes
    const unsubscribeStatus = client.onStatusChange((newStatus) => {
      setStatus(newStatus);
      onStatusChange?.(newStatus);
    });

    // Subscribe to messages
    let unsubscribeMessage: (() => void) | undefined;
    if (onMessage) {
      unsubscribeMessage = client.onMessage(onMessage);
    }

    // Connect to server
    client.connect();

    // Cleanup on unmount
    return () => {
      unsubscribeStatus();
      unsubscribeMessage?.();
      client.destroy();
      clientRef.current = null;
    };
  }, [url, enabled, onMessage, onStatusChange]);

  return {
    status,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    isDisconnected: status === 'disconnected',
    hasError: status === 'error',
    send: (message: KanbanMessage) => clientRef.current?.send(message) ?? false,
  };
}

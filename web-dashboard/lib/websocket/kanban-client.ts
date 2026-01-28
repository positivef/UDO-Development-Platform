/**
 * Kanban WebSocket Client (P0-3: Offline/Error Handling)
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Connection status tracking
 * - Event-based messaging system
 * - Network resilience
 */

export type ConnectionStatus =
  | 'connected'
  | 'disconnected'
  | 'connecting'
  | 'error';

export type KanbanMessage = {
  type: 'task_created' | 'task_updated' | 'task_deleted' | 'task_moved';
  payload: unknown;
  timestamp: string;
};

export type MessageHandler = (message: KanbanMessage) => void;
export type StatusHandler = (status: ConnectionStatus) => void;

export interface KanbanWebSocketConfig {
  url: string;
  maxReconnectDelay?: number; // max 30s
  initialReconnectDelay?: number; // start 1s
  reconnectDecay?: number; // multiply by 2
}

export class KanbanWebSocketClient {
  private ws: WebSocket | null = null;
  private config: Required<KanbanWebSocketConfig>;
  private status: ConnectionStatus = 'disconnected';
  private reconnectAttempts = 0;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private statusHandlers: Set<StatusHandler> = new Set();
  private shouldReconnect = true;

  constructor(config: KanbanWebSocketConfig) {
    this.config = {
      url: config.url,
      maxReconnectDelay: config.maxReconnectDelay ?? 30000, // 30s max
      initialReconnectDelay: config.initialReconnectDelay ?? 1000, // 1s initial
      reconnectDecay: config.reconnectDecay ?? 2, // exponential backoff
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.warn('WebSocket already connected');
      return;
    }

    this.shouldReconnect = true;
    this.setStatus('connecting');

    try {
      this.ws = new WebSocket(this.config.url);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.setStatus('error');
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.shouldReconnect = false;
    this.clearReconnectTimeout();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.setStatus('disconnected');
  }

  /**
   * Send message to server
   */
  send(message: KanbanMessage): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected, cannot send message');
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }

  /**
   * Add message handler
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  /**
   * Add status handler
   */
  onStatusChange(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    handler(this.status); // Call immediately with current status
    return () => this.statusHandlers.delete(handler);
  }

  /**
   * Get current connection status
   */
  getStatus(): ConnectionStatus {
    return this.status;
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(): void {
    console.log('WebSocket connected');
    this.reconnectAttempts = 0;
    this.setStatus('connected');
  }

  /**
   * Handle WebSocket message event
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: KanbanMessage = JSON.parse(event.data);
      this.messageHandlers.forEach((handler) => handler(message));
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket error event
   */
  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    this.setStatus('error');
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(event: CloseEvent): void {
    console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
    this.ws = null;

    if (this.shouldReconnect) {
      this.setStatus('disconnected');
      this.scheduleReconnect();
    } else {
      this.setStatus('disconnected');
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    this.clearReconnectTimeout();

    // Calculate delay: 1s, 2s, 4s, 8s, 16s, max 30s
    const delay = Math.min(
      this.config.initialReconnectDelay * Math.pow(this.config.reconnectDecay, this.reconnectAttempts),
      this.config.maxReconnectDelay
    );

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  /**
   * Clear reconnect timeout
   */
  private clearReconnectTimeout(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  /**
   * Set connection status and notify handlers
   */
  private setStatus(status: ConnectionStatus): void {
    if (this.status !== status) {
      this.status = status;
      this.statusHandlers.forEach((handler) => handler(status));
    }
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.disconnect();
    this.messageHandlers.clear();
    this.statusHandlers.clear();
  }
}

/**
 * Create Kanban WebSocket client instance
 */
export function createKanbanWebSocketClient(url: string): KanbanWebSocketClient {
  return new KanbanWebSocketClient({ url });
}

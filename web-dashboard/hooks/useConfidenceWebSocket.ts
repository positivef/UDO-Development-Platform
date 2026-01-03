'use client';

/**
 * useConfidenceWebSocket - Real-time confidence updates via WebSocket
 *
 * Features:
 * - Real-time confidence score updates
 * - Phase threshold crossing notifications
 * - Decision change alerts (GO/NO_GO)
 * - Auto-reconnection with exponential backoff
 * - React Query cache invalidation
 */

import { useEffect, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface ConfidenceUpdate {
  type: 'confidence_updated' | 'threshold_crossed' | 'decision_changed';
  phase: string;
  confidence_score: number;
  previous_score?: number;
  decision: 'GO' | 'GO_WITH_CHECKPOINTS' | 'NO_GO';
  previous_decision?: 'GO' | 'GO_WITH_CHECKPOINTS' | 'NO_GO';
  threshold_crossed?: 'above' | 'below';
  timestamp: string;
}

interface UseConfidenceWebSocketProps {
  phase?: string;
  enabled?: boolean;
  onStatusChange?: (status: ConnectionStatus) => void;
  onConfidenceUpdate?: (update: ConfidenceUpdate) => void;
  onThresholdCrossed?: (update: ConfidenceUpdate) => void;
  onDecisionChanged?: (update: ConfidenceUpdate) => void;
}

export function useConfidenceWebSocket({
  phase = 'implementation',
  enabled = true,
  onStatusChange,
  onConfidenceUpdate,
  onThresholdCrossed,
  onDecisionChanged,
}: UseConfidenceWebSocketProps = {}) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const isConnectingRef = useRef(false);

  // Store callbacks in refs to prevent connect from being recreated
  const onStatusChangeRef = useRef(onStatusChange);
  const onConfidenceUpdateRef = useRef(onConfidenceUpdate);
  const onThresholdCrossedRef = useRef(onThresholdCrossed);
  const onDecisionChangedRef = useRef(onDecisionChanged);

  // Update refs when callbacks change
  useEffect(() => {
    onStatusChangeRef.current = onStatusChange;
    onConfidenceUpdateRef.current = onConfidenceUpdate;
    onThresholdCrossedRef.current = onThresholdCrossed;
    onDecisionChangedRef.current = onDecisionChanged;
  }, [onStatusChange, onConfidenceUpdate, onThresholdCrossed, onDecisionChanged]);

  const connect = useCallback(() => {
    // Prevent duplicate connections
    if (isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[ConfidenceWS] Already connected or connecting, skipping...');
      return;
    }

    try {
      isConnectingRef.current = true;
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsPort = process.env.NEXT_PUBLIC_WS_PORT || '8000';
      const wsUrl = `${protocol}//${window.location.hostname}:${wsPort}/ws/confidence/${phase}`;

      console.log(`[ConfidenceWS] Connecting to ${wsUrl}`);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[ConfidenceWS] Connected');
        reconnectAttempts.current = 0;
        isConnectingRef.current = false;
        if (onStatusChangeRef.current) {
          onStatusChangeRef.current('connected');
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as ConfidenceUpdate;

          // Handle connection/heartbeat messages
          if ((message as any).type === 'connection_established' || (message as any).type === 'pong') {
            return;
          }

          // Invalidate React Query cache on any update
          queryClient.invalidateQueries({ queryKey: ['confidence', phase] });

          switch (message.type) {
            case 'confidence_updated':
              if (onConfidenceUpdateRef.current) {
                onConfidenceUpdateRef.current(message);
              }
              break;

            case 'threshold_crossed':
              if (onThresholdCrossedRef.current) {
                onThresholdCrossedRef.current(message);
              }
              // Show toast for threshold crossing
              toast({
                title: message.threshold_crossed === 'above'
                  ? 'Threshold Reached!'
                  : 'Below Threshold',
                description: `Confidence ${message.threshold_crossed === 'above' ? 'exceeded' : 'dropped below'} ${phase} phase threshold`,
                variant: message.threshold_crossed === 'above' ? 'default' : 'destructive',
              });
              break;

            case 'decision_changed':
              if (onDecisionChangedRef.current) {
                onDecisionChangedRef.current(message);
              }
              // Show toast for decision change
              const decisionLabels = {
                GO: 'GO',
                GO_WITH_CHECKPOINTS: 'GO (Checkpoints)',
                NO_GO: 'NO GO',
              };
              toast({
                title: 'Decision Changed',
                description: `${message.previous_decision ? decisionLabels[message.previous_decision] + ' → ' : ''}${decisionLabels[message.decision]}`,
                variant: message.decision === 'NO_GO' ? 'destructive' : 'default',
              });
              break;

            default:
              console.warn('[ConfidenceWS] Unknown message type:', (message as any).type);
          }
        } catch (error) {
          console.error('[ConfidenceWS] Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[ConfidenceWS] Error:', error);
        isConnectingRef.current = false;
        if (onStatusChangeRef.current) {
          onStatusChangeRef.current('error');
        }
      };

      ws.onclose = () => {
        console.log('[ConfidenceWS] Disconnected');
        isConnectingRef.current = false;
        if (onStatusChangeRef.current) {
          onStatusChangeRef.current('disconnected');
        }

        // Only reconnect if enabled
        if (!enabled) {
          console.log('[ConfidenceWS] Reconnection disabled');
          return;
        }

        // Exponential backoff reconnection
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current += 1;

        if (reconnectAttempts.current <= 10) {
          console.log(`[ConfidenceWS] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);
          if (onStatusChangeRef.current) {
            onStatusChangeRef.current('connecting');
          }
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      };

    } catch (error) {
      console.error('[ConfidenceWS] Failed to connect:', error);
      isConnectingRef.current = false;
    }
  }, [phase, enabled, toast, queryClient]);

  useEffect(() => {
    if (!enabled) {
      console.log('[ConfidenceWS] WebSocket disabled');
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
  }, [phase, enabled, connect]);

  // Request a confidence recalculation
  const requestRecalculation = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'request_recalculation',
        phase: phase,
      }));
    }
  }, [phase]);

  // Subscribe to a specific phase
  const subscribeToPhase = useCallback((newPhase: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe_phase',
        phase: newPhase,
      }));
    }
  }, []);

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    requestRecalculation,
    subscribeToPhase,
    connectionStatus: wsRef.current?.readyState === WebSocket.OPEN
      ? 'connected'
      : wsRef.current?.readyState === WebSocket.CONNECTING
        ? 'connecting'
        : 'disconnected',
  };
}

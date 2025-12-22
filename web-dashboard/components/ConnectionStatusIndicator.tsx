'use client';

/**
 * ConnectionStatusIndicator - Week 7 Day 4 P1 Fix
 *
 * Features:
 * - Real-time WebSocket connection status
 * - Visual indicators (connected/disconnected/error)
 * - Active clients count (multi-user awareness)
 * - Pulse animation for connected state
 */

import React from 'react';
import { Wifi, WifiOff, AlertCircle, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { ConnectionStatus } from '@/lib/websocket/kanban-client';

interface ConnectionStatusIndicatorProps {
  status: ConnectionStatus;
  activeClients?: number;
}

export function ConnectionStatusIndicator({
  status,
  activeClients = 1,
}: ConnectionStatusIndicatorProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Wifi,
          label: 'Connected',
          variant: 'default' as const,
          className: 'bg-green-100 text-green-800 border-green-200',
          pulse: true,
        };
      case 'connecting':
        return {
          icon: Wifi,
          label: 'Connecting...',
          variant: 'secondary' as const,
          className: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          pulse: true,
        };
      case 'error':
        return {
          icon: AlertCircle,
          label: 'Error',
          variant: 'destructive' as const,
          className: 'bg-red-100 text-red-800 border-red-200',
          pulse: false,
        };
      case 'disconnected':
      default:
        return {
          icon: WifiOff,
          label: 'Disconnected',
          variant: 'outline' as const,
          className: 'bg-gray-100 text-gray-800 border-gray-200',
          pulse: false,
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-2">
      <Badge variant={config.variant} className={`${config.className} flex items-center gap-1`}>
        <Icon className={`h-3 w-3 ${config.pulse ? 'animate-pulse' : ''}`} />
        <span className="text-xs font-medium">{config.label}</span>
      </Badge>

      {status === 'connected' && activeClients > 1 && (
        <Badge variant="secondary" className="flex items-center gap-1">
          <Users className="h-3 w-3" />
          <span className="text-xs">{activeClients}</span>
        </Badge>
      )}
    </div>
  );
}

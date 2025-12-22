'use client';

/**
 * PartialFailureHandler - Week 7 Day 4 P1 Fix
 *
 * Features:
 * - Graceful degradation for partial API failures
 * - Shows success count and displays successful data
 * - Provides retry mechanism for failed requests
 * - User-friendly error notifications
 *
 * Use Case:
 * When fetching multiple tasks, if 90/100 succeed, show 90 and allow retry for 10.
 */

import React, { useState, useCallback } from 'react';
import { AlertCircle, RefreshCw, CheckCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

export interface PartialFailureResult<T> {
  successful: T[];
  failed: Array<{ id: string; error: string }>;
  totalAttempted: number;
}

interface PartialFailureHandlerProps<T> {
  result: PartialFailureResult<T> | null;
  onRetry?: (failedIds: string[]) => Promise<void>;
  children: (data: T[]) => React.ReactNode;
  loadingMessage?: string;
  noDataMessage?: string;
}

export function PartialFailureHandler<T>({
  result,
  onRetry,
  children,
  loadingMessage = 'Loading...',
  noDataMessage = 'No data available',
}: PartialFailureHandlerProps<T>) {
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = useCallback(async () => {
    if (!result || !onRetry || result.failed.length === 0) return;

    setIsRetrying(true);
    try {
      const failedIds = result.failed.map((f) => f.id);
      await onRetry(failedIds);
    } catch (error) {
      console.error('[PartialFailureHandler] Retry failed:', error);
    } finally {
      setIsRetrying(false);
    }
  }, [result, onRetry]);

  // Loading state
  if (!result) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-sm text-muted-foreground">{loadingMessage}</p>
      </div>
    );
  }

  // No data state
  if (result.successful.length === 0 && result.failed.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-sm text-muted-foreground">{noDataMessage}</p>
      </div>
    );
  }

  // Partial failure state
  const hasFailures = result.failed.length > 0;
  const successRate = ((result.successful.length / result.totalAttempted) * 100).toFixed(0);

  return (
    <div className="space-y-4">
      {/* Success/Failure Summary Alert */}
      {hasFailures && (
        <Alert variant={result.successful.length > 0 ? 'default' : 'destructive'}>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>
            {result.successful.length > 0 ? 'Partial Success' : 'All Requests Failed'}
          </AlertTitle>
          <AlertDescription className="mt-2 space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-sm">
                {result.successful.length} / {result.totalAttempted} succeeded ({successRate}%)
              </span>
            </div>

            {result.failed.length > 0 && (
              <div className="text-sm text-muted-foreground">
                Failed: {result.failed.map((f) => f.id).join(', ')}
              </div>
            )}

            {onRetry && result.failed.length > 0 && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleRetry}
                disabled={isRetrying}
                className="mt-2"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isRetrying ? 'animate-spin' : ''}`} />
                {isRetrying ? 'Retrying...' : `Retry ${result.failed.length} failed`}
              </Button>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Render successful data */}
      {result.successful.length > 0 && children(result.successful)}

      {/* Total failure state (no successful data to show) */}
      {result.successful.length === 0 && result.failed.length > 0 && (
        <div className="flex flex-col items-center justify-center p-8 space-y-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <p className="text-sm text-muted-foreground text-center">
            Unable to load any data. Please try again.
          </p>
          {onRetry && (
            <Button onClick={handleRetry} disabled={isRetrying} variant="destructive">
              <RefreshCw className={`h-4 w-4 mr-2 ${isRetrying ? 'animate-spin' : ''}`} />
              {isRetrying ? 'Retrying...' : 'Retry All'}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

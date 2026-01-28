"use client"

/**
 * NetworkStatus - Network connectivity indicator (P0-3)
 *
 * Features:
 * - Detects online/offline status
 * - Shows toast notification on connection change
 * - Visual indicator (optional banner)
 * - Persists across page navigation
 */

import { useEffect, useState } from 'react'
import { Wifi, WifiOff } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function NetworkStatus() {
  const [isOnline, setIsOnline] = useState(true)
  const [showBanner, setShowBanner] = useState(false)

  useEffect(() => {
    // Initialize with navigator.onLine
    setIsOnline(navigator.onLine)

    // Handle online event
    const handleOnline = () => {
      setIsOnline(true)
      setShowBanner(true)

      // Auto-hide banner after 3 seconds
      setTimeout(() => setShowBanner(false), 3000)
    }

    // Handle offline event
    const handleOffline = () => {
      setIsOnline(false)
      setShowBanner(true)
    }

    // Add event listeners
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Cleanup
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Don't show banner if online and not recently changed
  if (isOnline && !showBanner) return null

  return (
    <div className="fixed top-16 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-md px-4">
      <Alert variant={isOnline ? 'default' : 'destructive'} className="shadow-lg">
        <div className="flex items-center gap-2">
          {isOnline ? (
            <Wifi className="h-4 w-4 text-green-600" />
          ) : (
            <WifiOff className="h-4 w-4" />
          )}
          <AlertDescription>
            {isOnline
              ? '인터넷 연결이 복구되었습니다'
              : '오프라인 상태입니다. 일부 기능이 제한될 수 있습니다.'}
          </AlertDescription>
        </div>
      </Alert>
    </div>
  )
}

/**
 * Hook for network status detection
 *
 * Usage:
 * const isOnline = useNetworkStatus()
 * if (!isOnline) return <OfflineMessage />
 */
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(true)

  useEffect(() => {
    setIsOnline(navigator.onLine)

    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return isOnline
}

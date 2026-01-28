'use client';

/**
 * Service Worker Provider (P0-3: Offline/Error Handling)
 *
 * Registers service worker for offline support
 */

import { useEffect } from 'react';
import { registerServiceWorker } from '@/lib/utils/service-worker-registration';
import { toast } from 'sonner';

export function ServiceWorkerProvider() {
  useEffect(() => {
    registerServiceWorker({
      onSuccess: () => {
        console.log('[App] Service worker registered successfully');
      },
      onUpdate: () => {
        console.log('[App] New service worker version available');
        toast.info('새로운 버전이 있습니다', {
          description: '페이지를 새로고침하면 최신 버전을 사용할 수 있습니다.',
          action: {
            label: '새로고침',
            onClick: () => window.location.reload(),
          },
          duration: 10000,
        });
      },
      onError: (error) => {
        console.error('[App] Service worker registration error:', error);
      },
    });
  }, []);

  return null;
}

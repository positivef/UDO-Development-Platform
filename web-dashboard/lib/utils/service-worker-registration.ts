/**
 * Service Worker Registration Utility (P0-3: Offline/Error Handling)
 *
 * Registers the service worker for offline support
 */

export interface ServiceWorkerRegistrationConfig {
  onSuccess?: (registration: ServiceWorkerRegistration) => void;
  onUpdate?: (registration: ServiceWorkerRegistration) => void;
  onError?: (error: Error) => void;
}

export function registerServiceWorker(config: ServiceWorkerRegistrationConfig = {}) {
  // Only register in production or when explicitly enabled
  const isProduction = process.env.NODE_ENV === 'production';
  const isEnabled = process.env.NEXT_PUBLIC_ENABLE_SW === 'true';

  if (!isProduction && !isEnabled) {
    console.log('[Service Worker] Registration skipped (not in production)');
    return;
  }

  // Check if service workers are supported
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    console.warn('[Service Worker] Not supported in this browser');
    return;
  }

  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js')
      .then((registration) => {
        console.log('[Service Worker] Registered successfully:', registration.scope);

        // Check for updates
        registration.onupdatefound = () => {
          const installingWorker = registration.installing;
          if (installingWorker == null) {
            return;
          }

          installingWorker.onstatechange = () => {
            if (installingWorker.state === 'installed') {
              if (navigator.serviceWorker.controller) {
                // New service worker available
                console.log('[Service Worker] New version available');
                config.onUpdate?.(registration);
              } else {
                // First install
                console.log('[Service Worker] Content cached for offline use');
                config.onSuccess?.(registration);
              }
            }
          };
        };
      })
      .catch((error) => {
        console.error('[Service Worker] Registration failed:', error);
        config.onError?.(error);
      });
  });
}

export function unregisterServiceWorker() {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  navigator.serviceWorker.ready
    .then((registration) => {
      registration.unregister();
      console.log('[Service Worker] Unregistered successfully');
    })
    .catch((error) => {
      console.error('[Service Worker] Unregistration failed:', error);
    });
}

export function updateServiceWorker() {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  navigator.serviceWorker.ready
    .then((registration) => {
      registration.update();
      console.log('[Service Worker] Update check initiated');
    })
    .catch((error) => {
      console.error('[Service Worker] Update check failed:', error);
    });
}

export function sendMessageToServiceWorker(message: { type: string; [key: string]: unknown }) {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  navigator.serviceWorker.ready
    .then((registration) => {
      registration.active?.postMessage(message);
    })
    .catch((error) => {
      console.error('[Service Worker] Message send failed:', error);
    });
}

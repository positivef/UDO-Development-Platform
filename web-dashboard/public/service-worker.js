/**
 * Service Worker for UDO Development Platform (P0-3: Offline/Error Handling)
 *
 * Features:
 * - Offline caching for essential resources
 * - Network-first strategy for API calls
 * - Cache-first strategy for static assets
 */

const CACHE_NAME = 'udo-v1';
const STATIC_CACHE_NAME = 'udo-static-v1';

// Essential resources to cache on install
const ESSENTIAL_RESOURCES = [
  '/',
  '/kanban',
  '/quality',
  '/time-tracking',
  '/governance',
  '/uncertainty',
  '/confidence',
  '/archive',
];

// Install event - cache essential resources
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');

  event.waitUntil(
    caches.open(STATIC_CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Caching essential resources');
      return cache.addAll(ESSENTIAL_RESOURCES);
    })
  );

  self.skipWaiting();
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== STATIC_CACHE_NAME)
          .map((name) => {
            console.log('[Service Worker] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    })
  );

  self.clients.claim();
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // API calls - Network-first strategy
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone response for caching
          const responseToCache = response.clone();

          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseToCache);
          });

          return response;
        })
        .catch(() => {
          // Fallback to cache if network fails
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              console.log('[Service Worker] Serving cached API response:', url.pathname);
              return cachedResponse;
            }

            // Return offline response for API calls
            return new Response(
              JSON.stringify({
                error: 'OFFLINE',
                message: '오프라인 상태입니다. 인터넷 연결을 확인해주세요.',
              }),
              {
                status: 503,
                headers: { 'Content-Type': 'application/json' },
              }
            );
          });
        })
    );
    return;
  }

  // Static assets - Cache-first strategy
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        console.log('[Service Worker] Serving from cache:', url.pathname);
        return cachedResponse;
      }

      // Fetch from network and cache
      return fetch(request).then((response) => {
        // Only cache successful responses
        if (!response || response.status !== 200 || response.type === 'error') {
          return response;
        }

        const responseToCache = response.clone();

        caches.open(STATIC_CACHE_NAME).then((cache) => {
          cache.put(request, responseToCache);
        });

        return response;
      }).catch(() => {
        // Return offline page for HTML requests
        if (request.headers.get('accept')?.includes('text/html')) {
          return caches.match('/').then((cachedPage) => {
            if (cachedPage) {
              return cachedPage;
            }

            return new Response(
              '<html><body><h1>오프라인</h1><p>인터넷 연결을 확인해주세요.</p></body></html>',
              {
                status: 503,
                headers: { 'Content-Type': 'text/html' },
              }
            );
          });
        }

        return new Response('Network error', { status: 503 });
      });
    })
  );
});

// Message event - handle cache updates
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CACHE_UPDATE') {
    console.log('[Service Worker] Manual cache update requested');
    caches.open(CACHE_NAME).then((cache) => {
      cache.addAll(ESSENTIAL_RESOURCES);
    });
  }
});

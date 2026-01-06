// BULL SAGE Service Worker - MINIMAL (no caching)
// v2.0.1 - Force refresh 2026-01-06

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(keys.map((key) => caches.delete(key)));
    })
  );
  self.clients.claim();
});

// No fetch handler = all requests go directly to network

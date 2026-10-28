/* MandiWise service worker: tiny network-first layer so "Add to Home screen"
   installs reliably and the shell still opens when signal drops. API calls are
   never intercepted (POST and cross-origin requests pass straight through). */
const CACHE = 'mandiwise-shell-v1';

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(['/']).catch(() => {})));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;                 // never touch API writes
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;      // never touch the API host
  if (url.pathname.startsWith('/api/')) return;

  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response && response.ok && request.mode === 'navigate') {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put('/', copy));
        }
        return response;
      })
      .catch(() => caches.match(request).then((hit) => hit || caches.match('/')))
  );
});

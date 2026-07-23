const CACHE_NAME = 'angelo-lounge-v3';
const BASE_PATH = '/';
const SHELL = [BASE_PATH + 'manifest.json', BASE_PATH + 'images/logo.svg'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL)).catch(() => undefined)
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  // Never cache images or hashed assets aggressively — always prefer network for fresh/fast CDN hits
  if (url.pathname.includes('/_astro/') || /\.(webp|avif|jpg|jpeg|png|gif|mp4)$/i.test(url.pathname)) {
    return;
  }
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(BASE_PATH))
    );
  }
});
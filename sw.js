// Om Sai service worker: lets the app open offline. App data lives in the browser (localStorage + IndexedDB), not here.
const V = 'omsai-v1';
const CORE = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png'];
self.addEventListener('install', e => e.waitUntil(caches.open(V).then(c => c.addAll(CORE)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const r = e.request; if (r.method !== 'GET') return;
  e.respondWith(caches.match(r, { ignoreSearch: true }).then(hit => {
    const net = fetch(r).then(res => { if (res && (res.ok || res.type === 'opaque')) { const c = res.clone(); caches.open(V).then(ca => ca.put(r, c)); } return res; })
      .catch(() => hit || (r.mode === 'navigate' ? caches.match('./index.html') : Response.error()));
    return hit || net;   // cached copy first, refreshed in the background when online
  }));
});

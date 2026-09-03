// 個体値ランク：オフライン用キャッシュ
// 大きいOCR部品はキャッシュ優先、index.html は更新を拾えるようネット優先にする
const CACHE = 'ivrank-v1';
const HEAVY = ['tesseract.min.js','worker.min.js',
               'tesseract-core-simd-lstm.wasm.js','tesseract-core-lstm.wasm.js',
               'jpn.traineddata','eng.traineddata'];

self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks =>
    Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  const heavy = HEAVY.some(n => req.url.endsWith(n));
  if (heavy) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok) { const c = res.clone(); caches.open(CACHE).then(x => x.put(req, c)); }
      return res;
    })));
  } else {
    e.respondWith(fetch(req).then(res => {
      if (res.ok) { const c = res.clone(); caches.open(CACHE).then(x => x.put(req, c)); }
      return res;
    }).catch(() => caches.match(req)));
  }
});

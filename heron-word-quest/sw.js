/* Heron Word Quest offline helper.
   - The app page: tries the internet first (so updates arrive), and uses the saved copy when offline.
   - Pictures, icons, sounds and fonts: saved on the device and used from there.
   - Class logins and saving to the cloud go straight to the internet (Firebase keeps its own offline copy). */
const SHELL = 'hwq-shell-v1', MEDIA = 'hwq-media-v1', EXT = 'hwq-ext-v1', META = 'hwq-meta-v1';
const KEEP = [SHELL, MEDIA, EXT, META];
const FONTS = 'https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Nunito:wght@600;700;800&family=Lexend:wght@400;600;700&family=Libre+Baskerville:wght@400;700&display=swap';
const FB = ['app', 'auth', 'firestore'].map(n => `https://www.gstatic.com/firebasejs/10.14.1/firebase-${n}-compat.js`);
const SHELL_FILES = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png', 'icons/favicon-32.png'];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const c = await caches.open(SHELL);
    await Promise.all(SHELL_FILES.map(u => c.add(new Request(u, {cache: 'reload'})).catch(() => {})));
    const x = await caches.open(EXT);
    await Promise.all([FONTS, ...FB].map(u => x.add(new Request(u, {mode: 'no-cors'})).catch(() => {})));
    await self.skipWaiting();
  })());
});
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (!KEEP.includes(k)) await caches.delete(k);
    await self.clients.claim();
  })());
});

const scopePath = new URL(self.registration.scope).pathname;
const isMedia = u => u.origin === location.origin && /^(pics|emoji|sfx|icons)\//.test(u.pathname.slice(scopePath.length));

async function cacheFirst(req, name) {
  const c = await caches.open(name), hit = await c.match(req, {ignoreSearch: true});
  if (hit) return hit;
  const res = await fetch(req);
  if (res && (res.ok || res.type === 'opaque')) c.put(req, res.clone()).catch(() => {});
  return res;
}
async function pageFirst(req) {
  const c = await caches.open(SHELL);
  try {
    const res = await Promise.race([fetch(req), new Promise((_, no) => setTimeout(() => no(new Error('slow')), 6000))]);
    if (res && res.ok) c.put('index.html', res.clone()).catch(() => {});
    return res;
  } catch (err) {
    return (await c.match('index.html')) || (await c.match('./')) || Response.error();
  }
}
async function staleWhileRevalidate(req, name) {
  const c = await caches.open(name), hit = await c.match(req);
  const net = fetch(req).then(res => { if (res && (res.ok || res.type === 'opaque')) c.put(req, res.clone()).catch(() => {}); return res; }).catch(() => hit);
  return hit || net;
}

self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET') return;
  const u = new URL(req.url);
  if (req.mode === 'navigate' && u.origin === location.origin) return e.respondWith(pageFirst(req));
  if (isMedia(u)) return e.respondWith(cacheFirst(req, MEDIA));
  if (u.origin === location.origin && /(manifest\.webmanifest|offline\.json)$/.test(u.pathname)) return e.respondWith(staleWhileRevalidate(req, SHELL));
  if (u.host === 'fonts.googleapis.com') return e.respondWith(staleWhileRevalidate(req, EXT));
  if (u.host === 'fonts.gstatic.com' || (u.host === 'www.gstatic.com' && u.pathname.startsWith('/firebasejs/'))) return e.respondWith(cacheFirst(req, EXT));
  // everything else (Firebase logins and saving, Wikimedia) goes straight to the internet
});

/* Save every picture, icon and sound for offline use. Only fetches what is missing or has changed. */
async function saveAll(port) {
  const list = await fetch('offline.json', {cache: 'no-store'}).then(r => r.json()).catch(() => null);
  if (!list) return port && port.postMessage({done: true, ok: false});
  const media = await caches.open(MEDIA), meta = await caches.open(META);
  const old = await meta.match('hashes').then(r => r ? r.json() : {}).catch(() => ({}));
  const want = Object.entries(list.files), todo = [];
  for (const [path, h] of want) { if (old[path] !== h || !(await media.match(path))) todo.push([path, h]); }
  let done = want.length - todo.length; const got = Object.assign({}, old);
  const step = async ([path, h]) => { try { const r = await fetch(path, {cache: 'no-store'}); if (r.ok) { await media.put(path, r); got[path] = h; done++; } } catch (e) {}
    if (port) port.postMessage({done: false, have: done, total: want.length}); };
  for (let i = 0; i < todo.length; i += 6) await Promise.all(todo.slice(i, i + 6).map(step));
  await meta.put('hashes', new Response(JSON.stringify(got)));
  if (port) port.postMessage({done: true, ok: true, have: done, total: want.length});
}
self.addEventListener('message', e => {
  if (e.data === 'save-all') e.waitUntil(saveAll(e.ports && e.ports[0]));
});

// ─── Caches ──────────────────────────────────────────────────────────────────
const SHELL_CACHE = 'apicole-shell-v4';
const API_CACHE   = 'apicole-api-v4';
const ALL_CACHES  = [SHELL_CACHE, API_CACHE];

// Assets précachés à l'installation (URLs stables, sans hash)
const SHELL_URLS = [
  '/',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/nav/accueil.png',
  '/icons/nav/ruche.png',
  '/icons/nav/historique.png',
  '/icons/nav/parametres.png',
  '/icons/nav/bot.png',
];

// Préfixes des appels API (Network first)
const API_PREFIXES = ['/hives', '/alerts', '/settings', '/api/'];

function isApiCall(pathname) {
  return API_PREFIXES.some((p) => pathname.startsWith(p));
}

// ─── Install : précache du shell ─────────────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) =>
      Promise.allSettled(SHELL_URLS.map((url) => cache.add(url).catch(() => {})))
    )
  );
  self.skipWaiting();
});

// ─── Activate : nettoyage des anciens caches ─────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => !ALL_CACHES.includes(k)).map((k) => caches.delete(k)))
      )
  );
  self.clients.claim();
});

// ─── Fetch : routage des stratégies ──────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Navigation SPA (F5, lien direct) → toujours index.html, jamais l'API
  // DOIT être avant isApiCall car les routes Angular partagent les mêmes préfixes
  if (req.mode === 'navigate') {
    event.respondWith(
      caches.match('/').then((r) => r || fetch(req))
    );
    return;
  }

  // Appels API XHR/fetch → Stale-while-revalidate
  if (isApiCall(url.pathname)) {
    event.respondWith(staleWhileRevalidateApi(req));
    return;
  }

  // Assets statiques → Cache first
  event.respondWith(cacheFirstStatic(req));
});

// ─── Stratégies ──────────────────────────────────────────────────────────────

async function staleWhileRevalidateApi(req) {
  const cache  = await caches.open(API_CACHE);
  const cached = await cache.match(req);

  // Mise à jour réseau en arrière-plan (fire & forget)
  const networkUpdate = fetch(req.clone())
    .then(response => {
      if (response.ok) {
        cache.put(req, response.clone());
        broadcast({ type: 'DATA_FRESH', cachedAt: Date.now() });
      }
      return response;
    })
    .catch(() => null);

  if (cached) {
    // Données en cache disponibles : retour immédiat, réseau en fond
    broadcast({ type: 'CACHE_FALLBACK', url: req.url });
    return cached;
  }

  // Pas de cache : on attend le réseau
  const response = await networkUpdate;
  if (response && response.status !== 0) return response;

  return new Response(JSON.stringify({ offline: true, error: 'Hors-ligne' }), {
    status: 503,
    headers: { 'Content-Type': 'application/json' },
  });
}

async function cacheFirstStatic(req) {
  const cached = await caches.match(req);
  if (cached) return cached;

  try {
    const response = await fetch(req);
    if (response.ok) {
      const cache = await caches.open(SHELL_CACHE);
      cache.put(req, response.clone());
    }
    return response;
  } catch (_) {
    return new Response('Ressource non disponible hors-ligne', { status: 503 });
  }
}

function broadcast(data) {
  self.clients
    .matchAll({ includeUncontrolled: true, type: 'window' })
    .then((clients) => clients.forEach((c) => c.postMessage(data)));
}

// ─── Push notifications ───────────────────────────────────────────────────────
self.addEventListener('push', (event) => {
  let data = {
    title: 'Alerte Ruche',
    body: 'Nouvelle alerte détectée',
    icon: '/icons/icon-192.png',
    url: '/',
  };

  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (_) {}
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon,
      badge: '/icons/icon-192.png',
      tag: 'apicole-alert',
      requireInteraction: true,
      data: { url: data.url },
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((list) => {
        const existing = list.find((c) => 'focus' in c);
        return existing ? existing.focus() : clients.openWindow(url);
      })
  );
});

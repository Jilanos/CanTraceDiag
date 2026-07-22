const CACHE_NAME = "cantracediag-pwa-shell-__CTD_BUILD_VERSION__";
const APP_SHELL = [
  "./",
  "./index.html",
  "./styles.css",
  "./manifest.webmanifest",
  "./assets/app-icon.svg",
  "./assets/app-icon-192.png",
  "./assets/app-icon-512.png",
  "./browser/product-app.mjs",
  "./browser/product-backend.mjs",
  "./browser/asc.mjs",
  "./browser/dbc.mjs",
  "./browser/decode.mjs",
  "./browser/local-backend.mjs",
  "./browser/store.mjs",
  "./browser/types.mjs",
  "./browser/workspace.mjs",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)),
    )),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || event.request.method !== "GET") return;
  if (event.request.mode === "navigate" || url.pathname.endsWith("/index.html")) {
    event.respondWith(networkFirst(event.request));
    return;
  }
  event.respondWith(staleWhileRevalidate(event.request));
});

async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const response = await fetch(request);
    cache.put(request, response.clone());
    return response;
  } catch {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw new Error("Offline and no cached app shell response.");
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  const fetched = fetch(request).then((response) => {
    cache.put(request, response.clone());
    return response;
  });
  return cached || fetched;
}

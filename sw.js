var SHELL = "zhaowen-shell-v6";
var DATA = "zhaowen-data-v1";
var ASSETS = ["./", "index.html", "assets/style.css", "assets/motion.css", "assets/motion.js", "assets/app.js", "assets/icon.svg", "assets/icon-192.png", "manifest.webmanifest"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(SHELL).then(function (c) { return c.addAll(ASSETS); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== SHELL && k !== DATA; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

function stripQuery(req) {
  var u = new URL(req.url);
  u.search = "";
  return u.toString();
}

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin !== location.origin) return;

  // news data: network first, fall back to the last copy
  if (url.pathname.indexOf("/data/") >= 0) {
    var key = stripQuery(req);
    e.respondWith(fetch(req).then(function (res) {
      if (res.ok) { var copy = res.clone(); caches.open(DATA).then(function (c) { c.put(key, copy); }); }
      return res;
    }).catch(function () { return caches.match(key); }));
    return;
  }

  // app shell: serve cached, refresh in the background
  e.respondWith(caches.match(req, { ignoreSearch: true }).then(function (hit) {
    var net = fetch(req).then(function (res) {
      if (res.ok) { var copy = res.clone(); caches.open(SHELL).then(function (c) { c.put(req, copy); }); }
      return res;
    }).catch(function () { return hit || caches.match("index.html"); });
    return hit || net;
  }));
});

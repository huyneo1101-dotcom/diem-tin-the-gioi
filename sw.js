// Điểm Tin Thế Giới — service worker (network-first cho nội dung mới, cache dự phòng offline)
var C = 'diemtin-v13';
var SHELL = ['./', './index.html', './manifest.webmanifest', './icon.svg'];

self.addEventListener('install', function (e) {
  self.skipWaiting();
  e.waitUntil(caches.open(C).then(function (c) { return c.addAll(SHELL); }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k !== C; }).map(function (k) { return caches.delete(k); }));
  }));
  self.clients.claim();
});

// Nhận push từ server (GitHub Action gửi khi có bản tin mới)
self.addEventListener('push', function (e) {
  var data = { title: '📰 Điểm Tin Thế Giới', body: 'Có bản tin mới', url: './' };
  try { if (e.data) { var j = e.data.json(); data.title = j.title || data.title; data.body = j.body || data.body; data.url = j.url || data.url; } }
  catch (_) { try { data.body = e.data.text(); } catch (__) {} }
  e.waitUntil(self.registration.showNotification(data.title, {
    body: data.body, icon: './icon.svg', badge: './icon.svg', tag: 'diemtin-news', renotify: true, data: { url: data.url || './' }
  }));
});

self.addEventListener('notificationclick', function (e) {
  e.notification.close();
  var url = (e.notification.data && e.notification.data.url) || './';
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (cl) {
    for (var i = 0; i < cl.length; i++) { if ('focus' in cl[i]) return cl[i].focus(); }
    if (self.clients.openWindow) return self.clients.openWindow(url);
  }));
});

self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then(function (r) {
      var cp = r.clone();
      caches.open(C).then(function (c) { c.put(e.request, cp); });
      return r;
    }).catch(function () {
      return caches.match(e.request).then(function (m) { return m || caches.match('./index.html'); });
    })
  );
});

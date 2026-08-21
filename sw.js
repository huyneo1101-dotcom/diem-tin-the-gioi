// Điểm Tin Thế Giới — service worker (network-first cho nội dung mới, cache dự phòng offline)
var C = 'diemtin-v52';
var SHELL = ['./', './index.html', './manifest.webmanifest', './icon.svg'];
// HAI KHO TÁCH KHỎI index.html, phải precache nếu không thì mở offline sẽ thiếu nội dung mà
// KHÔNG có lỗi nào hiện ra: data/analyses.json (tách 30/07/2026) mất mục 🏛️ Think-tank;
// data/kho.json (tách 21/08/2026) mất kho tin cũ, hồ sơ tập trận, cà phê, bản tuần.
// ⚠️ Để RIÊNG khỏi SHELL và bắt lỗi từng file: `addAll` là tất-cả-hoặc-không — một file 404
// (bản dựng cũ chưa có kho.json, hoặc mở từ bản repo chưa qua bước dựng) là service worker
// KHÔNG cài được, mất luôn cả phần chạy offline của trang.
var KHO = ['./data/analyses.json', './data/kho.json'];

self.addEventListener('install', function (e) {
  self.skipWaiting();
  e.waitUntil(caches.open(C).then(function (c) {
    return c.addAll(SHELL).then(function () {
      return Promise.all(KHO.map(function (u) { return c.add(u).catch(function () {}); }));
    });
  }));
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
      // ⛔ 21/08/2026 — `ignoreSearch` cho request CÙNG GỐC, đừng gỡ. `loadKho()` và
      // `loadAnalyses()` gắn `?t=<mốc hiện tại>` để né cache, nên mỗi lần mở trang là một URL
      // khác. `caches.match` mặc định so CẢ chuỗi truy vấn ⇒ bản precache `/data/kho.json`
      // KHÔNG BAO GIỜ khớp, hàm rơi xuống trả `index.html`, `r.json()` ném lỗi, `catch` nuốt
      // gọn: mở offline thì mất kho tin cũ và mục 🏛️ Think-tank trống — precache chỉ có trên
      // giấy. Đo 21/08: `match(kho.json?t=999999)` trả undefined, thêm ignoreSearch thì trúng.
      // Chỉ áp cho cùng gốc: chuỗi truy vấn của Supabase (`?select=cid,tags`) MANG NGHĨA, bỏ
      // qua nó là trả nhầm bảng cho nhau.
      var nha = e.request.url.indexOf(self.location.origin) === 0;
      return caches.match(e.request, nha ? { ignoreSearch: true } : undefined)
        .then(function (m) { return m || caches.match('./index.html'); });
    })
  );
});

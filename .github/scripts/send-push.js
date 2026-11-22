// Gửi Web Push tới mọi thiết bị đã đăng ký khi bản tin cập nhật.
// Chạy trong GitHub Action notify-push.yml. Cần secret VAPID_PRIVATE và DT_BOT_KEY.
//
// ⛔ 22/11/2026 — bảng `push_subs` thôi mở cho khoá công khai: người lạ chỉ còn THÊM được
// một đăng ký, không đọc, không sửa, không xoá. Máy này đọc danh sách qua hàm máy chủ
// `push_ds_gui()` (đòi header x-dt-key, cùng mã với bot Điểm Tin, kiểm bằng dt_ma_hop_le())
// và gỡ đăng ký chết qua `push_huy_dang_ky(endpoint)`. Luật: docs/supabase-setup.sql.
// Trước đó người lạ cầm khoá công khai xoá sạch được danh sách hoặc đổi endpoint để máy này
// gửi tin tới địa chỉ lạ.
const webpush = require('web-push');

const SB_URL = 'https://ltmlueqkajqmduoqghdf.supabase.co';
const SB_ANON = 'sb_publishable_74Lm6cc0CkoOOzy3A4IRrQ_BX0jHQcg';
const VAPID_PUBLIC = 'BJSpsOTphW35nM4lPwtbQHWlfo2f9Z4uoUjvn2pzg746SRlJEzijWfxdFFHoTqpE2Mdow-kbxSQchoSDtZYMzGs';
const VAPID_PRIVATE = process.env.VAPID_PRIVATE;
const DT_BOT_KEY = process.env.DT_BOT_KEY;
const NEWS_DATE = process.env.NEWS_DATE || '';

// Chỉ gửi tới máy chủ thông báo của trình duyệt. Luật INSERT của bảng cũng chặn địa chỉ khác;
// lọc thêm ở đây để một dòng lọt luật cũng không biến máy CI thành chỗ gửi tin đi bất kỳ đâu.
const HOST_PUSH = /^https:\/\/(fcm\.googleapis\.com|[a-z0-9-]+\.google\.com|updates\.push\.services\.mozilla\.com|[a-z0-9.-]+\.notify\.windows\.com|web\.push\.apple\.com)\//;

function hdr(them) {
  return Object.assign({ apikey: SB_ANON, Authorization: `Bearer ${SB_ANON}`, 'Content-Type': 'application/json' }, them || {});
}

async function main() {
  if (!VAPID_PRIVATE) { console.log('Thiếu secret VAPID_PRIVATE — không gửi được.'); process.exitCode = 1; return; }
  if (!DT_BOT_KEY) { console.log('Thiếu secret DT_BOT_KEY — không đọc được danh sách đăng ký.'); process.exitCode = 1; return; }
  webpush.setVapidDetails('mailto:huyneo1101@gmail.com', VAPID_PUBLIC, VAPID_PRIVATE);

  const r = await fetch(`${SB_URL}/rest/v1/rpc/push_ds_gui`, {
    method: 'POST', headers: hdr({ 'x-dt-key': DT_BOT_KEY }), body: '{}'
  });
  if (!r.ok) { console.log('Không đọc được danh sách đăng ký:', r.status, await r.text()); process.exitCode = 1; return; }
  const tat_ca = await r.json();
  const subs = tat_ca.filter(s => HOST_PUSH.test(s.endpoint || ''));
  console.log('Số thiết bị đăng ký:', subs.length, tat_ca.length > subs.length ? `(bỏ ${tat_ca.length - subs.length} địa chỉ lạ)` : '');
  if (!subs.length) return;

  const parts = (NEWS_DATE || '').split('-'); // YYYY-MM-DD
  const ddmm = parts.length === 3 ? `${parts[2]}/${parts[1]}` : '';
  const payload = JSON.stringify({
    title: '📰 Điểm Tin Thế Giới',
    body: ddmm ? `Bản tin ${ddmm} đã cập nhật — bấm để xem tin mới` : 'Có bản tin mới — bấm để xem',
    url: './'
  });

  let ok = 0, gone = 0, fail = 0;
  for (const s of subs) {
    try {
      await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, payload);
      ok++;
    } catch (e) {
      const code = e && e.statusCode;
      if (code === 404 || code === 410) {
        gone++;
        await fetch(`${SB_URL}/rest/v1/rpc/push_huy_dang_ky`, {
          method: 'POST', headers: hdr(), body: JSON.stringify({ p_endpoint: s.endpoint })
        }).catch(() => {});
      } else { fail++; console.log('push fail', code, (e && e.body) || ''); }
    }
  }
  console.log(`Đã gửi: ok=${ok} gone(đã xoá)=${gone} fail=${fail}`);
}

main().catch(e => { console.log('Lỗi:', e && e.message); process.exitCode = 1; });

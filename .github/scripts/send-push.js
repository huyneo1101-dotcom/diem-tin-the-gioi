// Gửi Web Push tới mọi thiết bị đã đăng ký khi bản tin cập nhật.
// Chạy trong GitHub Action notify-push.yml. Cần secret VAPID_PRIVATE.
const webpush = require('web-push');

const SB_URL = 'https://ltmlueqkajqmduoqghdf.supabase.co';
const SB_ANON = 'sb_publishable_74Lm6cc0CkoOOzy3A4IRrQ_BX0jHQcg';
const VAPID_PUBLIC = 'BN0PSYP1rgXE8KojMqRdrDis3hZCU8tiE5OpdGF6zFO5B_Ho3ba3UZ590rUfOKgUSgJR0iMVjdhRZX3aFk8d2qo';
const VAPID_PRIVATE = process.env.VAPID_PRIVATE;
const NEWS_DATE = process.env.NEWS_DATE || '';

async function main() {
  if (!VAPID_PRIVATE) { console.log('Thiếu secret VAPID_PRIVATE — bỏ qua gửi push.'); return; }
  webpush.setVapidDetails('mailto:huyneo1101@gmail.com', VAPID_PUBLIC, VAPID_PRIVATE);

  const r = await fetch(`${SB_URL}/rest/v1/push_subs?select=endpoint,p256dh,auth`, {
    headers: { apikey: SB_ANON, Authorization: `Bearer ${SB_ANON}` }
  });
  if (!r.ok) { console.log('Không đọc được push_subs:', r.status, await r.text()); return; }
  const subs = await r.json();
  console.log('Số thiết bị đăng ký:', subs.length);
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
        await fetch(`${SB_URL}/rest/v1/push_subs?endpoint=eq.${encodeURIComponent(s.endpoint)}`, {
          method: 'DELETE', headers: { apikey: SB_ANON, Authorization: `Bearer ${SB_ANON}` }
        }).catch(() => {});
      } else { fail++; console.log('push fail', code, (e && e.body) || ''); }
    }
  }
  console.log(`Đã gửi: ok=${ok} gone(đã xoá)=${gone} fail=${fail}`);
}

main().catch(e => { console.log('Lỗi:', e && e.message); });

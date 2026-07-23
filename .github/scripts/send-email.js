// Gửi email điểm tin khi bản tin cập nhật.
// Chạy trong GitHub Action notify-email.yml. Trích vài tin đáng chú ý vừa quét được
// từ index.html rồi gửi qua Gmail SMTP. Cần secret EMAIL_USER + EMAIL_APP_PASSWORD.
const fs = require('fs');
const nodemailer = require('nodemailer');

const WEB_URL = 'https://huyneo1101-dotcom.github.io/diem-tin-the-gioi';
const EMAIL_USER = process.env.EMAIL_USER;                 // gmail dùng để gửi
const EMAIL_PASS = process.env.EMAIL_APP_PASSWORD;         // App Password 16 ký tự
const EMAIL_TO = process.env.EMAIL_TO || 'lamgiaphat1603@gmail.com';
const MAX_ITEMS = parseInt(process.env.EMAIL_MAX_ITEMS || '6', 10);

// --- Trích object DATA = {...} trong index.html bằng cách đếm ngoặc (không đọc bằng Read) ---
function extractDATA() {
  const html = fs.readFileSync('index.html', 'utf8');
  const i = html.indexOf('var DATA');
  if (i < 0) throw new Error('Không tìm thấy "var DATA" trong index.html');
  const start = html.indexOf('{', i);
  let depth = 0, end = -1;
  for (let k = start; k < html.length; k++) {
    const c = html[k];
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) { end = k; break; } }
  }
  if (end < 0) throw new Error('Không đóng được object DATA');
  return JSON.parse(html.slice(start, end + 1));
}

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function trim(s, n) {
  s = String(s == null ? '' : s).trim();
  return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s;
}

// Chọn tin đáng chú ý: ưu tiên tin mới đưa hôm nay (_addedDate == generatedAt), mới nhất trước;
// trộn xen kẽ world/us để cân 2 mảng; thiếu thì bù bằng tin mới nhất bất kể ngày.
function pickHighlights(DATA) {
  const today = DATA.generatedAt;
  const tag = (arr, kind) => (Array.isArray(arr) ? arr : []).map((it, idx) => ({ ...it, _kind: kind, _idx: idx }));
  const world = tag(DATA.worldNews, 'Thế giới');
  const us = tag(DATA.usNews, 'Mỹ');
  const isToday = (it) => it._addedDate === today || it.date === today;

  const interleave = (a, b) => {
    const out = []; let i = 0, j = 0;
    while (i < a.length || j < b.length) { if (i < a.length) out.push(a[i++]); if (j < b.length) out.push(b[j++]); }
    return out;
  };
  let pool = interleave(world.filter(isToday), us.filter(isToday));
  if (pool.length < MAX_ITEMS) {
    const seen = new Set(pool.map(it => it.sourceUrl));
    for (const it of interleave(world, us)) { if (pool.length >= MAX_ITEMS) break; if (!seen.has(it.sourceUrl)) { pool.push(it); seen.add(it.sourceUrl); } }
  }
  return pool.slice(0, MAX_ITEMS);
}

function buildHtml(DATA, items) {
  const p = (DATA.generatedAt || '').split('-');
  const ddmm = p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : (DATA.generatedAt || '');
  const rows = items.map(it => `
    <tr><td style="padding:14px 0;border-bottom:1px solid #eceff3;">
      <div style="font-size:12px;color:#8a94a6;text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px;">
        ${esc(it._kind)}${it.category ? ' · ' + esc(it.category) : ''}
      </div>
      <a href="${esc(it.sourceUrl || WEB_URL)}" style="font-size:16px;font-weight:600;color:#12233b;text-decoration:none;line-height:1.4;">
        ${esc(trim(it.title, 140))}
      </a>
      <div style="font-size:14px;color:#48566b;line-height:1.55;margin-top:6px;">${esc(trim(it.summary, 180))}</div>
      <div style="font-size:12px;color:#9aa4b2;margin-top:6px;">${esc(it.sourceName || '')}</div>
    </td></tr>`).join('');

  return `<!doctype html><html><body style="margin:0;background:#f4f6f9;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e6eaf0;">
        <tr><td style="background:#12233b;padding:22px 28px;">
          <div style="font-size:20px;font-weight:700;color:#ffffff;">📰 Điểm Tin Thế Giới</div>
          <div style="font-size:13px;color:#aebbcf;margin-top:4px;">Bản tin ${esc(ddmm)} — vài tin đáng chú ý vừa cập nhật</div>
        </td></tr>
        <tr><td style="padding:8px 28px 4px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">${rows}</table>
        </td></tr>
        <tr><td align="center" style="padding:22px 28px 10px;">
          <a href="${WEB_URL}" style="display:inline-block;background:#1a56db;color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;padding:12px 26px;border-radius:9px;">
            Đọc toàn bộ bản tin →
          </a>
        </td></tr>
        <tr><td align="center" style="padding:6px 28px 24px;">
          <a href="${WEB_URL}" style="font-size:12px;color:#9aa4b2;">${WEB_URL}</a>
        </td></tr>
      </table>
    </td></tr>
  </table></body></html>`;
}

async function main() {
  if (!EMAIL_USER || !EMAIL_PASS) {
    console.log('Thiếu secret EMAIL_USER / EMAIL_APP_PASSWORD — bỏ qua gửi email.');
    return;
  }
  const DATA = extractDATA();
  const items = pickHighlights(DATA);
  if (!items.length) { console.log('Không có tin để gửi — bỏ qua.'); return; }

  const p = (DATA.generatedAt || '').split('-');
  const ddmm = p.length === 3 ? `${p[2]}/${p[1]}` : (DATA.generatedAt || '');
  const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com', port: 465, secure: true,
    auth: { user: EMAIL_USER, pass: EMAIL_PASS },
  });

  const info = await transporter.sendMail({
    from: `"Điểm Tin Thế Giới" <${EMAIL_USER}>`,
    to: EMAIL_TO,
    subject: `📰 Điểm Tin Thế Giới — bản tin ${ddmm} (${items.length} tin nổi bật)`,
    text: `Bản tin ${ddmm} đã cập nhật.\n\n` +
      items.map(it => `• [${it._kind}] ${it.title}\n  ${trim(it.summary, 180)}\n  ${it.sourceName || ''} — ${it.sourceUrl || ''}`).join('\n\n') +
      `\n\nĐọc toàn bộ: ${WEB_URL}`,
    html: buildHtml(DATA, items),
  });
  console.log(`Đã gửi email tới ${EMAIL_TO}: ${info.messageId} (${items.length} tin)`);
}

main().catch(e => { console.log('Lỗi gửi email:', e && e.message); process.exit(0); });

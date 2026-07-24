// Email newsletter BUỔI SÁNG — gửi khi phiên quét sáng có:
//   (a) sự kiện ngoại giao / tập trận MỚI được tạo hoặc thêm tin liên quan, và/hoặc
//   (b) BÁO CÁO TUẦN mới đăng (Chủ nhật).
// Gộp cả hai vào MỘT email nếu cùng ngày. Chạy trong Action notify-morning.yml.
//
// Cách phát hiện "mới": so DATA hiện tại (index.html) với bản commit TRƯỚC (PREV_HTML do
// workflow ghi từ `git show HEAD~1:index.html`). Không cần đánh dấu gì thêm trong dữ liệu.
// Cần secret EMAIL_USER + EMAIL_APP_PASSWORD.
const fs = require('fs');
const nodemailer = require('nodemailer');

const WEB_URL = 'https://huyneo1101-dotcom.github.io/diem-tin-the-gioi';
const EMAIL_USER = process.env.EMAIL_USER;
const EMAIL_PASS = process.env.EMAIL_APP_PASSWORD;
const EMAIL_TO = process.env.EMAIL_TO || 'lamgiaphat1603@gmail.com,huyneo1101@gmail.com';

function extractDATA(html) {
  const i = html.indexOf('var DATA');
  if (i < 0) return null;
  const start = html.indexOf('{', i);
  let depth = 0, end = -1;
  for (let k = start; k < html.length; k++) {
    const c = html[k];
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) { end = k; break; } }
  }
  if (end < 0) return null;
  try { return JSON.parse(html.slice(start, end + 1)); } catch (e) { return null; }
}
function readDATA(path) {
  try { return extractDATA(fs.readFileSync(path, 'utf8')); } catch (e) { return null; }
}
function esc(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function trim(s, n) { s = String(s == null ? '' : s).trim(); return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s; }
const STLABEL = { ongoing: 'Đang diễn ra', upcoming: 'Sắp diễn ra', recent: 'Đã kết thúc' };

// Gom dipEvents + exercises của một DATA thành map name -> {ev, itemUrls:Set}
function eventMap(DATA) {
  const m = new Map();
  const add = (arr, kind) => (Array.isArray(arr) ? arr : []).forEach(ev => {
    const urls = new Set((ev.items || []).map(it => it.sourceUrl).filter(Boolean));
    m.set((kind + '::' + (ev.name || '')), { ev, kind, urls });
  });
  add(DATA.dipEvents, 'dip');
  add(DATA.exercises, 'ex');
  return m;
}

// Tìm sự kiện mới + tin mới (so với prev). Trả [{ev, kind, isNewEvent, newItems:[...]}]
function diffEvents(cur, prev) {
  const curM = eventMap(cur);
  const prevM = prev ? eventMap(prev) : new Map();
  const out = [];
  for (const [key, c] of curM) {
    const p = prevM.get(key);
    if (!p) {
      out.push({ ev: c.ev, kind: c.kind, isNewEvent: true, newItems: (c.ev.items || []) });
    } else {
      const fresh = (c.ev.items || []).filter(it => it.sourceUrl && !p.urls.has(it.sourceUrl));
      if (fresh.length) out.push({ ev: c.ev, kind: c.kind, isNewEvent: false, newItems: fresh });
    }
  }
  return out;
}

function weeklyIsNew(cur, prev) {
  const w = cur.weeklyReport;
  if (!w || !(w.countries || []).length) return null;
  if (prev && prev.weeklyReport && prev.weeklyReport.generatedAt === w.generatedAt) return null;
  return w;
}

function evBlockHtml(d) {
  const st = STLABEL[d.ev.status] || '';
  const tag = d.kind === 'ex' ? '🎯 Tập trận' : '🕊️ Ngoại giao';
  const items = d.newItems.slice(0, 5).map(it => `
    <li style="margin:4px 0;"><a href="${esc(it.sourceUrl || WEB_URL)}" style="color:#12233b;text-decoration:none;font-weight:600;">${esc(trim(it.title, 140))}</a>
      <span style="color:#9aa4b2;font-size:12px;">${it.sourceName ? ' · ' + esc(it.sourceName) : ''}</span></li>`).join('');
  return `<tr><td style="padding:14px 0;border-bottom:1px solid #eceff3;">
      <div style="font-size:12px;color:#8a94a6;text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px;">${tag}${st ? ' · ' + esc(st) : ''}${d.isNewEvent ? ' · MỚI' : ''}</div>
      <div style="font-size:16px;font-weight:700;color:#12233b;line-height:1.4;">${esc(d.ev.name || '')}</div>
      ${d.ev.dates ? `<div style="font-size:12px;color:#9aa4b2;margin-top:2px;">${esc(d.ev.dates)}</div>` : ''}
      <ul style="margin:8px 0 0;padding-left:18px;">${items}</ul>
    </td></tr>`;
}

function weeklyHtml(w) {
  const range = (w.weekStart ? w.weekStart : '') + (w.weekEnd ? ' – ' + w.weekEnd : '');
  const blocks = (w.countries || []).map(c => {
    const pts = (c.points || []).slice(0, 4).map(p => `<li style="margin:3px 0;color:#48566b;">${esc(trim(p.title, 120))}</li>`).join('');
    return `<div style="margin:10px 0;">
      <div style="font-size:15px;font-weight:700;color:#12233b;">${esc(c.flag || '')} ${esc(c.name || '')}</div>
      ${c.lede ? `<div style="font-size:13px;color:#48566b;font-style:italic;margin:3px 0;">${esc(trim(c.lede, 220))}</div>` : ''}
      <ul style="margin:4px 0 0;padding-left:18px;">${pts}</ul></div>`;
  }).join('');
  return `<tr><td style="padding:16px 0 6px;">
      <div style="font-size:13px;color:#8a94a6;text-transform:uppercase;letter-spacing:.4px;">📊 Báo cáo tuần · ${esc(range)}</div>
      ${blocks}
      <div style="margin-top:8px;"><a href="${WEB_URL}/#analysis" style="color:#1a56db;font-weight:600;text-decoration:none;">Đọc báo cáo tuần đầy đủ →</a></div>
    </td></tr>`;
}

function buildHtml(evs, weekly, ddmm) {
  let sections = '';
  if (evs.length) sections += `<tr><td style="padding:6px 28px 0;"><table role="presentation" width="100%">${evs.map(evBlockHtml).join('')}</table></td></tr>`;
  if (weekly) sections += `<tr><td style="padding:0 28px;"><table role="presentation" width="100%">${weeklyHtml(weekly)}</table></td></tr>`;
  const sub = [evs.length ? `${evs.length} sự kiện/tập trận cập nhật` : '', weekly ? 'báo cáo tuần mới' : ''].filter(Boolean).join(' · ');
  return `<!doctype html><html><body style="margin:0;background:#f4f6f9;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e6eaf0;">
        <tr><td style="background:#0e4d4d;padding:22px 28px;">
          <div style="font-size:20px;font-weight:700;color:#ffffff;">🌏 Bản tin sáng — Sự kiện & Báo cáo</div>
          <div style="font-size:13px;color:#a9cccc;margin-top:4px;">${esc(ddmm)}${sub ? ' — ' + esc(sub) : ''}</div>
        </td></tr>
        ${sections}
        <tr><td align="center" style="padding:20px 28px 24px;">
          <a href="${WEB_URL}" style="display:inline-block;background:#0e8a8a;color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;padding:12px 26px;border-radius:9px;">Mở trang tin →</a>
        </td></tr>
      </table>
    </td></tr>
  </table></body></html>`;
}

async function main() {
  // Thiếu secret / không đọc được DATA = LỖI CẤU HÌNH (không phải no-op) -> để job ĐỎ.
  if (!EMAIL_USER || !EMAIL_PASS) { console.error('LỖI: thiếu secret EMAIL_USER/EMAIL_APP_PASSWORD.'); process.exit(1); }
  const cur = readDATA('index.html');
  if (!cur) { console.error('LỖI: không đọc được DATA hiện tại (index.html).'); process.exit(1); }
  const prev = process.env.PREV_HTML ? readDATA(process.env.PREV_HTML) : null;

  const evs = diffEvents(cur, prev);
  const weekly = weeklyIsNew(cur, prev);
  if (!evs.length && !weekly) { console.log('Không có sự kiện/tập trận mới, không có báo cáo tuần mới — bỏ qua gửi.'); return; }

  const p = (cur.generatedAt || '').split('-');
  const ddmm = p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : new Date().toISOString().slice(0, 10);
  const subjBits = [];
  if (evs.length) subjBits.push(`${evs.length} sự kiện/tập trận`);
  if (weekly) subjBits.push('báo cáo tuần');

  const transporter = nodemailer.createTransport({ host: 'smtp.gmail.com', port: 465, secure: true, auth: { user: EMAIL_USER, pass: EMAIL_PASS } });
  const textLines = [];
  evs.forEach(d => {
    textLines.push(`• [${d.kind === 'ex' ? 'Tập trận' : 'Ngoại giao'}${d.isNewEvent ? ' · MỚI' : ''}] ${d.ev.name}`);
    d.newItems.slice(0, 5).forEach(it => textLines.push(`   - ${it.title} — ${it.sourceUrl || ''}`));
  });
  if (weekly) {
    textLines.push('', `📊 Báo cáo tuần ${weekly.weekStart || ''}–${weekly.weekEnd || ''}:`);
    (weekly.countries || []).forEach(c => textLines.push(`   ${c.flag || ''} ${c.name}: ${(c.points || []).map(x => x.title).slice(0, 4).join(' · ')}`));
  }
  const info = await transporter.sendMail({
    from: `"Điểm Tin Thế Giới" <${EMAIL_USER}>`,
    to: EMAIL_TO,
    subject: `🌏 Bản tin sáng ${ddmm} — ${subjBits.join(' + ')}`,
    text: `Bản tin sáng ${ddmm}.\n\n` + textLines.join('\n') + `\n\nMở trang: ${WEB_URL}`,
    html: buildHtml(evs, weekly, ddmm),
  });
  console.log(`Đã gửi email sáng tới ${EMAIL_TO}: ${info.messageId} (${evs.length} sự kiện, báo cáo tuần: ${weekly ? 'có' : 'không'})`);
}

main().catch(e => { console.error('LỖI gửi email sáng:', (e && e.stack) || e); process.exit(1); });

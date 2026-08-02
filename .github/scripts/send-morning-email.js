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
// Bài think-tank tách khỏi index.html 30/07/2026 (xem scripts/analyses_store.py) — phải nạp
// riêng, cho CẢ bản hiện tại lẫn bản HEAD~1, nếu không diffAnalyses luôn thấy mảng rỗng và
// khối 🏛️ Think-tank biến mất khỏi email mà không có lỗi nào.
function readAnalyses(path) {
  if (!path) return [];
  try {
    const a = JSON.parse(fs.readFileSync(path, 'utf8'));
    return Array.isArray(a) ? a : [];
  } catch (e) { return []; }
}
function esc(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function trim(s, n) { s = String(s == null ? '' : s).trim(); return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s; }
const STLABEL = { ongoing: 'Đang diễn ra', upcoming: 'Sắp diễn ra', recent: 'Đã kết thúc' };

// ==== 🆕 Mới trên web + 💡 Có thể bạn chưa biết (chỉ thị Huy 27/07/2026) ====
// Nguồn: whats-new.json ở gốc repo (xem "_doc" trong file đó). Hai mục này KHÔNG bao giờ tự
// mở email: gate gửi vẫn là "có sự kiện/tập trận mới hoặc báo cáo tuần mới" — nếu không thì
// một mẹo dùng web không đáng một lá mail. Chúng ăn theo email đã chắc chắn gửi.
// Chốt an toàn giống mục "Chủ đề thiếu" của send-email.js: thiếu file / JSON lỗi / mảng rỗng
// thì BỎ CẢ MỤC (chỉ log), KHÔNG làm vỡ email.
const FEATURE_DAYS = 7;   // feature cũ hơn số ngày này thì thôi, coi như đã giới thiệu rồi
const FEATURE_MAX = 3;    // in tối đa 3 mục, tránh email dài hơn phần tin

function readWhatsNew() {
  try {
    const j = JSON.parse(fs.readFileSync('whats-new.json', 'utf8'));
    return {
      features: Array.isArray(j.features) ? j.features : [],
      tips: Array.isArray(j.tips) ? j.tips : [],
    };
  } catch (e) {
    console.log('whats-new.json: không đọc được (' + (e && e.message) + ') — bỏ mục Mới trên web + Có thể bạn chưa biết.');
    return { features: [], tips: [] };
  }
}

// generatedAt dạng YYYY-MM-DD -> số ngày kể từ epoch (UTC, khỏi lệ thuộc giờ máy chạy Action).
function dayNum(ymd) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(ymd || ''));
  const t = m ? Date.UTC(+m[1], +m[2] - 1, +m[3]) : Date.now();
  return Math.floor(t / 86400000);
}

function freshFeatures(wn, ymd) {
  const today = dayNum(ymd);
  return wn.features
    .filter(f => f && f.title && /^\d{4}-\d{2}-\d{2}$/.test(f.date || ''))
    .filter(f => { const d = today - dayNum(f.date); return d >= 0 && d < FEATURE_DAYS; })
    .sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0))
    .slice(0, FEATURE_MAX);
}

// Mẹo xoay theo NGÀY, không random: cùng một ngày chạy lại (retry/dispatch) ra cùng mẹo, và
// mẹo mới thêm vào cuối mảng chắc chắn có lượt. Thêm/bớt mẹo chỉ làm lệch pha, không hỏng gì.
function tipOfDay(wn, ymd) {
  const t = wn.tips.filter(x => x && x.title);
  return t.length ? t[((dayNum(ymd) % t.length) + t.length) % t.length] : null;
}

function featuresHtml(fs_, i) {
  const rows = fs_.map((f, k) => `<div style="margin-top:${k ? 9 : 8}px;">
        <div style="font-size:14.5px;font-weight:700;color:${INK};">${esc(f.title)}</div>
        <div style="font-size:13.5px;color:${BODY};line-height:1.6;">${esc(trim(f.desc, 340))}</div>
      </div>`).join('');
  return rowHtml(String(i + 1).padStart(2, '0'), labelHtml('Mới trên web', '#0f766e') + rows);
}

function tipHtml(tip) {
  const link = tip.path
    ? `<div style="margin-top:7px;"><a href="${WEB_URL}${esc(tip.path)}" style="font-size:13px;color:${INK};font-weight:600;">Mở thử →</a></div>`
    : '';
  const inner = labelHtml('Có thể bạn chưa biết', '#a16207')
    + `<div style="font-size:15px;font-weight:700;color:${INK};margin-top:6px;">${esc(tip.title)}</div>`
    + `<div style="font-size:13.5px;color:${BODY};line-height:1.65;margin-top:3px;">${esc(trim(tip.desc, 340))}</div>`
    + link;
  return rowHtml('💡', inner, '17px');
}

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

// Bài phân tích think-tank vừa nạp (DATA.analyses) — thêm 27/07/2026 theo chỉ thị Huy
// "quét tin buổi sáng nhớ quét thêm cả các bài từ think-tank".
function diffAnalyses(cur, prev) {
  const arr = Array.isArray(cur.analyses) ? cur.analyses : [];
  // `analysesKnown` là Ý ĐỊNH KHAI BẰNG LỜI: "bản trước của kho think-tank đã được nạp thật".
  // KHÔNG suy từ việc prev.analyses có phần tử hay không — kho tách ra file riêng 30/07/2026,
  // nên quên truyền PREV_ANALYSES sẽ cho mảng rỗng, và "rỗng" đọc thành "trước đây chưa có bài
  // nào" → email liệt kê nguyên kho 442 bài như vừa nạp sáng nay. Cùng lớp lỗi với
  // TELEGRAM_BAT_BUOC và tu_dong=1 (xem CLAUDE.md).
  if (prev && prev.analysesKnown) {
    const seen = new Set((prev.analyses || []).map(a => a && a.url).filter(Boolean));
    return arr.filter(a => a && a.url && !seen.has(a.url));
  }
  // Không có bản trước để so (workflow_dispatch, hoặc commit đầu): dựa vào dấu `_addedDate`
  // do add_analyses.py đóng. Bài không có dấu = bài đời cũ -> coi như cũ. Thà bỏ sót một
  // email còn hơn liệt kê nguyên kho 24 bài như thể vừa nạp hết trong sáng nay.
  return arr.filter(a => a && a._addedDate && a._addedDate === cur.generatedAt);
}

function weeklyIsNew(cur, prev) {
  const w = cur.weeklyReport;
  if (!w || !(w.countries || []).length) return null;
  if (prev && prev.weeklyReport && prev.weeklyReport.generatedAt === w.generatedAt) return null;
  return w;
}

// ==== GIAO DIỆN: mẫu 4 "Digest tối giản" (Huy chốt 27/07/2026) ====
// Chọn từ 5 mẫu trong docs/mockup-newsletter-sang-v1.html. Nguyên tắc của mẫu này: KHÔNG nền màu,
// KHÔNG thẻ bo tròn — chỉ typography, số mục đánh dấu bên lề và đường kẻ mảnh. Đổi màu/nền trong
// đây là làm mất chính thứ Huy chọn; muốn đổi phong cách thì lấy mẫu khác trong file mockup.
// Vì sao mẫu này an toàn nhất: không ô nào dựa vào background-color, nên Outlook/Gmail dark mode
// không thể tạo ra cảnh chữ trắng trên nền trắng như các mẫu nền tối.
const ACCENT = { ex: '#b45309', dip: '#0f766e', ana: '#3730a3' };   // tập trận = hổ phách · ngoại giao = xanh mòng · think-tank = chàm
const INK = '#111827', BODY = '#4b5563', MUTED = '#9ca3af', RULE = '#eceff3';

// Số mục in ở lề trái: 01, 02, 03… Mục mẹo dùng 💡 thay số (xem tipHtml).
function rowHtml(mark, inner, markSize) {
  return `<tr><td style="padding:22px 30px 0;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
        <td width="34" valign="top"><div style="font-size:${markSize || '19px'};font-weight:800;color:#d1d5db;line-height:1.2;">${mark}</div></td>
        <td valign="top">${inner}</td>
      </tr></table>
    </td></tr>`;
}
function ruleHtml() {
  return `<tr><td style="padding:22px 30px 0;"><div style="height:1px;background:${RULE};line-height:1px;font-size:0;">&nbsp;</div></td></tr>`;
}
function labelHtml(text, color) {
  return `<div style="font-size:11.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:${color};">${text}</div>`;
}

function evBlockHtml(d, i) {
  const st = STLABEL[d.ev.status] || '';
  const accent = ACCENT[d.kind] || ACCENT.dip;
  const label = [d.kind === 'ex' ? 'Tập trận' : 'Ngoại giao', st, d.isNewEvent ? 'MỚI' : '']
    .filter(Boolean).map(esc).join(' · ');
  const items = d.newItems.slice(0, 5);
  const meta = bits => `<div style="font-size:12.5px;color:${MUTED};margin-top:8px;">${bits.filter(Boolean).join(' · ')}</div>`;
  const src = it => (it.sourceUrl
    ? `<a href="${esc(it.sourceUrl)}" style="color:${INK};font-weight:600;text-decoration:none;">${esc(it.sourceName || 'Nguồn')}</a>`
    : esc(it.sourceName || ''));

  let inner;
  if (items.length === 1) {
    // Một tin mới: cho chính tiêu đề tin làm tít, tên sự kiện lùi xuống dòng meta — đọc thẳng vào việc.
    const it = items[0];
    inner = labelHtml(label, accent)
      + `<div style="font-size:17px;font-weight:700;color:${INK};line-height:1.4;margin-top:6px;">${esc(trim(it.title, 150))}</div>`
      + (it.summary ? `<div style="font-size:14px;color:${BODY};line-height:1.68;margin-top:8px;">${esc(trim(it.summary, 360))}</div>` : '')
      + meta([esc(d.ev.name || ''), d.ev.dates ? esc(d.ev.dates) : '', src(it)]);
  } else {
    // Nhiều tin mới: tít là tên sự kiện, các tin liệt kê bên dưới, mỗi tin một dòng đậm + nguồn.
    inner = labelHtml(label, accent)
      + `<div style="font-size:17px;font-weight:700;color:${INK};line-height:1.4;margin-top:6px;">${esc(d.ev.name || '')}</div>`
      + (d.ev.dates ? `<div style="font-size:12.5px;color:${MUTED};margin-top:3px;">${esc(d.ev.dates)}</div>` : '')
      + items.map(it => `<div style="margin-top:11px;">
          <a href="${esc(it.sourceUrl || WEB_URL)}" style="font-size:14.5px;font-weight:700;color:${INK};text-decoration:none;line-height:1.45;">${esc(trim(it.title, 150))}</a>
          ${it.sourceName ? `<div style="font-size:12.5px;color:${MUTED};margin-top:2px;">${esc(it.sourceName)}</div>` : ''}
        </div>`).join('');
  }
  return rowHtml(String(i + 1).padStart(2, '0'), inner);
}

function weeklyHtml(w, i) {
  const range = (w.weekStart ? w.weekStart : '') + (w.weekEnd ? ' – ' + w.weekEnd : '');
  const blocks = (w.countries || []).map(c => {
    const pts = (c.points || []).slice(0, 4)
      .map(p => `<div style="font-size:13.5px;color:${BODY};line-height:1.62;margin-top:2px;">— ${esc(trim(p.title, 130))}</div>`).join('');
    return `<div style="margin-top:10px;">
      <div style="font-size:14px;font-weight:700;color:${INK};">${esc(c.flag || '')} ${esc(c.name || '')}</div>
      ${c.lede ? `<div style="font-size:13.5px;color:${BODY};line-height:1.62;font-style:italic;margin-top:2px;">${esc(trim(c.lede, 220))}</div>` : ''}
      ${pts}</div>`;
  }).join('');
  const inner = labelHtml('Báo cáo tuần' + (range ? ` <span style="font-weight:400;letter-spacing:0;text-transform:none;color:${MUTED};">${esc(range)}</span>` : ''), '#6d28d9')
    + blocks
    + `<div style="margin-top:10px;"><a href="${WEB_URL}/#analysis/weekly" style="font-size:13px;color:${INK};font-weight:600;">Đọc báo cáo tuần đầy đủ →</a></div>`;
  return rowHtml(String(i + 1).padStart(2, '0'), inner);
}

// Khối 🏛️ Think-tank: mỗi bài một dòng tít + viện/tác giả + câu takeaway (thứ đáng đọc nhất
// của bài phân tích). Cap 6 bài để email không dài hơn phần sự kiện.
const ANA_MAX = 6;
function analysesHtml(list, i) {
  const rows = list.slice(0, ANA_MAX).map((a, k) => `<div style="margin-top:${k ? 12 : 8}px;">
        <a href="${esc(a.url || WEB_URL)}" style="font-size:14.5px;font-weight:700;color:${INK};text-decoration:none;line-height:1.45;">${esc(trim(a.title, 150))}</a>
        <div style="font-size:12.5px;color:${MUTED};margin-top:2px;">${[esc(a.outlet || ''), esc(a.author || ''), esc(a.topic || '')].filter(Boolean).join(' · ')}</div>
        ${a.takeaway ? `<div style="font-size:13.5px;color:${BODY};line-height:1.62;margin-top:4px;">${esc(trim(a.takeaway, 260))}</div>` : ''}
      </div>`).join('');
  const more = list.length > ANA_MAX
    ? `<div style="font-size:12.5px;color:${MUTED};margin-top:10px;">…và ${list.length - ANA_MAX} bài nữa trên web.</div>` : '';
  return rowHtml(String(i + 1).padStart(2, '0'), labelHtml('Think-tank', ACCENT.ana) + rows + more);
}

function buildHtml(evs, weekly, anas, ddmm, feats, tip) {
  // Số mục chạy LIÊN TỤC qua mọi khối có nội dung: mỗi sự kiện một số, rồi báo cáo tuần, rồi
  // Mới trên web. Ngày rỗng khối nào thì số tự dồn lên, không để lỗ 01 → 03.
  let n = 0, sections = '';
  evs.forEach(d => { if (n) sections += ruleHtml(); sections += evBlockHtml(d, n++); });
  if (weekly) { if (n) sections += ruleHtml(); sections += weeklyHtml(weekly, n++); }
  if (anas && anas.length) { if (n) sections += ruleHtml(); sections += analysesHtml(anas, n++); }
  if (feats && feats.length) { if (n) sections += ruleHtml(); sections += featuresHtml(feats, n++); }
  if (tip) { if (n) sections += ruleHtml(); sections += tipHtml(tip); }
  const sub = [evs.length ? `${evs.length} cập nhật` : '', weekly ? 'báo cáo tuần' : '',
    anas && anas.length ? `${anas.length} bài think-tank` : ''].filter(Boolean).join(' · ');
  return `<!doctype html><html><body style="margin:0;background:#f2f4f7;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f2f4f7;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border:1px solid #e8ecf1;border-radius:4px;">
        <tr><td style="padding:30px 30px 0;">
          <div style="font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#8a94a0;">Điểm Tin Thế Giới · ${esc(ddmm)}</div>
          <div style="font-size:24px;font-weight:800;color:${INK};margin-top:8px;letter-spacing:-.01em;">Sự kiện &amp; Tập trận</div>
          ${sub ? `<div style="font-size:13px;color:${MUTED};margin-top:5px;">${esc(sub)}</div>` : ''}
          <div style="height:2px;background:${INK};width:44px;margin-top:14px;line-height:2px;font-size:0;">&nbsp;</div>
        </td></tr>
        ${sections}
        <tr><td style="padding:26px 30px 32px;">
          <a href="${WEB_URL}" style="font-size:15px;font-weight:700;color:${INK};text-decoration:none;border-bottom:2px solid ${INK};padding-bottom:2px;">Mở trang tin →</a>
        </td></tr>
      </table>
    </td></tr>
  </table></body></html>`;
}

async function main() {
  // Thiếu secret / không đọc được DATA = LỖI CẤU HÌNH (không phải no-op) -> để job ĐỎ.
  // Chỉ bắt buộc secret khi THẬT SỰ gửi email. Với GUI_EMAIL=0 script vẫn phải chạy tới cuối
  // để ghi payload cho Telegram — chết ở đây là Telegram sáng chết theo, kể cả khi Huy đã gỡ
  // secret email khỏi repo (chuyện rất dễ xảy ra sau khi bỏ hẳn kênh email).
  if (process.env.GUI_EMAIL !== '0' && (!EMAIL_USER || !EMAIL_PASS)) {
    console.error('LỖI: thiếu secret EMAIL_USER/EMAIL_APP_PASSWORD.'); process.exit(1);
  }
  const cur = readDATA('index.html');
  if (!cur) { console.error('LỖI: không đọc được DATA hiện tại (index.html).'); process.exit(1); }
  cur.analyses = readAnalyses('data/analyses.json');
  const prev = process.env.PREV_HTML ? readDATA(process.env.PREV_HTML) : null;
  // prev có thể null (không có HEAD~1) — khi đó diffAnalyses tự lùi về dấu _addedDate.
  if (prev && process.env.PREV_ANALYSES) {
    prev.analyses = readAnalyses(process.env.PREV_ANALYSES);
    prev.analysesKnown = true;
  }

  const evs = diffEvents(cur, prev);
  const weekly = weeklyIsNew(cur, prev);
  const anas = diffAnalyses(cur, prev);
  if (!evs.length && !weekly && !anas.length) {
    console.log('Không có sự kiện/tập trận mới, không có báo cáo tuần mới, không có bài think-tank mới — bỏ qua gửi.');
    return;
  }

  const p = (cur.generatedAt || '').split('-');
  const ddmm = p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : new Date().toISOString().slice(0, 10);
  const subjBits = [];
  if (evs.length) subjBits.push(`${evs.length} sự kiện/tập trận`);
  if (weekly) subjBits.push('báo cáo tuần');
  if (anas.length) subjBits.push(`${anas.length} bài think-tank`);

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
  if (anas.length) {
    textLines.push('', '🏛️ Think-tank:');
    anas.slice(0, ANA_MAX).forEach(a => textLines.push(`   - [${a.outlet || ''}] ${a.title} — ${a.url || ''}`));
  }
  const wn = readWhatsNew();
  const feats = freshFeatures(wn, cur.generatedAt);
  const tip = tipOfDay(wn, cur.generatedAt);
  if (feats.length) {
    textLines.push('', '🆕 Mới trên web:');
    feats.forEach(f => textLines.push(`   - ${f.title}: ${f.desc || ''}`));
  }
  if (tip) {
    textLines.push('', `💡 Có thể bạn chưa biết — ${tip.title}`, `   ${tip.desc || ''}${tip.path ? ' → ' + WEB_URL + tip.path : ''}`);
  }
  // ---- Payload cho Telegram (thêm 27/07/2026) ----
  // Ghi ra file NGAY TẠI ĐÂY, TRƯỚC sendMail, vì đây là chỗ duy nhất đã biết "hôm nay có
  // gì mới" — cùng dữ liệu, cùng gate với email. Viết lại diffEvents/weeklyIsNew/
  // diffAnalyses bằng Python là cách chắc chắn để hai kênh lệch nhau sau vài tháng (bài
  // học preview-morning-email.jsc.js: load lại chính file này thay vì copy code).
  // TRƯỚC sendMail chứ không phải sau: Gmail chết thì Telegram vẫn phải tới được.
  // Bọc try/catch — hỏng phần phụ TUYỆT ĐỐI không được làm vỡ email.
  try {
    const payloadPath = process.env.TELEGRAM_PAYLOAD || '/tmp/morning-telegram.json';
    fs.writeFileSync(payloadPath, JSON.stringify({
      ddmm, generatedAt: cur.generatedAt || '', subjBits, webUrl: WEB_URL,
      events: evs.map(d => ({
        kind: d.kind, isNewEvent: !!d.isNewEvent, name: d.ev.name,
        dates: d.ev.dates || '', location: d.ev.location || '',
        items: (d.newItems || []).slice(0, 5).map(it => ({
          title: it.title, sourceUrl: it.sourceUrl || '', sourceName: it.sourceName || '',
        })),
      })),
      weekly: weekly ? {
        weekStart: weekly.weekStart || '', weekEnd: weekly.weekEnd || '',
        // Chỉ thị Huy 02/08/2026: Telegram sáng THÔI liệt kê luận điểm từng nước
        // ("không cần tóm tắt từng nước như vậy, chỉ cần có link trực tiếp đến Báo cáo
        // tuần của từng nước"). Nên payload bỏ `points`, thay bằng LINK SÂU.
        // URL ghép ở ĐÂY chứ không ở phía Python: `WEB_URL` là một nguồn sự thật duy nhất,
        // hai nơi tự ghép thì đổi tên miền là lệch âm thầm.
        // `key` do add_weekly.py đặt (us|cn|ru); thiếu key thì trỏ về mục Báo cáo tuần
        // chung — tới đúng mục vẫn hơn là đưa một link không nhảy được.
        countries: (weekly.countries || []).map(c => ({
          flag: c.flag || '', name: c.name,
          url: WEB_URL + '/#analysis/weekly' + (c.key ? '/' + c.key : ''),
        })),
      } : null,
      analyses: anas.slice(0, ANA_MAX).map(a => ({
        outlet: a.outlet || '', title: a.title, url: a.url || '', takeaway: a.takeaway || '',
      })),
      features: feats.map(f => ({ title: f.title, desc: f.desc || '' })),
      tip: tip ? { title: tip.title, desc: tip.desc || '', path: tip.path || '' } : null,
    }, null, 2), 'utf8');
    console.log(`Đã ghi payload Telegram: ${payloadPath}`);
  } catch (e) {
    console.error('[telegram] không ghi được payload (bỏ qua, email vẫn gửi):', e && e.message);
  }

  // TẮT EMAIL (chỉ thị Huy 27/07/2026: "từ giờ không cần gửi email cho ai nữa, gửi telegram
  // thôi"). Đặt Ở ĐÂY chứ KHÔNG ở đầu main(): payload Telegram được ghi ngay phía trên, và
  // đây là chỗ DUY NHẤT biết "hôm nay có gì mới" — thoát sớm là Telegram sáng chết theo.
  // BẬT LẠI: đổi `GUI_EMAIL: '0'` thành `'1'` trong .github/workflows/notify-morning.yml.
  if (process.env.GUI_EMAIL === '0') {
    console.log('GUI_EMAIL=0 — BỎ QUA gửi email sáng (payload Telegram đã ghi xong ở trên).');
    return;
  }

  const info = await transporter.sendMail({
    from: `"Điểm Tin Thế Giới" <${EMAIL_USER}>`,
    to: EMAIL_TO,
    // Tên email này ĐỔI 27/07/2026 (chỉ thị Huy): trước là "🌏 Bản tin sáng ..." — trùng chữ với
    // bản tin 5 chủ đề phiên sáng sớm (`📰 Điểm Tin Thế Giới BUỔI SÁNG ...`, send-email.js) nên
    // nhìn hộp thư không phân biệt được. Đây KHÔNG phải điểm tin: nội dung là sự kiện ngoại giao
    // có ký kết + cập nhật tập trận (+ báo cáo tuần vào Chủ Nhật) → gọi thẳng tên nội dung, và
    // dùng emoji khác hẳn (🎖️ vs 📰) để liếc là ra.
    subject: `🎖️ Sự kiện & Tập trận ${ddmm} — ${subjBits.join(' + ')}`,
    text: `Sự kiện & Tập trận ${ddmm}.\n\n` + textLines.join('\n') + `\n\nMở trang: ${WEB_URL}`,
    html: buildHtml(evs, weekly, anas, ddmm, feats, tip),
  });
  console.log(`Đã gửi email sáng tới ${EMAIL_TO}: ${info.messageId} (${evs.length} sự kiện, báo cáo tuần: ${weekly ? 'có' : 'không'}, think-tank: ${anas.length}, tính năng mới: ${feats.length}, mẹo: ${tip ? tip.title : 'không'})`);
}

main().catch(e => { console.error('LỖI gửi email sáng:', (e && e.stack) || e); process.exit(1); });

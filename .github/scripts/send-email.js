// Gửi email điểm tin khi bản tin cập nhật.
// Chạy trong GitHub Action notify-email.yml. Trích vài tin đáng chú ý vừa quét được
// từ index.html rồi gửi qua Gmail SMTP. Cần secret EMAIL_USER + EMAIL_APP_PASSWORD.
const fs = require('fs');
const nodemailer = require('nodemailer');

const WEB_URL = 'https://huyneo1101-dotcom.github.io/diem-tin-the-gioi';
const EMAIL_USER = process.env.EMAIL_USER;                 // gmail dùng để gửi
const EMAIL_PASS = process.env.EMAIL_APP_PASSWORD;         // App Password 16 ký tự
const EMAIL_TO = process.env.EMAIL_TO || 'lamgiaphat1603@gmail.com,huyneo1101@gmail.com';
const MAX_ITEMS = parseInt(process.env.EMAIL_MAX_ITEMS || '6', 10);
// Bản kê sản lượng + lý do thiếu chủ đề, do PHIÊN QUÉT ghi ra (xem CLAUDE.md mục
// "Bản kê chủ đề thiếu"). Lý do thiếu là kiến thức của phiên quét, Action không tự suy ra được.
const GAPS_PATH = process.env.GAPS_PATH || 'logs/scan-gaps.json';

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

// Đọc bản kê sản lượng 5 chủ đề + lý do thiếu. Không có file, file lỗi, hoặc file của NGÀY KHÁC
// với bản tin đang gửi -> bỏ mục này (thà thiếu mục còn hơn gửi lý do cũ của hôm trước).
function readGaps(DATA) {
  try {
    if (!fs.existsSync(GAPS_PATH)) {
      console.log(`Không thấy ${GAPS_PATH} — email sẽ không có mục "Chủ đề thiếu và lý do".`);
      return null;
    }
    const g = JSON.parse(fs.readFileSync(GAPS_PATH, 'utf8'));
    if (!g || !Array.isArray(g.topics) || !g.topics.length) {
      console.log(`${GAPS_PATH} không có mảng "topics" — bỏ mục "Chủ đề thiếu và lý do".`);
      return null;
    }
    if (g.date && DATA.generatedAt && g.date !== DATA.generatedAt) {
      console.log(`${GAPS_PATH} là của ngày ${g.date} nhưng bản tin là ${DATA.generatedAt} — bỏ qua để không gửi lý do cũ.`);
      return null;
    }
    return g;
  } catch (e) {
    console.log(`Không đọc được ${GAPS_PATH}: ${e.message} — bỏ mục "Chủ đề thiếu và lý do".`);
    return null;
  }
}

// Chủ đề coi là THIẾU khi phiên quét ghi rõ "thieu": true; không ghi thì suy từ count < min.
function isShort(t) {
  if (typeof t.thieu === 'boolean') return t.thieu;
  return typeof t.count === 'number' && typeof t.min === 'number' && t.count < t.min;
}
function topicCount(t) {
  return `${t.count == null ? '?' : t.count}${t.target ? '/' + t.target : ''}`;
}

function buildGapsHtml(gaps) {
  if (!gaps) return '';
  const tally = gaps.topics
    .map(t => `<span style="white-space:nowrap;">${esc(t.name)} <b style="color:${isShort(t) ? '#b42318' : '#12233b'};">${esc(topicCount(t))}</b></span>`)
    .join('<span style="color:#c8d0da;"> · </span>');
  const short = gaps.topics.filter(isShort);
  const rows = short.map(t => `
    <div style="padding:9px 0;border-bottom:1px solid #f4e3e0;">
      <div style="font-size:14px;font-weight:600;color:#b42318;">${esc(t.name)} — ${esc(topicCount(t))} bài</div>
      <div style="font-size:13px;color:#54606f;margin-top:3px;line-height:1.5;">${esc(t.reason || 'Phiên quét không nêu lý do.')}</div>
    </div>`).join('');
  const gapBlock = short.length
    ? `<div style="font-size:14px;font-weight:700;color:#b42318;margin:2px 0 2px;">⚠️ Chủ đề thiếu và lý do (${short.length}/${gaps.topics.length})</div>${rows}`
    : `<div style="font-size:14px;font-weight:600;color:#046c4e;">✅ Không chủ đề nào thiếu — cả ${gaps.topics.length} chủ đề đạt mục tiêu.</div>`;
  const note = gaps.note
    ? `<div style="font-size:12px;color:#7b8794;margin-top:9px;line-height:1.5;">${esc(gaps.note)}</div>`
    : '';

  return `
    <tr><td style="padding:6px 28px 0;">
      <div style="background:#fbfcfe;border:1px solid #e6eaf0;border-radius:10px;padding:14px 16px;">
        <div style="font-size:12px;color:#7b8794;text-transform:uppercase;letter-spacing:.4px;margin-bottom:7px;">Sản lượng ${gaps.topics.length} chủ đề</div>
        <div style="font-size:13px;color:#12233b;line-height:1.9;margin-bottom:11px;">${tally}</div>
        ${gapBlock}${note}
      </div>
    </td></tr>`;
}

function buildGapsText(gaps) {
  if (!gaps) return '';
  const lines = [`\n--- Sản lượng ${gaps.topics.length} chủ đề ---`];
  for (const t of gaps.topics) lines.push(`${isShort(t) ? '⚠️' : '•'} ${t.name}: ${topicCount(t)} bài`);
  const short = gaps.topics.filter(isShort);
  if (short.length) {
    lines.push(`\n--- Chủ đề thiếu và lý do (${short.length}/${gaps.topics.length}) ---`);
    for (const t of short) lines.push(`• ${t.name} — ${topicCount(t)} bài: ${t.reason || 'không nêu lý do'}`);
  } else {
    lines.push(`\nKhông chủ đề nào thiếu — cả ${gaps.topics.length} chủ đề đạt mục tiêu.`);
  }
  if (gaps.note) lines.push(`\nGhi chú: ${gaps.note}`);
  return lines.join('\n') + '\n';
}

function buildHtml(DATA, items, gaps) {
  const p = (DATA.generatedAt || '').split('-');
  const ddmm = p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : (DATA.generatedAt || '');
  // Chỉ TIÊU ĐỀ (điểm tin nhanh) — KHÔNG tóm tắt; chi tiết đầy đủ nằm trong file Word đính kèm.
  const rows = items.map(it => `
    <tr><td style="padding:11px 0;border-bottom:1px solid #eceff3;">
      <a href="${esc(it.sourceUrl || WEB_URL)}" style="font-size:15px;font-weight:600;color:#12233b;text-decoration:none;line-height:1.45;">
        ${esc(trim(it.title, 150))}
      </a>
      <div style="font-size:12px;color:#9aa4b2;margin-top:4px;">${esc(it._kind)}${it.category ? ' · ' + esc(it.category) : ''}${it.sourceName ? ' · ' + esc(it.sourceName) : ''}</div>
    </td></tr>`).join('');

  return `<!doctype html><html><body style="margin:0;background:#f4f6f9;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e6eaf0;">
        <tr><td style="background:#12233b;padding:22px 28px;">
          <div style="font-size:20px;font-weight:700;color:#ffffff;">📰 Điểm Tin Thế Giới</div>
          <div style="font-size:13px;color:#aebbcf;margin-top:4px;">Điểm tin ${esc(ddmm)} — chi tiết đầy đủ trong file Word đính kèm</div>
        </td></tr>
        <tr><td style="padding:8px 28px 4px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">${rows}</table>
        </td></tr>
        ${buildGapsHtml(gaps)}
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
  const dryRun = process.env.DRY_RUN === '1';
  if (!dryRun && (!EMAIL_USER || !EMAIL_PASS)) {
    console.error('LỖI: thiếu secret EMAIL_USER / EMAIL_APP_PASSWORD.');
    process.exit(1); // lỗi cấu hình -> để job ĐỎ, không nuốt im lặng
  }
  const DATA = extractDATA();
  const items = pickHighlights(DATA);
  if (!items.length) { console.log('Không có tin để gửi — bỏ qua.'); return; }
  const gaps = readGaps(DATA);

  // DRY_RUN=1: in ra nội dung email rồi dừng, KHÔNG gửi. Dùng để kiểm mắt trước khi push.
  if (dryRun) {
    console.log(buildGapsText(gaps) || '(không có mục "Chủ đề thiếu và lý do")');
    fs.writeFileSync('/tmp/email-preview.html', buildHtml(DATA, items, gaps));
    console.log(`${items.length} tin nổi bật · HTML xem tại /tmp/email-preview.html · DRY_RUN nên KHÔNG gửi email.`);
    return;
  }

  const p = (DATA.generatedAt || '').split('-');
  const ddmm = p.length === 3 ? `${p[2]}/${p[1]}` : (DATA.generatedAt || '');
  const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com', port: 465, secure: true,
    auth: { user: EMAIL_USER, pass: EMAIL_PASS },
  });

  // Đính kèm file docx toàn bộ tin vừa quét (do make_docx.py tạo, truyền qua DOCX_PATH)
  const attachments = [];
  const docxPath = process.env.DOCX_PATH;
  if (docxPath && fs.existsSync(docxPath)) {
    attachments.push({ filename: `Diem-tin-ngay-${(DATA.generatedAt || '').replace(/\//g, '-')}.docx`, path: docxPath });
    console.log('Đính kèm docx:', docxPath);
  } else {
    console.log('Không có file docx để đính kèm (DOCX_PATH rỗng hoặc file không tồn tại).');
  }

  const info = await transporter.sendMail({
    from: `"Điểm Tin Thế Giới" <${EMAIL_USER}>`,
    to: EMAIL_TO,
    subject: `📰 Điểm Tin Thế Giới — bản tin ${ddmm} (${items.length} tin nổi bật)`,
    text: `Điểm tin ${ddmm} — chi tiết đầy đủ trong file Word đính kèm.\n\n` +
      items.map(it => `• [${it._kind}${it.category ? ' · ' + it.category : ''}] ${it.title}\n  ${it.sourceName || ''} — ${it.sourceUrl || ''}`).join('\n') +
      buildGapsText(gaps) +
      `\nĐọc toàn bộ: ${WEB_URL}`,
    html: buildHtml(DATA, items, gaps),
    attachments,
  });
  console.log(`Đã gửi email tới ${EMAIL_TO}: ${info.messageId} (${items.length} tin, ${attachments.length} đính kèm)`);
}

main().catch(e => { console.error('LỖI gửi email:', (e && e.stack) || e); process.exit(1); });

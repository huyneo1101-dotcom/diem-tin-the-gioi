// XEM TRƯỚC email sáng mà KHÔNG gửi thật — thay cho `DRY_RUN=1` của send-email.js.
//
// Vì sao là file riêng chạy bằng jsc: máy Huy KHÔNG có `node`, nên không chạy trực tiếp
// send-morning-email.js được. jsc (có sẵn trong macOS) chạy được nếu ta tự stub `require`,
// `process`, `console`. Script này load NGUYÊN send-morning-email.js (không copy code sang
// đây — copy là chắc chắn lệch nhau) rồi gọi buildHtml với dữ liệu THẬT trong index.html.
//
// CHẠY (một lệnh phẳng, đường dẫn tuyệt đối):
//   /System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc \
//     /Users/Huy/Claude/diem-tin-the-gioi/.github/scripts/preview-morning-email.jsc.js \
//     > /Users/Huy/Claude/diem-tin-the-gioi/docs/preview-email-sang-mau4.html
// rồi mở file HTML đó trong trình duyệt.
//
// Nội dung xem trước: sự kiện/tập trận có item mới nhất trong DATA (nhánh "1 tin mới") + một
// dipEvent nhiều item (nhánh "nhiều tin mới") + khối báo cáo tuần MẪU (có đánh dấu rõ, vì báo
// cáo thật chỉ ra Chủ Nhật) + Mới trên web + mẹo của ngày, tất cả đọc từ file thật.
var ROOT = '/Users/Huy/Claude/diem-tin-the-gioi/';
function require(m) {
  if (m === 'fs') return { readFileSync: function (p) { return readFile(p.charAt(0) === '/' ? p : ROOT + p); } };
  if (m === 'nodemailer') return { createTransport: function () { return { sendMail: function () { return { messageId: 'preview' }; } }; } };
  throw new Error('module la: ' + m);
}
// Không có secret -> main() tự thoát sớm; nuốt log của nó để STDOUT chỉ còn HTML.
var process = { env: {}, exit: function () { throw new Error('exit'); } };
var _log = [];
var console = { log: function () { _log.push(Array.prototype.join.call(arguments, ' ')); },
                error: function () { _log.push(Array.prototype.join.call(arguments, ' ')); } };

load(ROOT + '.github/scripts/send-morning-email.js');

var D = extractDATA(readFile(ROOT + 'index.html'));

// Nhánh 1: cuộc tập trận có item mới nhất theo _addedDate/date = generatedAt.
var evs = [];
var pickEx = null;
(D.exercises || []).forEach(function (ex) {
  (ex.items || []).forEach(function (it) {
    if (!pickEx && it.date === D.generatedAt) pickEx = { ev: ex, kind: 'ex', isNewEvent: false, newItems: [it] };
  });
});
if (!pickEx && (D.exercises || []).length) {
  var ex0 = D.exercises[0];
  pickEx = { ev: ex0, kind: 'ex', isNewEvent: false, newItems: (ex0.items || []).slice(0, 1) };
}
if (pickEx) evs.push(pickEx);

// Nhánh 2: một sự kiện ngoại giao nhiều item, để xem cách xếp khi có 2-5 tin mới.
if ((D.dipEvents || []).length) {
  var dip = D.dipEvents[0];
  evs.push({ ev: dip, kind: 'dip', isNewEvent: true, newItems: (dip.items || []).slice(0, 3) });
}

// Báo cáo tuần: dùng bản THẬT nếu DATA có, không thì khối mẫu đã ghi rõ là mẫu.
var weekly = (D.weeklyReport && (D.weeklyReport.countries || []).length) ? D.weeklyReport : {
  weekStart: '(mẫu)', weekEnd: '(mẫu)', countries: [
    { flag: '🇺🇸', name: 'Mỹ', lede: 'KHỐI MẪU — báo cáo tuần thật do agent Opus viết Chủ Nhật.',
      points: [{ title: 'Luận điểm mẫu 1' }, { title: 'Luận điểm mẫu 2' }] },
    { flag: '🇨🇳', name: 'Trung Quốc', points: [{ title: 'Luận điểm mẫu' }] },
    { flag: '🇷🇺', name: 'Nga', points: [{ title: 'Luận điểm mẫu' }] }]
};

var wn = readWhatsNew();
var p = String(D.generatedAt || '').split('-');
var ddmm = p.length === 3 ? (p[2] + '/' + p[1] + '/' + p[0]) : String(D.generatedAt);
print(buildHtml(evs, weekly, ddmm, freshFeatures(wn, D.generatedAt), tipOfDay(wn, D.generatedAt)));

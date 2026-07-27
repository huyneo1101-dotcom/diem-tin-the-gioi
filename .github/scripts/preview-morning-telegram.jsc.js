// XEM TRƯỚC tin nhắn Telegram bản tin SÁNG mà KHÔNG gửi thật, và không cần `node`.
//
// Khác `preview-morning-email.jsc.js` (chỉ gọi buildHtml): file này chạy NGUYÊN `main()`
// của send-morning-email.js với nodemailer + fs giả, nên nó kiểm luôn được đoạn ghi
// payload Telegram — thứ mà kiểm cú pháp không bắt được. Email KHÔNG bị gửi: transport
// là stub, chỉ in ra người nhận.
//
// CHẠY (một lệnh phẳng, đường dẫn tuyệt đối):
//   /System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc \
//     /Users/Huy/Claude/diem-tin-the-gioi/.github/scripts/preview-morning-telegram.jsc.js
// rồi:
//   TELEGRAM_PAYLOAD=/tmp/morning-telegram.json DRY_RUN=1 \
//     python3 /Users/Huy/Claude/diem-tin-the-gioi/.github/scripts/send_telegram.py --morning
var ROOT = '/Users/Huy/Claude/diem-tin-the-gioi/';
var OUT = '/tmp/morning-telegram.json';
var _written = null;

function require(m) {
  if (m === 'fs') return {
    readFileSync: function (p) { return readFile(p.charAt(0) === '/' ? p : ROOT + p); },
    writeFileSync: function (p, data) { _written = { path: p, data: data }; },
  };
  if (m === 'nodemailer') return {
    createTransport: function () {
      return { sendMail: function (o) {
        print('[stub] KHÔNG gửi thật. subject: ' + o.subject);
        return { messageId: 'preview' };
      } };
    }
  };
  throw new Error('module la: ' + m);
}

var process = {
  // Secret giả để main() không thoát sớm; transport là stub nên không có gì rời khỏi máy.
  env: { EMAIL_USER: 'preview@local', EMAIL_APP_PASSWORD: 'x', TELEGRAM_PAYLOAD: OUT },
  exit: function (c) { throw new Error('exit ' + c); },
};
var console = { log: function () { print(Array.prototype.join.call(arguments, ' ')); },
                error: function () { print('ERR ' + Array.prototype.join.call(arguments, ' ')); } };

// ⚠️ `load()` đã tự chạy `main()` (dòng cuối của send-morning-email.js), nên ĐỪNG gọi
// main() lần nữa — gọi thêm là chạy hai lượt, log in đôi và rất dễ đọc nhầm thành lỗi.
// Chỉ cần đợi hết microtask của lượt đó rồi in kết quả.
//
// ⚠️ Bản xem trước KHÔNG set PREV_HTML nên `prev = null`, `diffEvents` coi MỌI sự kiện là
// mới (27/07: 22 sự kiện). Trong CI có PREV_HTML nên con số thật nhỏ hơn nhiều — đừng lấy
// số ở đây để đánh giá độ dài tin nhắn hằng ngày.
load(ROOT + '.github/scripts/send-morning-email.js');

Promise.resolve().then(function () {
  if (!_written) {
    print('KHÔNG ghi payload — nghĩa là hôm nay không có sự kiện/tập trận/think-tank mới, ' +
          'hoặc đoạn ghi payload không chạy. Xem log ở trên để phân biệt.');
    return;
  }
  // jsc không ghi file được -> in ra để chuyển tiếp bằng shell.
  print('=== PAYLOAD (' + _written.path + ') ===');
  print(_written.data);
}, function (e) { print('LỖI: ' + ((e && e.stack) || e)); });

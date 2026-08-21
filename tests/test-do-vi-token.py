#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bản hỏng cho `.github/scripts/do_vi_token.py` — chứng minh 15 ca tự kiểm có răng.

    python3 tests/test-do-vi-token.py

Lớp nguy hiểm nhất của script này không phải phép đo mà là phần IN RA: repo công khai, log
Actions ai cũng đọc được, nên một lần "in thêm cho dễ chẩn đoán" là email của Huy nằm vĩnh viễn
trong log công khai — và không lệnh nào báo lỗi. Ca 7 canh đúng chiều ấy; bảng dưới đây gỡ từng
lớp rồi khẳng định ca tương ứng phải báo không đạt.

⚠ Bảng BAN_HONG nằm ở FILE RIÊNG chứ không chung file với mã nó nhắm tới: chuỗi neo đặt cùng
file sẽ tự xuất hiện thêm một lần ở chính phần khai báo, `count(tim)` luôn ≥ 2 và MỌI bản hỏng
bị từ chối (bài học chung với tests/test-cat-nhe-trang.py và HeThong/test-so-token-api.py).
"""
import hashlib
import importlib.util
import io
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
GOC = REPO / ".github" / "scripts" / "do_vi_token.py"
YML = REPO / ".github" / "workflows" / "do-vi-token.yml"

# (nhãn, chuỗi tìm, chuỗi thay, các ca PHẢI chuyển sang không đạt)
BAN_HONG = [
    (
        # Chiều LỘ DỮ LIỆU — thứ đắt nhất ở đây. "In thêm email cho dễ chẩn đoán" là câu
        # người ta tự nói với mình ngay trước khi đẩy danh tính vào log công khai.
        "in thẳng email ra log (repo công khai, ai cũng đọc được)",
        '    print("dấu hiệu ví : %s" % dau)',
        '    print("dấu hiệu ví : %s (%s)" % (dau, ho_so["account"]["email"]))',
        [7],
    ),
    (
        "in cả tên tổ chức ra log",
        '    print("mức gói     : %s" % tier)',
        '    print("mức gói     : %s · %s" % (tier, ho_so["organization"].get("name", "")))',
        [7],
    ),
    (
        # Chiều FAIL-OPEN: hồ sơ thiếu email vẫn băm chuỗi rỗng thành một dấu hiệu trông rất
        # thật, và bảng in ra đọc y như một lượt đo thành công.
        "hồ sơ thiếu email vẫn băm chuỗi rỗng thành dấu hiệu",
        '    if not email:\n        return None, None, tier, "hồ sơ trả về không có email — chưa đo được ví"',
        "    if False:\n        pass",
        [2],
    ),
    (
        # Chiều ĐOÁN BỪA: ví lạ mà gán đại một nhãn thì mã thoát về 0 và người đọc tin rằng
        # đã nhận ra ví.
        "ví lạ vẫn gán nhãn ví A (đoán bừa, mã thoát về 0)",
        "    return dau, VI_DA_BIET.get(dau), tier, None",
        '    return dau, VI_DA_BIET.get(dau, "ví A (túi Max 5x, chủ cũ của máy Mac)"), tier, None',
        [5, 9],
    ),
    (
        # Chiều GỘP HAI LỖI: token chết và ví lạ là hai chuyện phải đi sửa khác hẳn nhau.
        "gộp mã thoát: ví lạ cũng trả 4 như token chết",
        '    print("⇒ ví LẠ, chưa khai trong VI_DA_BIET — thêm dòng vào bảng rồi chạy lại")\n    return 3',
        '    print("⇒ ví LẠ, chưa khai trong VI_DA_BIET — thêm dòng vào bảng rồi chạy lại")\n    return 4',
        [9],
    ),
    (
        # Chiều IM: thiếu token đọc thành "đo xong, không thấy gì".
        # ⚠ Neo phải kèm dòng LIỀN SAU: sau khi thêm nhánh dấu vân 21/08, đoạn kiểm token
        # rỗng xuất hiện ở CẢ HAI hàm, neo trần khớp 2 chỗ và bản hỏng bị từ chối.
        "thiếu token vẫn đi gọi API — nhánh danh tính",
        '    if not token:\n        return None, "thiếu token: biến CLAUDE_CODE_OAUTH_TOKEN rỗng"\n    if mo is not None:\n        return mo(token)\n    req = urllib.request.Request(API,',
        "    req = urllib.request.Request(API,",
        [1],
    ),
    (
        "thiếu token vẫn đi gọi API — nhánh dấu vân hạn mức",
        '    if not token:\n        return None, "thiếu token: biến CLAUDE_CODE_OAUTH_TOKEN rỗng"\n    if mo is not None:\n        return mo(token)\n    body = json.dumps(',
        "    body = json.dumps(",
        [10],
    ),
    (
        # Chiều CẮT PHÉP ĐO: bỏ mức gói là mất đúng thứ phân biệt hai túi khi bảng băm chưa
        # kịp khai ví mới.
        "bỏ dòng in mức gói (mất phép phân biệt hai túi)",
        '    print("mức gói     : %s" % tier)\n',
        "",
        [8],
    ),
    (
        # Chiều LỘ Ở NHÁNH THỨ HAI: nhánh dấu vân mới thêm 21/08 là chỗ dễ quên nhất — ca 7
        # chỉ canh nhánh danh tính, nên phải có ca 13 và bản hỏng riêng cho nhánh này.
        "nhánh dấu vân in luôn cả email lấy từ hồ sơ",
        '        print("mốc reset tuần : %s" % van["reset_7d"])',
        '        print("mốc reset tuần : %s (%s)" % (van["reset_7d"], van.get("email", "")))',
        [13],
    ),
    (
        # Chiều MẤT PHÉP SO: bỏ mốc reset tuần là bỏ đúng thứ duy nhất phân biệt được hai ví
        # khi endpoint danh tính đã trả 403.
        "bỏ dòng in mốc reset tuần (mất hẳn phép so hai ví)",
        '        print("mốc reset tuần : %s" % van["reset_7d"])\n',
        "",
        [13, 14],
    ),
    (
        # Chiều FAIL-OPEN: header thiếu mốc tuần vẫn trả vân cụt, bảng in ra "mốc: None" mà
        # mã thoát vẫn 0.
        "header thiếu mốc reset tuần vẫn trả vân cụt (mã thoát 0)",
        '    if not van["reset_7d"]:\n        return None, "header không có mốc reset tuần — chưa đo được dấu vân ví"',
        "    if False:\n        pass",
        [12],
    ),
    (
        # Chiều GỘP: hai nhánh cùng trượt mà vẫn trả 0 thì lượt đo hỏng đọc y như lượt đo xong.
        "cả hai nhánh trượt vẫn trả mã 0",
        '            print("⛔ CHƯA ĐO ĐƯỢC ví của token CI — %s" % loi2)\n            return 4',
        '            print("⛔ CHƯA ĐO ĐƯỢC ví của token CI — %s" % loi2)\n            return 0',
        [15],
    ),
    (
        # Chiều BĂM CỤT: cắt dấu hiệu còn 2 ký tự thì hai ví khác nhau đụng nhau rất dễ, mà
        # bảng in ra vẫn trông bình thường.
        "cắt dấu hiệu băm còn 1 ký tự (hai ví đụng nhau)",
        'dau = hashlib.sha256(email.encode("utf-8")).hexdigest()[:12]',
        'dau = hashlib.sha256(email.encode("utf-8")).hexdigest()[:1]',
        [3, 4],
    ),
]


def ca_workflow_khong_goi_model(ten_file: str) -> str:
    """Job này phải RẺ. Ngày nào đó ai đó thêm `npm install -g @anthropic-ai/claude-code` vào
    cho tiện là phép đo tự nó bắt đầu đốt hạn mức của chính ví đang đo."""
    y = YML.read_text(encoding="utf-8")
    for cam in ("claude-code", "claude -p", "anthropic-ai"):
        if cam in y:
            return "workflow có '%s' — job đo ví lại đi gọi model, đốt đúng ví đang đo" % cam
    if "workflow_dispatch" not in y:
        return "workflow thiếu workflow_dispatch — không chạy tay được"
    if "schedule" in y or "cron" in y:
        return "workflow có lịch chạy — phép đo một lần không được tự chạy hằng ngày"
    return ""


def _chay_tu_kiem(duong):
    ten = "banhong_%d" % abs(hash(duong))
    spec = importlib.util.spec_from_file_location(ten, duong)
    mo = importlib.util.module_from_spec(spec)
    cu_argv, cu_out = sys.argv, sys.stdout
    sys.argv = ["x"]
    sys.stdout = io.StringIO()
    try:
        spec.loader.exec_module(mo)
        do_ = []
        for so, _ten, fn in mo.CAC_CA:
            try:
                if not bool(fn()):
                    do_.append(so)
            except Exception:  # noqa: BLE001
                do_.append(so)
        return do_
    finally:
        sys.argv, sys.stdout = cu_argv, cu_out


def main():
    loi_yml = ca_workflow_khong_goi_model("")
    print("=== Ca soi workflow ===")
    print(("✅ workflow đo ví không gọi model, chạy tay" if not loi_yml
           else "❌ %s" % loi_yml))
    if loi_yml:
        return 2

    r = subprocess.run([sys.executable, str(GOC), "--tu-kiem"], capture_output=True, text=True)
    print("\n" + r.stdout.strip())
    if r.returncode != 0:
        print("\nBản ĐÚNG đã không đạt — sửa nó trước.")
        return 2

    goc = GOC.read_text(encoding="utf-8")
    print("\n=== BẢN HỎNG — %d bản ===\n" % len(BAN_HONG))
    truot = 0
    for nhan, tim, thay, can_do in BAN_HONG:
        dem = goc.count(tim)
        if dem != 1:
            print("  ✗ %s — chuỗi neo khớp %d chỗ (phải đúng 1)" % (nhan, dem))
            truot += 1
            continue
        noi_dung = goc.replace(tim, thay)
        ma = hashlib.sha1(noi_dung.encode("utf-8")).hexdigest()[:8]
        p = REPO / "tests" / ("_thu-hong-%d-%s-do-vi-token.py" % (os.getpid(), ma))
        try:
            p.write_text(noi_dung, encoding="utf-8")
            do_ = _chay_tu_kiem(str(p))
        finally:
            try:
                p.unlink()
            except OSError:
                pass
        thieu = [c for c in can_do if c not in do_]
        if thieu:
            print("  ✗ %s — ca %s VẪN đạt (đỏ thực tế: %s)" % (nhan, thieu, do_))
            truot += 1
        else:
            print("  ✓ %s — bắt được, ca đỏ: %s" % (nhan, do_))

    print("\n%s" % ("%d/%d bản hỏng đều bị bắt" % (len(BAN_HONG), len(BAN_HONG)) if not truot
                    else "✗ %d/%d bản hỏng KHÔNG bị bắt" % (truot, len(BAN_HONG))))
    return 0 if not truot else 1


if __name__ == "__main__":
    raise SystemExit(main())

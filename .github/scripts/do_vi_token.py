#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Đo VÍ nào đang trả tiền cho token CI — in dấu hiệu ẩn danh, không in danh tính.

VÌ SAO CẦN (21/08/2026): metadata của GitHub Secrets không khai chủ token, nên câu hỏi "CI đang
đốt hạn mức của tài khoản nào" không có cách trả lời nào ngoài suy đoán. Ngày 21/08 máy Mac
chuyển sang một túi khác, túi cũ còn nguyên đăng nhập mà không nằm trên đường rút nào, trong khi
túi mới nhảy từ 9% lên 24% trong 32 giờ mà máy Mac không hề rút — không đo được thì chỉ có nghi.

⛔ REPO NÀY CÔNG KHAI, LOG ACTIONS AI CŨNG ĐỌC ĐƯỢC. Vì vậy chỉ in:
  - 12 ký tự đầu của sha256(email) — đủ để đối chiếu với bảng dưới đây, không lần ngược ra email;
  - `rate_limit_tier` do API khai (mức gói, không phải danh tính).
Cấm in email, tên, uuid tổ chức, và tất nhiên cấm in token.

    python3 .github/scripts/do_vi_token.py          # đọc CLAUDE_CODE_OAUTH_TOKEN từ môi trường
    python3 .github/scripts/do_vi_token.py --tu-kiem

Mã thoát: 0 nhận ra ví · 3 token sống nhưng ví LẠ (chưa khai trong bảng) · 4 chưa đo được
(thiếu token, mạng hỏng, token chết). Ba mức tách rời vì cả ba đều "không in ra tên ví" nếu
đọc ẩu, mà chỉ một trong ba là chuyện đáng đi sửa.
"""
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.anthropic.com/api/oauth/profile"

# Bảng ví đã biết: 12 ký tự đầu sha256(email) → nhãn ngắn. Thêm ví mới thì thêm dòng ở đây;
# hash không lần ngược ra email được nên để trong repo công khai vẫn an toàn.
VI_DA_BIET = {
    "4b0e43b25e68": "ví A (túi Max 5x, chủ cũ của máy Mac)",
    "fc00b51b4530": "ví B (túi Max 20x, chủ hiện hành của máy Mac)",
}


def lay_ho_so(token, mo=None):
    """Trả (dict hồ sơ, lỗi). `mo` là hàm tiêm cho tự kiểm — CHỈ dùng trong `--tu-kiem`."""
    if not token:
        return None, "thiếu token: biến CLAUDE_CODE_OAUTH_TOKEN rỗng"
    if mo is not None:
        return mo(token)
    req = urllib.request.Request(API, headers={
        "Authorization": "Bearer " + token,
        "anthropic-beta": "oauth-2025-04-20",
        "User-Agent": "claude-cli/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, "API trả mã %d (token hết hạn hoặc bị thu hồi?)" % e.code
    except Exception as e:  # noqa: BLE001
        return None, "không gọi được API: %s" % type(e).__name__


def doc_ho_so(ho_so):
    """Bóc đúng hai thứ được phép in. Trả (dấu_hiệu, nhãn_ví, tier, lỗi).

    ⛔ Hồ sơ thiếu email thì trả LỖI, không trả dấu hiệu của chuỗi rỗng: sha256("") là một
    hằng số hợp lệ, nên nhánh fail-open ở đây sẽ in ra một dấu hiệu trông rất thật.
    """
    email = ((ho_so or {}).get("account") or {}).get("email") or ""
    tier = ((ho_so or {}).get("organization") or {}).get("rate_limit_tier") or "(không khai)"
    if not email:
        return None, None, tier, "hồ sơ trả về không có email — chưa đo được ví"
    dau = hashlib.sha256(email.encode("utf-8")).hexdigest()[:12]
    return dau, VI_DA_BIET.get(dau), tier, None


def main(argv):
    if "--tu-kiem" in argv:
        return tu_kiem()
    ho_so, loi = lay_ho_so(os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "").strip())
    if loi:
        print("⛔ CHƯA ĐO ĐƯỢC ví của token CI — %s" % loi)
        return 4
    dau, nhan, tier, loi = doc_ho_so(ho_so)
    if loi:
        print("⛔ CHƯA ĐO ĐƯỢC ví của token CI — %s" % loi)
        return 4
    print("dấu hiệu ví : %s" % dau)
    print("mức gói     : %s" % tier)
    if nhan:
        print("⇒ token CI đang rút %s" % nhan)
        return 0
    print("⇒ ví LẠ, chưa khai trong VI_DA_BIET — thêm dòng vào bảng rồi chạy lại")
    return 3


# ─────────────────────────────────────────────────────────────── tự kiểm
CAC_CA = []


def ca(so, ten):
    def deco(fn):
        CAC_CA.append((so, ten, fn))
        return fn
    return deco


def _ho_so(email, tier="default_claude_max_20x"):
    return {"account": {"email": email}, "organization": {"rate_limit_tier": tier}}


@ca(1, "PHẢI KÊU — thiếu token thì báo chưa đo được, không im lặng trả 0")
def _c1():
    _, loi = lay_ho_so("")
    return bool(loi) and "thiếu token" in loi


@ca(2, "PHẢI KÊU — hồ sơ không có email thì báo lỗi, KHÔNG băm chuỗi rỗng thành dấu hiệu")
def _c2():
    dau, nhan, _tier, loi = doc_ho_so({"account": {}, "organization": {}})
    return dau is None and nhan is None and bool(loi)


@ca(3, "nhận đúng ví A qua dấu hiệu băm")
def _c3():
    dau, nhan, _t, loi = doc_ho_so(_ho_so("huyneo1101@gmail.com"))
    return loi is None and dau == "4b0e43b25e68" and nhan and nhan.startswith("ví A")


@ca(4, "nhận đúng ví B qua dấu hiệu băm")
def _c4():
    dau, nhan, _t, loi = doc_ho_so(_ho_so("chidoanbusiness@gmail.com"))
    return loi is None and dau == "fc00b51b4530" and nhan and nhan.startswith("ví B")


@ca(5, "PHẢI KÊU — ví lạ thì trả nhãn rỗng để bên gọi thoát mã 3, không đoán bừa")
def _c5():
    dau, nhan, _t, loi = doc_ho_so(_ho_so("ai-do-hoan-toan-khac@example.com"))
    return loi is None and dau and nhan is None


@ca(6, "[đối chứng] hai email khác nhau KHÔNG ra cùng dấu hiệu")
def _c6():
    a = doc_ho_so(_ho_so("huyneo1101@gmail.com"))[0]
    b = doc_ho_so(_ho_so("chidoanbusiness@gmail.com"))[0]
    return a != b


@ca(7, "⛔ đầu ra KHÔNG chứa email, tên hay uuid (log Actions của repo công khai)")
def _c7():
    import contextlib
    import io as _io
    ho_so = {"account": {"email": "huyneo1101@gmail.com", "full_name": "Ho Ten That",
                         "uuid": "aaaa-bbbb"},
             "organization": {"rate_limit_tier": "default_claude_max_5x",
                              "uuid": "cccc-dddd", "name": "Ten To Chuc"}}
    goc = globals()["lay_ho_so"]
    globals()["lay_ho_so"] = lambda t, mo=None: (ho_so, None)
    os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "token-gia"
    b = _io.StringIO()
    try:
        with contextlib.redirect_stdout(b):
            ma = main([])
    finally:
        globals()["lay_ho_so"] = goc
        os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    ra = b.getvalue()
    cam = ["huyneo1101@gmail.com", "gmail.com", "Ho Ten That", "aaaa-bbbb", "cccc-dddd",
           "Ten To Chuc", "token-gia"]
    return ma == 0 and not any(c in ra for c in cam)


@ca(8, "[đối chứng] mức gói VẪN được in — bỏ nó là mất phép phân biệt hai túi")
def _c8():
    import contextlib
    import io as _io
    goc = globals()["lay_ho_so"]
    globals()["lay_ho_so"] = lambda t, mo=None: (
        _ho_so("huyneo1101@gmail.com", "default_claude_max_5x"), None)
    os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "x"
    b = _io.StringIO()
    try:
        with contextlib.redirect_stdout(b):
            main([])
    finally:
        globals()["lay_ho_so"] = goc
        os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    return "default_claude_max_5x" in b.getvalue()


@ca(9, "PHẢI KÊU — token chết trả mã 4, ví lạ trả mã 3 (hai chuyện khác nhau)")
def _c9():
    import contextlib
    import io as _io
    goc = globals()["lay_ho_so"]
    os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "x"
    b = _io.StringIO()
    try:
        globals()["lay_ho_so"] = lambda t, mo=None: (None, "API trả mã 401")
        with contextlib.redirect_stdout(b):
            ma_chet = main([])
        globals()["lay_ho_so"] = lambda t, mo=None: (_ho_so("la@example.com"), None)
        with contextlib.redirect_stdout(b):
            ma_la = main([])
    finally:
        globals()["lay_ho_so"] = goc
        os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    return ma_chet == 4 and ma_la == 3


def tu_kiem():
    print("=== TỰ KIỂM ĐO VÍ TOKEN CI — %d ca ===\n" % len(CAC_CA))
    do_ = []
    for so, ten, fn in CAC_CA:
        try:
            ok = bool(fn())
        except Exception as e:  # noqa: BLE001
            print("  ✗ [%d] %s\n      LỖI: %s" % (so, ten, e))
            do_.append(so)
            continue
        print("  %s [%d] %s" % ("✓" if ok else "✗", so, ten))
        if not ok:
            do_.append(so)
    print("\n%d/%d ca đạt%s" % (len(CAC_CA) - len(do_), len(CAC_CA),
                                (" — KHÔNG ĐẠT: %s" % do_) if do_ else ""))
    return 0 if not do_ else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Đo VÍ nào đang trả tiền cho token CI — in dấu hiệu ẩn danh, không in danh tính.

VÌ SAO CẦN (21/08/2026): metadata của GitHub Secrets không khai chủ token, nên câu hỏi "CI đang
đốt hạn mức của tài khoản nào" không có cách trả lời nào ngoài suy đoán. Ngày 21/08 máy Mac
chuyển sang một túi khác, túi cũ còn nguyên đăng nhập mà không nằm trên đường rút nào, trong khi
túi mới nhảy từ 9% lên 24% trong 32 giờ mà máy Mac không hề rút — không đo được thì chỉ có nghi.

HAI NHÁNH, đi lần lượt: (1) hỏi endpoint danh tính — chỉ chạy được với access token của
phiên đăng nhập; (2) token do `claude setup-token` sinh có scope hẹp, endpoint ấy trả **403**,
nên lùi sang đọc **mốc reset tuần** trong header hạn mức. Mốc đó gắn với chu kỳ riêng của từng
tài khoản: TRÙNG mốc của máy Mac là chung ví, LỆCH là khác ví.

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

# SỐ ĐO 21/08/2026 lúc 15:54 giờ VN — mốc để lượt sau đối chiếu, đừng đo lại từ đầu:
#   máy Mac (ví B): reset tuần 1787684400 = 26/08 02:00 · reset 5 giờ 1787307000 = 21/08 17:10
#   token CI      : reset tuần 1787335200 = 22/08 01:00 · reset 5 giờ 1787310000 = 21/08 18:00
# Hai mốc tuần LỆCH ⇒ CI KHÔNG rút cùng ví với máy Mac, tức đang rút ví A. Cùng lượt đo, CI
# khai tuần đã dùng 0.87 — túi ấy sắp cạn trước mốc reset 22/08 01:00.


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


MESSAGES = "https://api.anthropic.com/v1/messages"


def dau_van_han_muc(token, mo=None):
    """Dấu vân TÀI KHOẢN đọc từ header hạn mức. Trả (dict, lỗi).

    VÌ SAO CẦN NHÁNH NÀY (đo 21/08/2026): token do `claude setup-token` sinh ra có scope hẹp,
    endpoint danh tính trả **403** cho nó — nhánh hồ sơ ở trên chỉ chạy được với access token
    của phiên đăng nhập. Nhánh này không hỏi danh tính mà đọc `anthropic-ratelimit-unified-*`:
    **mốc reset tuần** (`7d-reset`) gắn với chu kỳ riêng của từng tài khoản, nên hai ví khác
    nhau cho hai mốc khác nhau — đủ để trả lời "CI có rút cùng ví với máy không" mà không cần
    biết ví đó của ai.

    Tốn đúng 01 lời gọi `max_tokens: 1` — vài token, không phải một phiên quét.
    """
    if not token:
        return None, "thiếu token: biến CLAUDE_CODE_OAUTH_TOKEN rỗng"
    if mo is not None:
        return mo(token)
    body = json.dumps({"model": "claude-haiku-4-5-20251001", "max_tokens": 1,
                       "messages": [{"role": "user", "content": "hi"}]}).encode()
    req = urllib.request.Request(MESSAGES, data=body, headers={
        "Authorization": "Bearer " + token,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "oauth-2025-04-20",
        "Content-Type": "application/json",
        "User-Agent": "claude-cli/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            h = dict(r.headers)
    except urllib.error.HTTPError as e:
        h = dict(e.headers)
        if not any("ratelimit-unified" in k.lower() for k in h):
            return None, "API trả mã %d và không kèm header hạn mức" % e.code
    except Exception as e:  # noqa: BLE001
        return None, "không gọi được API: %s" % type(e).__name__
    return boc_van(h)


def boc_van(h):
    """Bóc dấu vân từ header. Tách thành hàm THUẦN để `--tu-kiem` đi qua ĐÚNG đoạn mã này —
    ca tiêm sẵn kết quả ở tầng trên thì gỡ chính nhánh dưới đây đi mà ca vẫn xanh."""
    lay = lambda k: h.get("anthropic-ratelimit-unified-" + k)  # noqa: E731
    van = {"reset_7d": lay("7d-reset"), "reset_5h": lay("5h-reset"),
           "dung_7d": lay("7d-utilization"), "dung_5h": lay("5h-utilization")}
    if not van["reset_7d"]:
        return None, "header không có mốc reset tuần — chưa đo được dấu vân ví"
    return van, None


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
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "").strip()
    ho_so, loi = lay_ho_so(token)
    if not loi:
        dau, nhan, tier, loi = doc_ho_so(ho_so)
    if loi:
        # Nhánh danh tính trượt (token scope hẹp trả 403) ⇒ lùi sang dấu vân hạn mức. In lý do
        # trượt chứ không nuốt: hai nhánh hỏng vì hai cớ khác nhau, gộp lại là đi sửa nhầm hướng.
        print("ℹ nhánh danh tính không dùng được — %s" % loi)
        van, loi2 = dau_van_han_muc(token)
        if loi2:
            print("⛔ CHƯA ĐO ĐƯỢC ví của token CI — %s" % loi2)
            return 4
        print("mốc reset tuần : %s" % van["reset_7d"])
        print("mốc reset 5 giờ: %s" % van["reset_5h"])
        print("đã dùng        : tuần %s · cửa sổ 5 giờ %s" % (van["dung_7d"], van["dung_5h"]))
        print("⇒ so mốc reset tuần này với mốc của máy Mac: TRÙNG là chung ví, LỆCH là khác ví")
        return 0
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


# ─── nhánh DẤU VÂN HẠN MỨC (thêm 21/08/2026 sau khi đo được endpoint danh tính trả 403
# cho token scope hẹp). Mọi ca TIÊM header giả, không gọi mạng.
def _hdr(**kw):
    h = {"anthropic-ratelimit-unified-7d-reset": "1787684400",
         "anthropic-ratelimit-unified-5h-reset": "1787307000",
         "anthropic-ratelimit-unified-7d-utilization": "0.35",
         "anthropic-ratelimit-unified-5h-utilization": "0.48"}
    h.update(kw)
    return h


@ca(10, "PHẢI KÊU — thiếu token thì nhánh dấu vân cũng báo, không đi gọi API")
def _c10():
    _, loi = dau_van_han_muc("")
    return bool(loi) and "thiếu token" in loi


@ca(11, "bóc đủ 04 trường dấu vân từ header hạn mức")
def _c11():
    van, loi = boc_van(_hdr())
    return loi is None and van["reset_7d"] == "1787684400" and van["dung_5h"] == "0.48"


@ca(12, "PHẢI KÊU — header thiếu mốc reset tuần thì báo chưa đo được, không trả vân cụt")
def _c12():
    van, loi = boc_van(_hdr(**{"anthropic-ratelimit-unified-7d-reset": ""}))
    return van is None and bool(loi)


@ca(13, "⛔ nhánh dấu vân cũng KHÔNG in danh tính (log Actions của repo công khai)")
def _c13():
    import contextlib
    import io as _io
    goc_hs, goc_van = globals()["lay_ho_so"], globals()["dau_van_han_muc"]
    globals()["lay_ho_so"] = lambda t, mo=None: (None, "API trả mã 403")
    globals()["dau_van_han_muc"] = lambda t, mo=None: (
        {"reset_7d": "1787684400", "reset_5h": "1787307000",
         "dung_7d": "0.35", "dung_5h": "0.48",
         "email": "huyneo1101@gmail.com", "ten": "Ho Ten That"}, None)
    os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "token-gia"
    b = _io.StringIO()
    try:
        with contextlib.redirect_stdout(b):
            ma = main([])
    finally:
        globals()["lay_ho_so"], globals()["dau_van_han_muc"] = goc_hs, goc_van
        os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    ra = b.getvalue()
    cam = ["huyneo1101@gmail.com", "gmail.com", "Ho Ten That", "token-gia"]
    return ma == 0 and "1787684400" in ra and not any(c in ra for c in cam)


@ca(14, "[đối chứng] mốc reset tuần VẪN được in — bỏ nó là mất hẳn phép so hai ví")
def _c14():
    import contextlib
    import io as _io
    goc_hs, goc_van = globals()["lay_ho_so"], globals()["dau_van_han_muc"]
    globals()["lay_ho_so"] = lambda t, mo=None: (None, "API trả mã 403")
    globals()["dau_van_han_muc"] = lambda t, mo=None: (
        {"reset_7d": "1787684400", "reset_5h": "1787307000",
         "dung_7d": "0.35", "dung_5h": "0.48"}, None)
    os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "x"
    b = _io.StringIO()
    try:
        with contextlib.redirect_stdout(b):
            main([])
    finally:
        globals()["lay_ho_so"], globals()["dau_van_han_muc"] = goc_hs, goc_van
        os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    return "1787684400" in b.getvalue()


@ca(15, "PHẢI KÊU — cả hai nhánh đều trượt thì mã thoát 4, không phải 0")
def _c15():
    import contextlib
    import io as _io
    goc_hs, goc_van = globals()["lay_ho_so"], globals()["dau_van_han_muc"]
    globals()["lay_ho_so"] = lambda t, mo=None: (None, "API trả mã 403")
    globals()["dau_van_han_muc"] = lambda t, mo=None: (None, "không gọi được API")
    os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "x"
    b = _io.StringIO()
    try:
        with contextlib.redirect_stdout(b):
            ma = main([])
    finally:
        globals()["lay_ho_so"], globals()["dau_van_han_muc"] = goc_hs, goc_van
        os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    return ma == 4


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

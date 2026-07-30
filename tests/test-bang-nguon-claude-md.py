#!/usr/bin/env python3
"""Cổng canh việc ĐỌC BẢNG NGUỒN từ CLAUDE.md — `harvest.py` lấy feed và trang HTML ở đâu.

VÌ SAO CÓ BỘ NÀY (bug thật 30/07/2026, hỏng CÂM hoàn hảo): `html_pages_from_claude_md()` định vị
bảng bằng `text.index("TRANG HTML QUÉT TRỰC TIẾP")`, tức lần xuất hiện ĐẦU TIÊN của chuỗi. Chỉ cần
một câu VĂN XUÔI nhắc tên bảng (`nay cả 06 nằm trong bảng "🕸️ TRANG HTML QUÉT TRỰC TIẾP"`) đứng
trước bảng thật là hàm cắt lấy đoạn văn ấy và trả về **0 trang** — lớp [HTML] chết sạch. Không ném
lỗi, không cảnh báo, mà bảng trong CLAUDE.md vẫn còn nguyên 25 dòng nên soi bằng mắt thì thấy đủ.
Đo thật lúc bắt được: **25 trang -> 0**, và lớp RSS ăn thêm 31 request vô ích (83 feed -> 114).

Đây đúng loại "hỏng thì im lặng cho qua": bảng rỗng và hôm nay không có nguồn nào trông y hệt nhau.
Nên bộ test phải có ca PHẢI ĐỎ dựng đúng điều kiện xấu, không chỉ ca "chạy được".

Chạy:  python3 tests/test-bang-nguon-claude-md.py
       python3 tests/test-bang-nguon-claude-md.py --tu-kiem
"""
import argparse
import contextlib
import io
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# Bảng nguồn thật của repo, dùng làm nền cho mọi ca — tái sử dụng văn bản đã sạch thay vì bịa mới
# (bịa mới rất dễ trượt vì lý do khác, rồi đo nhầm cổng mà vẫn tưởng đã chặn).
CLAUDE_THAT = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

KEY = "TRANG HTML QUÉT TRỰC TIẾP"

# Câu văn xuôi nhắc tên bảng — chính là thứ đã gây bug. Chèn vào TRƯỚC bảng.
CAU_NHAC = (
    '\nCả 06 trang quân chủng nay nằm trong bảng **"🕸️ ' + KEY + '"** và `harvest.py` quét chúng '
    "qua lớp `[HTML]`.\n"
)


def _nap_harvest(thu_muc):
    """Nạp harvest với ROOT ghim vào thư mục chứa CLAUDE.md của ca thử.

    Ghim bằng cách gán `harvest.ROOT` chứ không copy script: bản hỏng của `--tu-kiem` phải là
    bản trên đĩa thật của harvest, nếu không phép tráo bản hỏng sẽ không đụng tới được.
    """
    mod = os.environ.get("HARVEST_MOD", "harvest")
    for k in list(sys.modules):
        if k == mod:
            del sys.modules[k]
    h = __import__(mod)
    h.ROOT = pathlib.Path(thu_muc)
    return h


def _dung_kho(noi_dung):
    d = tempfile.mkdtemp(prefix=f"thu-bang-{os.getpid()}-")
    (pathlib.Path(d) / "CLAUDE.md").write_text(noi_dung, encoding="utf-8")
    return d


def _do(noi_dung, la_ci=False):
    """Trả (số trang HTML, số feed). Bắt stderr để dòng '[HTML] bỏ qua...' không lẫn vào bảng."""
    d = _dung_kho(noi_dung)
    cu = os.environ.get("GITHUB_ACTIONS")
    try:
        if la_ci:
            os.environ["GITHUB_ACTIONS"] = "1"
        else:
            os.environ.pop("GITHUB_ACTIONS", None)
        h = _nap_harvest(d)
        with contextlib.redirect_stderr(io.StringIO()):
            trang = h.html_pages_from_claude_md()
            feed = h.feeds_from_claude_md()
        return len(trang), len(feed), trang
    finally:
        if cu is None:
            os.environ.pop("GITHUB_ACTIONS", None)
        else:
            os.environ["GITHUB_ACTIONS"] = cu
        shutil.rmtree(d, ignore_errors=True)


def _chen_truoc_bang(text, cau):
    """Chèn `cau` vào ngay TRƯỚC dòng tiêu đề của bảng HTML."""
    m = None
    for mm in re.finditer(r"^#{2,4} .*$", text, re.M):
        if KEY in mm.group(0):
            m = mm
            break
    assert m, "không tìm thấy tiêu đề bảng HTML trong CLAUDE.md thật"
    return text[: m.start()] + cau + text[m.start():]


CAC_CA = []


def ca(so, ten):
    def deco(f):
        CAC_CA.append((so, ten, f))
        return f
    return deco


# ───────────────────────── ca PHẢI CHẶN (dựng đúng điều kiện xấu) ─────────────────────────

@ca(1, "PHẢI CHẶN: câu văn xuôi nhắc tên bảng TRƯỚC bảng -> vẫn phải đọc đủ trang")
def _c1():
    goc, _, _ = _do(CLAUDE_THAT)
    hong, _, _ = _do(_chen_truoc_bang(CLAUDE_THAT, CAU_NHAC))
    assert goc > 20, f"nền sai: bảng thật chỉ ra {goc} trang"
    assert hong == goc, f"nhắc tên bảng làm số trang tụt {goc} -> {hong}"
    return f"{goc} trang, không đổi khi có câu nhắc"


@ca(2, "PHẢI CHẶN: nhắc tên bảng KHÔNG được làm lớp RSS ăn thêm dòng bảng HTML")
def _c2():
    _, feed_goc, _ = _do(CLAUDE_THAT)
    _, feed_hong, _ = _do(_chen_truoc_bang(CLAUDE_THAT, CAU_NHAC))
    assert feed_hong == feed_goc, f"số feed đổi {feed_goc} -> {feed_hong} (bảng HTML lọt vào lớp RSS)"
    return f"{feed_goc} feed, không đổi"


@ca(3, "PHẢI CHẶN: nhắc tên bảng NHIỀU LẦN, cả trước lẫn sau bảng")
def _c3():
    goc, _, _ = _do(CLAUDE_THAT)
    t = _chen_truoc_bang(CLAUDE_THAT, CAU_NHAC + CAU_NHAC) + CAU_NHAC
    hong, _, _ = _do(t)
    # NGƯỠNG TUYỆT ĐỐI, không chỉ so hai phía với nhau: CLAUDE.md thật NAY ĐÃ chứa một câu nhắc
    # tên bảng, nên trên bản hỏng cả `goc` lẫn `hong` đều ra 0 và phép so tương đối vẫn cho ĐẠT.
    # Đã vấp đúng thế lúc dựng — một ca chỉ so tương đối thì mất răng khi lỗi tác động đều hai phía.
    assert hong > 20, f"chỉ còn {hong} trang"
    assert hong == goc, f"{goc} -> {hong}"
    return f"{goc} trang, bền với 3 chỗ nhắc"


@ca(4, "PHẢI CHẶN: bảng HTML phải bị cắt khỏi lớp RSS (feed không chứa url của bảng HTML)")
def _c4():
    _, _, trang = _do(CLAUDE_THAT, la_ci=True)
    d = _dung_kho(CLAUDE_THAT)
    try:
        h = _nap_harvest(d)
        with contextlib.redirect_stderr(io.StringIO()):
            feeds = h.feeds_from_claude_md()
        url_feed = {u for _, u in feeds}
        url_trang = {u for _, u in trang}
        lan = url_feed & url_trang
        assert not lan, f"{len(lan)} url của bảng HTML lọt vào lớp RSS: {sorted(lan)[:3]}"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return f"{len(url_feed)} feed và {len(url_trang)} trang, không giao nhau"


# ───────────────────── ca đối chứng: chống chặn oan / canh hành vi đúng ─────────────────────

@ca(5, "đối chứng: trang cột `CI` bị bỏ ở local, được lấy ở CI")
def _c5():
    n_local, _, _ = _do(CLAUDE_THAT, la_ci=False)
    n_ci, _, _ = _do(CLAUDE_THAT, la_ci=True)
    assert n_ci > n_local, f"CI ({n_ci}) phải nhiều hơn local ({n_local})"
    return f"local {n_local} · CI {n_ci}"


@ca(6, "đối chứng: 06 trang quân chủng .mil có mặt trong bảng khi chạy ở CI")
def _c6():
    _, _, trang = _do(CLAUDE_THAT, la_ci=True)
    urls = " ".join(u for _, u in trang)
    thieu = [d for d in ("pacom.mil", "centcom.mil", "jcs.mil", "news.uscg.mil",
                         "navy.mil", "marines.mil") if d not in urls]
    assert not thieu, f"thiếu khỏi bảng: {thieu}"
    return "đủ 06 trang quân chủng"


@ca(7, "đối chứng: navy.mil và marines.mil là `cả hai` nên LOCAL cũng phải lấy được")
def _c7():
    _, _, trang = _do(CLAUDE_THAT, la_ci=False)
    urls = " ".join(u for _, u in trang)
    thieu = [d for d in ("navy.mil", "marines.mil") if d not in urls]
    assert not thieu, f"local thiếu: {thieu}"
    return "local có navy.mil + marines.mil"


@ca(8, "đối chứng: tên trang không được mang dấu ** của markdown")
def _c8():
    _, _, trang = _do(CLAUDE_THAT, la_ci=True)
    xau = [n for n, _ in trang if "*" in n]
    assert not xau, f"tên còn dấu **: {xau[:3]}"
    return f"{len(trang)} tên sạch"


@ca(9, "đối chứng: CLAUDE.md không có bảng thì trả rỗng, KHÔNG ném lỗi")
def _c9():
    n, _, _ = _do("# tài liệu trống\nkhông có bảng nào.\n")
    assert n == 0, f"phải rỗng, ra {n}"
    return "trả rỗng êm"


@ca(10, "đối chứng: tiêu đề bảng bị đổi chữ -> lùi về nếp cũ, KHÔNG mất bảng")
def _c10():
    # Đổi tiêu đề `### 🕸️ TRANG HTML...` thành dòng thường: hàm phải lùi về text.index và vẫn
    # đọc ra bảng. Fail-open có chủ ý — thà lệch còn hơn làm lớp [HTML] chết câm.
    t = re.sub(r"^(#{2,4}) (.*TRANG HTML QUÉT TRỰC TIẾP.*)$", r"\2", CLAUDE_THAT, count=1, flags=re.M)
    n, _, _ = _do(t, la_ci=True)
    assert n > 20, f"đổi tiêu đề làm mất bảng: {n} trang"
    return f"{n} trang"


BAN_HONG = [
    (
        # Phải gỡ CẢ HAI lớp cùng bảo vệ một hành vi (neo tiêu đề + nhánh chọn khối có nhiều
        # dòng bảng nhất). Gỡ một lớp thì lớp kia gánh và ca vẫn đạt — đã thử và đúng thế.
        "gỡ phép định vị bảng, quay lại text.index — chính bản CŨ có bug",
        [('    for m in re.finditer(r"^#{2,4} .*$", text, re.M):\n'
          "        if key in m.group(0):\n"
          "            return m.start()\n",
          "    return text.index(key)\n")],
        # KHÔNG khai ca 2 (đo số feed): lớp vá này chỉ chi phối đường đọc BẢNG HTML, còn số feed
        # do lớp cắt trong `feeds_from_claude_md` giữ (bản hỏng thứ hai). Khai thừa thì `--tu-kiem`
        # báo trượt vì lý do sai, che mất bản hỏng thật sự không bắt được.
        [1, 3],
    ),
    (
        "lớp RSS KHÔNG cắt bảng HTML ra nữa",
        [("    if KEY_BANG_HTML in block:\n", "    if False:\n")],
        [4],
    ),
    (
        "bỏ chốt lọc trang chỉ-CI khi chạy ở local",
        [("        if ci_only and not la_ci:\n", "        if False:\n")],
        [5],
    ),
    (
        "không bỏ dấu ** khỏi tên trang",
        [('        name = re.sub(r"\\*+", "", cols[1]).strip() if len(cols) > 1 else url',
          "        name = cols[1].strip() if len(cols) > 1 else url")],
        [8],
    ),
]


def chay():
    do = 0
    for so, ten, f in CAC_CA:
        try:
            kq = f()
            print(f"  ✓ [{so}] {ten} — {kq}")
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ [{so}] {ten}\n      {type(e).__name__}: {e}")
            do += 1
    print(f"\n{len(CAC_CA) - do}/{len(CAC_CA)} ca đạt")
    return do


def tu_kiem():
    """Chứng minh bộ ca BẮT ĐƯỢC lỗi: gỡ đúng dòng bảo vệ thì ca đã khai phải không đạt."""
    goc = (ROOT / "scripts" / "harvest.py").read_text(encoding="utf-8")
    tong_truot = 0
    for ten, phep_thay, ca_phai_do in BAN_HONG:
        noi_dung = goc
        loi_thay = None
        for cu, moi in phep_thay:
            if noi_dung.count(cu) != 1:
                loi_thay = f"KHÔNG áp được phép thay: {noi_dung.count(cu)} chỗ khớp"
                break
            noi_dung = noi_dung.replace(cu, moi)
        print(f"\n--- bản hỏng: {ten}")
        if loi_thay:
            print(f"    TRƯỢT — {loi_thay}")
            tong_truot += 1
            continue
        # Bản hỏng phải nằm TRONG thư mục thật của script (harvest tự suy repo root từ __file__
        # và import topics), và tên mang PID để hai phiên chạy chồng không xoá bản hỏng của nhau.
        p = ROOT / "scripts" / f"_thu-hong-{os.getpid()}-harvest.py"
        p.write_text(noi_dung, encoding="utf-8")
        try:
            r = subprocess.run(
                [sys.executable, str(pathlib.Path(__file__).resolve())],
                capture_output=True, text=True,
                env={**os.environ, "HARVEST_MOD": p.stem})
            out = r.stdout
            do = {int(m) for m in re.findall(r"✗ \[(\d+)\]", out)}
            thieu = [c for c in ca_phai_do if c not in do]
            if len(do) == len(CAC_CA):
                print("    TRƯỢT — bản hỏng làm ĐỎ TOÀN BỘ ca: phép thay phá cú pháp/nền, "
                      "không phải gỡ đúng một lớp vá. Sửa lại phép thay.")
                tong_truot += 1
            elif thieu:
                print(f"    TRƯỢT — ca {thieu} VẪN ĐẠT dù đã gỡ lớp vá (ca đỏ thật: {sorted(do)})")
                tong_truot += 1
            else:
                print(f"    ✓ bắt được — ca không đạt: {sorted(do)}")
        finally:
            p.unlink(missing_ok=True)
    print(f"\n=== tự kiểm: {len(BAN_HONG) - tong_truot}/{len(BAN_HONG)} bản hỏng bị bắt")
    return tong_truot


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tu-kiem", action="store_true")
    a = ap.parse_args()
    sys.exit(tu_kiem() if a.tu_kiem else chay())

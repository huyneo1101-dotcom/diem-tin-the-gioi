#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CỔNG "GHI SỔ ĐÃ GỬI CHỊU ĐƯỢC HAI WORKFLOW GHI CÙNG LÚC"
(`.github/scripts/ghi_so_push.py`, dùng chung cho notify-email.yml + notify-morning.yml).

⚠ VÌ SAO CÓ FILE NÀY — sự cố THẬT sáng 30/07/2026:
`notify-morning.yml` ghi `logs/da-gui-email.json` lúc 21:28:01Z, `notify-email.yml` ghi lúc
21:28:08Z — CÁCH NHAU 07 GIÂY, cùng một file. Khối lệnh cũ (chép y nhau ở hai workflow)
commit local rồi `git pull --rebase origin main` ⇒ rebase phải phát lại commit của mình lên
trên commit của workflow kia, hai bên sửa cùng chỗ trong JSON nên XUNG ĐỘT:
`error: could not apply 7209062... (sang)`. Rebase hỏng để repo ở trạng thái rebase dở nên
**cả 5 vòng retry chết tiếp**, chỉ còn `::warning::khong push duoc so da gui`.
Bản tin sáng ĐÃ tới tay lúc 04:28 mà sổ trống ⇒ (a) canary ca `sang` kêu oan + nhắn Telegram;
(b) hai phiên CI dự phòng (05:00 · 05:37) kết luận "mất bản tin" rồi quét lại tốn token.

Đây đúng loại cổng "hỏng thì im lặng" của mục 17 CLAUDE.md: sổ ghi được thì im, mà sổ ghi
KHÔNG được cũng gần như im (chỉ một dòng `::warning::` giữa log CI, còn job vẫn XANH vì
`continue-on-error: true`). Cái kêu lên lại là canary — kêu SAI CHỖ. Vì vậy ca chính ở đây
là ca PHẢI GIỮ ĐƯỢC CẢ HAI DÒNG: dựng đúng điều kiện xấu (workflow kia push trước 7 giây)
rồi khẳng định sổ cuối có ĐỦ dòng của cả hai.

Chạy:
    python3 tests/test-ghi-so-push.py
    python3 tests/test-ghi-so-push.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi

Không cần thư viện ngoài (chỉ cần `git`). Mỗi ca dựng repo git THẬT trong thư mục tạm:
remote bare + 2 clone = hai workflow.
"""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
MOD_THAT = REPO / ".github" / "scripts" / "ghi_so_push.py"

# Seam để --tu-kiem tráo bản hỏng. Mặc định là bản thật.
MOD_PATH = pathlib.Path(os.environ.get("GHISO_MOD") or MOD_THAT)

SO_REL = "logs/da-gui-email.json"


# ───────────────────────── hạ tầng: dựng repo git thật ─────────────────────────
def _git(cwd, *a, kiem=True):
    r = subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True)
    if kiem and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)} rc={r.returncode}: "
                           f"{(r.stderr or r.stdout).strip()[:300]}")
    return r


def _doc_so(p: pathlib.Path):
    return json.loads((p / SO_REL).read_text(encoding="utf-8"))["lan_gui"]


def _ghi_gia(clone: pathlib.Path):
    """Bản giả của so_da_gui.py --ghi: append MỘT dòng vào sổ.

    Cố tình KHÔNG gọi script thật: script thật cần python-docx + index.html + `git show
    HEAD~1`, tức đo cả thứ không thuộc cổng này. Thứ đang đo là logic GIT hợp nhất sổ.
    """
    def f(buoi, chi=None):
        p = clone / SO_REL
        d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"lan_gui": []}
        d["lan_gui"].append({"luc": f"2026-07-30T04:28:0{len(d['lan_gui'])}+07:00",
                             "buoi": buoi,
                             "urls": [f"https://x/{buoi}"]})
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return f


def _nap_mod(clone: pathlib.Path):
    """Nạp module ĐANG THỬ, ghim ROOT vào clone tạm."""
    spec = importlib.util.spec_from_file_location(f"ghi_so_push_thu_{id(clone)}", MOD_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.ROOT = clone
    return m


class Sanh:
    """remote bare + clone A (workflow kia) + clone B (workflow của mình)."""

    def __enter__(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="ghiso-"))
        self.remote = self.tmp / "remote.git"
        _git(self.tmp, "init", "-q", "--bare", "-b", "main", str(self.remote))
        seed = self.tmp / "seed"
        _git(self.tmp, "clone", "-q", str(self.remote), str(seed))
        _git(seed, "config", "user.name", "seed")
        _git(seed, "config", "user.email", "s@x")
        (seed / "logs").mkdir()
        (seed / SO_REL).write_text(json.dumps(
            {"lan_gui": [{"luc": "2026-07-29T21:34:08+07:00", "buoi": "toi",
                          "urls": ["https://x/cu"]}]}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        (seed / "index.html").write_text("BAN CUA REMOTE", encoding="utf-8")
        _git(seed, "add", "-A")
        _git(seed, "commit", "-q", "-m", "seed")
        _git(seed, "push", "-q", "origin", "main")
        self.A = self.tmp / "A"
        self.B = self.tmp / "B"
        for ten in ("A", "B"):
            c = self.tmp / ten
            _git(self.tmp, "clone", "-q", str(self.remote), str(c))
            _git(c, "config", "user.name", ten)
            _git(c, "config", "user.email", f"{ten}@x")
        return self

    def __exit__(self, *e):
        shutil.rmtree(self.tmp, ignore_errors=True)
        return False

    def A_push(self, buoi="sukien"):
        """Workflow KIA ghi sổ rồi push — đúng cái xảy ra trước 7 giây."""
        _git(self.A, "fetch", "-q", "origin", "main")
        _git(self.A, "reset", "-q", "--hard", "FETCH_HEAD")
        _ghi_gia(self.A)(buoi)
        _git(self.A, "add", SO_REL)
        _git(self.A, "commit", "-q", "-m", f"so: {buoi}")
        _git(self.A, "push", "-q", "origin", "HEAD:main")

    def so_tren_remote(self):
        xem = self.tmp / "xem"
        shutil.rmtree(xem, ignore_errors=True)
        _git(self.tmp, "clone", "-q", str(self.remote), str(xem))
        return _doc_so(xem)

    def chay(self, buoi="sang", vong=5, ghi_so=None, chen_o_vong=()):
        """`chen_o_vong` = các vòng mà workflow KIA chen vào giữa fetch và push.

        Chen bằng cách bọc `_git` và bắt đúng lệnh `add` — nó chạy sau fetch/checkout và
        trước commit/push, tức đúng khe hở mà race thật xảy ra, và mỗi vòng gọi đúng một
        lần. Cố tình KHÔNG bọc `_append_dong`: bản hỏng có thể bỏ hẳn hàm đó, lúc ấy seam
        chết theo và ca đỏ vì lý do sai.
        """
        m = _nap_mod(self.B)
        goc = m._git
        dem = {"n": 0}

        def bao(*a, **kw):
            if a and a[0] == "add":
                dem["n"] += 1
                if dem["n"] in chen_o_vong:
                    self.A_push(f"sukien{dem['n']}")
            return goc(*a, **kw)

        m._git = bao
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = m.ghi_va_push(buoi, vong=vong,
                               ghi_so=ghi_so or _ghi_gia(self.B),
                               ngu=lambda s: None)
        return rc, buf.getvalue()


# ────────────────────────────────── các ca ──────────────────────────────────
def ca_race_giu_du_hai_dong():
    """CA CHÍNH — PHẢI GIỮ CẢ HAI DÒNG. Đây là sự cố 30/07 dựng lại nguyên trạng."""
    with Sanh() as s:
        s.A_push("sukien")                       # notify-morning ghi trước 7 giây
        rc, out = s.chay("sang")                 # notify-email ghi sau
        if rc != 0:
            return False, f"rc={rc} (phải 0 — bản cũ rebase chết ở đúng đây)\n{out}"
        buoi = [x["buoi"] for x in s.so_tren_remote()]
        if "sukien" not in buoi:
            return False, f"MẤT dòng của workflow kia: {buoi}"
        if "sang" not in buoi:
            return False, f"MẤT dòng của chính mình: {buoi}"
        return True, buoi


def ca_khong_nhan_doi_dong():
    """PHẢI CHẶN nhân dòng: bị chen ở vòng 1, vòng 2 thành công → đúng MỘT dòng `sang`."""
    with Sanh() as s:
        rc, out = s.chay("sang", chen_o_vong=(1,))
        if rc != 0:
            return False, f"rc={rc}\n{out}"
        buoi = [x["buoi"] for x in s.so_tren_remote()]
        if buoi.count("sang") != 1:
            return False, f"dòng `sang` xuất hiện {buoi.count('sang')} lần: {buoi}"
        if "sukien1" not in buoi:
            return False, f"MẤT dòng của workflow kia: {buoi}"
        return True, buoi


def ca_tinh_url_dung_mot_lan():
    """CA CHÍNH 2 — PHẢI CHẶN việc tính lại URL sau khi HEAD đã nhảy sang lô người khác.

    `so_da_gui.py` chọn URL bằng `make_docx.pick_items`, tức DIFF index.html với `HEAD~1`.
    Nếu vòng retry gọi lại nó SAU `reset FETCH_HEAD` thì diff là với lô của PHIÊN KHÁC ⇒
    sổ ghi thừa URL của lô đó ⇒ bản tin sau BỎ những tin đó. Mất tin, không phải trùng
    tin — nên dù bị chen mấy vòng, `ghi_so` vẫn chỉ được gọi ĐÚNG MỘT LẦN.
    """
    with Sanh() as s:
        goi = {"n": 0}

        def ghi(buoi, chi=None):
            goi["n"] += 1
            _ghi_gia(s.B)(buoi, chi)

        rc, out = s.chay("sang", ghi_so=ghi, chen_o_vong=(1, 2))
        if rc != 0:
            return False, f"rc={rc}\n{out}"
        if goi["n"] != 1:
            return False, (f"ghi_so gọi {goi['n']} lần — tính lại URL trên ngữ cảnh git "
                           f"đã đổi, sổ sẽ ăn URL của lô phiên khác")
        return True, f"ghi_so gọi 1 lần, thắng sau khi bị chen 2 vòng"


def ca_khong_keo_index_html_cua_remote():
    """PHẢI CHẶN `reset --hard`: index.html của phiên mình không được bị remote đè.

    Nếu bị đè, `so_da_gui.py` sẽ đọc index.html của LÔ KHÁC và ghi thừa URL vào sổ ⇒
    bản tin sau BỎ những tin đó. Mất tin, không phải trùng tin.
    """
    with Sanh() as s:
        (s.B / "index.html").write_text("BAN CUA PHIEN MINH", encoding="utf-8")
        s.A_push("sukien")
        _git(s.A, "fetch", "-q", "origin", "main")
        _git(s.A, "reset", "-q", "--hard", "FETCH_HEAD")
        (s.A / "index.html").write_text("BAN MOI CUA REMOTE", encoding="utf-8")
        _git(s.A, "add", "index.html")
        _git(s.A, "commit", "-q", "-m", "tin moi cua phien khac")
        _git(s.A, "push", "-q", "origin", "HEAD:main")

        rc, out = s.chay("sang")
        if rc != 0:
            return False, f"rc={rc}\n{out}"
        con = (s.B / "index.html").read_text(encoding="utf-8")
        if con != "BAN CUA PHIEN MINH":
            return False, f"index.html bị đè thành {con!r} — dùng --hard thay vì --mixed?"
        return True, con


def ca_het_vong_phai_keu():
    """PHẢI KÊU: bị chen mọi vòng → mã ≠ 0 + có `::error::`, KHÔNG được trả 0 cho êm."""
    with Sanh() as s:
        rc, out = s.chay("sang", vong=3, chen_o_vong=(1, 2, 3))
        if rc == 0:
            return False, f"trả 0 dù chưa push được (fail-open)\n{out}"
        if "::error::" not in out:
            return False, f"không in ::error:: nên không ai lần được dấu vết\n{out}"
        return True, f"rc={rc}"


def ca_du_vong_de_thang():
    """ĐỐI CHỨNG cho ca trên: chen 2 vòng đầu, vòng 3 phải thắng (chứng minh CÓ retry)."""
    with Sanh() as s:
        rc, out = s.chay("sang", vong=5, chen_o_vong=(1, 2))
        if rc != 0:
            return False, f"rc={rc} — vòng retry bị bỏ?\n{out}"
        buoi = [x["buoi"] for x in s.so_tren_remote()]
        if buoi.count("sang") != 1 or "sukien1" not in buoi or "sukien2" not in buoi:
            return False, f"sổ cuối sai: {buoi}"
        return True, f"sổ {buoi}"


def ca_khong_race_thi_chay_thuong():
    """ĐỐI CHỨNG — chống chặn oan: không ai chen thì push ngay vòng 1."""
    with Sanh() as s:
        rc, out = s.chay("sang")
        if rc != 0:
            return False, f"rc={rc}\n{out}"
        if "vong 1/5" not in out:
            return False, f"không push ở vòng 1: {out}"
        buoi = [x["buoi"] for x in s.so_tren_remote()]
        if buoi != ["toi", "sang"]:
            return False, f"sổ cuối {buoi}, chờ ['toi','sang']"
        return True, buoi


def ca_so_khong_doi_thi_khong_commit():
    """ĐỐI CHỨNG — sổ không đổi thì exit 0 và KHÔNG tạo commit rác mỗi lần chạy."""
    with Sanh() as s:
        truoc = _git(s.B, "rev-parse", "origin/main").stdout.strip()
        rc, out = s.chay("sang", ghi_so=lambda buoi, chi=None: None)
        if rc != 0:
            return False, f"rc={rc}\n{out}"
        sau = s.so_tren_remote()
        if len(sau) != 1:
            return False, f"sổ đổi dù không ghi gì: {sau}"
        moi = _git(s.B, "ls-remote", str(s.remote), "main").stdout.split()[0]
        if moi != truoc:
            return False, "đã push commit rỗng lên remote"
        return True, "không commit"


def ca_so_chua_co_tren_remote():
    """ĐỐI CHỨNG — lần đầu tiên (remote chưa có sổ) vẫn ghi và push được."""
    with Sanh() as s:
        _git(s.A, "rm", "-q", SO_REL)
        _git(s.A, "commit", "-q", "-m", "xoa so")
        _git(s.A, "push", "-q", "origin", "HEAD:main")
        rc, out = s.chay("sang")
        if rc != 0:
            return False, f"rc={rc}\n{out}"
        buoi = [x["buoi"] for x in s.so_tren_remote()]
        if buoi != ["sang"]:
            return False, f"sổ cuối {buoi}, chờ ['sang'] (nhân dòng của working tree cũ?)"
        return True, buoi


def ca_cong_con_nam_tren_duong_di():
    """Cổng có tồn tại mà không ai gọi thì vô nghĩa — soi CHÍNH hai file workflow."""
    thieu = []
    for ten in ("notify-email.yml", "notify-morning.yml"):
        p = REPO / ".github" / "workflows" / ten
        t = p.read_text(encoding="utf-8")
        if "ghi_so_push.py" not in t:
            thieu.append(f"{ten}: không gọi ghi_so_push.py")
        if "pull --rebase origin main && git push" in t:
            thieu.append(f"{ten}: CÒN khối rebase cũ — chính chỗ gây sự cố 30/07")
    return (not thieu), "\n".join(thieu) or "cả hai workflow đã đi qua cổng"


CA = [
    ("CA CHÍNH · workflow kia push trước 7 giây → sổ PHẢI có đủ hai dòng",
     ca_race_giu_du_hai_dong),
    ("PHẢI CHẶN · bị chen rồi ghi lại → KHÔNG nhân đôi dòng của mình",
     ca_khong_nhan_doi_dong),
    ("CA CHÍNH 2 · URL tính ĐÚNG MỘT LẦN, retry không tính lại theo HEAD đã nhảy",
     ca_tinh_url_dung_mot_lan),
    ("PHẢI CHẶN · index.html của phiên mình KHÔNG bị bản remote đè (--mixed, không --hard)",
     ca_khong_keo_index_html_cua_remote),
    ("PHẢI KÊU · hết vòng vẫn chưa push được → mã ≠ 0 + ::error::",
     ca_het_vong_phai_keu),
    ("ĐỐI CHỨNG · chen 2 vòng đầu thì vòng 3 phải thắng (có retry thật)",
     ca_du_vong_de_thang),
    ("ĐỐI CHỨNG · không ai chen thì push ngay vòng 1", ca_khong_race_thi_chay_thuong),
    ("ĐỐI CHỨNG · sổ không đổi → exit 0, không commit rác",
     ca_so_khong_doi_thi_khong_commit),
    ("ĐỐI CHỨNG · remote chưa có sổ → vẫn ghi được, không nhân dòng",
     ca_so_chua_co_tren_remote),
    ("Cổng còn nằm trên đường đi (soi 2 file workflow)", ca_cong_con_nam_tren_duong_di),
]


# ──────────────────────────────── tự kiểm ────────────────────────────────
# Mỗi bản hỏng GỠ ĐÚNG MỘT lớp bảo vệ. Luật 29/07: bảo vệ hay đắp nhiều lớp chồng nhau,
# gỡ một lớp mà lớp kia gánh thì ca vẫn XANH và mình tưởng ca đó vô dụng.
BAN_HONG = [
    ("dùng lại `git pull --rebase` như bản cũ (chính sự cố 30/07)",
     [('_git("fetch", "-q", "origin", "main", kiem=True)\n'
       '        _git("reset", "-q", "--mixed", "FETCH_HEAD", kiem=True)',
       '_git("stash", "-q")\n        _git("stash", "-q", "pop", kiem=False)'),
      ('if _git("checkout", "-q", "FETCH_HEAD", "--", SO_REL).returncode != 0:',
       'if False:'),
      ('if _git("push", "-q", "origin", "HEAD:main").returncode == 0:',
       'if _git("pull", "--rebase", "-q", "origin", "main").returncode == 0 '
       'and _git("push", "-q", "origin", "HEAD:main").returncode == 0:')],
     ["CA CHÍNH · workflow kia push trước 7 giây → sổ PHẢI có đủ hai dòng"]),

    ("bỏ bước lấy sổ mới nhất của remote (mất dòng workflow kia)",
     [('if _git("checkout", "-q", "FETCH_HEAD", "--", SO_REL).returncode != 0:\n'
       '            # sổ chưa từng có trên remote: bỏ bản trong working tree để khỏi nhân dòng\n'
       '            (ROOT / SO_REL).unlink(missing_ok=True)',
       'pass')],
     ["CA CHÍNH · workflow kia push trước 7 giây → sổ PHẢI có đủ hai dòng",
      "PHẢI CHẶN · bị chen rồi ghi lại → KHÔNG nhân đôi dòng của mình",
      "ĐỐI CHỨNG · chen 2 vòng đầu thì vòng 3 phải thắng (có retry thật)",
      "ĐỐI CHỨNG · remote chưa có sổ → vẫn ghi được, không nhân dòng"]),

    ("dùng `reset --hard` (kéo cả index.html của lô khác về)",
     [('_git("reset", "-q", "--mixed", "FETCH_HEAD", kiem=True)',
       '_git("reset", "-q", "--hard", "FETCH_HEAD", kiem=True)')],
     ["PHẢI CHẶN · index.html của phiên mình KHÔNG bị bản remote đè "
      "(--mixed, không --hard)"]),

    ("hết vòng vẫn trả 0 cho êm (fail-open)",
     [('    print(f"::error::khong push duoc so da gui sau {vong} vong. So TRONG se lam canary "\n'
       '          f"keu oan va lam phien du phong quet lai — xem tests/test-ghi-so-push.py")\n'
       '    return 1',
       '    return 0')],
     ["PHẢI KÊU · hết vòng vẫn chưa push được → mã ≠ 0 + ::error::"]),

    ("bỏ vòng retry, chỉ thử một lần",
     [("for i in range(1, vong + 1):", "for i in range(1, 2):")],
     ["ĐỐI CHỨNG · chen 2 vòng đầu thì vòng 3 phải thắng (có retry thật)"]),

    ("tính lại URL ở MỖI vòng (gọi so_da_gui.py sau khi HEAD đã nhảy)",
     [("        _append_dong(dong)", "        ghi_so(buoi, chi)")],
     ["CA CHÍNH 2 · URL tính ĐÚNG MỘT LẦN, retry không tính lại theo HEAD đã nhảy"]),
]


def _chay_bo_ca():
    do = []
    for ten, f in CA:
        try:
            ok, _ = f()
        except Exception:                                        # noqa: BLE001
            ok = False
        if not ok:
            do.append(ten)
    return do


def tu_kiem() -> int:
    print("TỰ KIỂM — dựng bản ghi_so_push.py HỎNG rồi đòi các ca đã khai phải ĐỎ")
    print("─" * 78)
    goc = MOD_THAT.read_text(encoding="utf-8")
    hong_tong = 0
    for mo_ta, phep_thay, can_do in BAN_HONG:
        moi = goc
        loi_thay = []
        for tim, thay in phep_thay:
            if moi.count(tim) != 1:
                loi_thay.append(f"KHÔNG áp được phép thay: {moi.count(tim)} chỗ khớp "
                                f"— neo lại chuỗi ({tim.splitlines()[0][:60]}…)")
            moi = moi.replace(tim, thay, 1)
        # ⚠ Bản hỏng phải nằm trong ĐÚNG thư mục thật (mục 17 CLAUDE.md)
        tam = MOD_THAT.with_name(f"_hong-{os.getpid()}-ghi-so-push.py")
        try:
            tam.write_text(moi, encoding="utf-8")
            os.environ["GHISO_MOD"] = str(tam)
            globals()["MOD_PATH"] = tam
            do = _chay_bo_ca()
        finally:
            tam.unlink(missing_ok=True)
            os.environ.pop("GHISO_MOD", None)
            globals()["MOD_PATH"] = MOD_THAT

        loi = list(loi_thay)
        # Luật 30/07: đỏ SẠCH mọi ca = phép thay hỏng cú pháp, không chứng minh được gì
        if len(do) == len(CA):
            loi.append("ĐỎ TOÀN BỘ ca — phép thay có thể hỏng cú pháp, sửa lại phép thay")
        for c in can_do:
            if c not in do:
                loi.append(f"ca PHẢI ĐỎ mà vẫn xanh: {c}")
        print(f"  {'✓' if not loi else '✗'} bản hỏng: {mo_ta}")
        print(f"        │ {len(do)}/{len(CA)} ca đỏ")
        for d in loi:
            print(f"        │ {d}")
        if loi:
            hong_tong += 1
    print("─" * 78)
    if hong_tong:
        print(f"✗ {hong_tong}/{len(BAN_HONG)} bản hỏng KHÔNG bị bắt — test chưa có răng.")
        return 1
    print(f"✓ {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt — test có răng thật.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print("TEST GHI SỔ ĐÃ GỬI — hai workflow ghi cùng file thì không được mất dòng nào")
    print(f"(bản đang thử: {MOD_PATH})")
    print("─" * 78)
    if shutil.which("git") is None:
        print("✗ không có git trên máy — bộ test này cần git thật")
        return 1
    hong = 0
    for ten, f in CA:
        try:
            ok, out = f()
        except Exception as e:                                   # noqa: BLE001
            ok, out = False, f"LỖI CHẠY: {e.__class__.__name__}: {e}"
        print(f"  {'✓' if ok else '✗'} {ten}")
        if not ok:
            hong += 1
            for dong in str(out or "(không có đầu ra)").strip().split("\n")[:8]:
                print(f"        │ {dong}")
    print("─" * 78)
    if hong:
        print(f"✗ {hong}/{len(CA)} ca HỎNG — sổ đã gửi có thể mất dòng khi hai workflow "
              f"ghi cùng lúc, và canary sẽ kêu oan.")
        return 1
    print(f"✓ {len(CA)}/{len(CA)} ca đạt — sổ giữ đủ dòng của cả hai workflow.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

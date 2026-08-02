#!/usr/bin/env python3
"""CỔNG: log ngày phải hợp nhất kiểu APPEND-ONLY, tuyệt đối KHÔNG `pull --rebase`.

VÌ SAO CÓ FILE NÀY — sự cố thật sáng 02/08/2026:
04 phiên cùng ghi `logs/scan-2026-08-02.log` (CI 03:47 · local 04:30 · lớp vét 04:47 · một
phiên gọi lại). Mỗi phiên append một dòng vào cuối rồi `git pull --rebase` khi push bị từ
chối ⇒ xung đột văn bản ⇒ rebase hỏng ⇒ repo nằm lại ở trạng thái rebase dở. Phiên local
05:30 vào thì chết ngay lệnh đầu tiên: *"Pulling is not possible because you have unmerged
files"*. Repo kẹt như thế thì MỌI phiên sau đều chết ở Bước 1, kể cả phiên tối có hạn chót
gửi 22:00 — và không có tiếng kêu nào ngoài một dòng `fatal`.

Bộ test dựng repo git THẬT (remote bare + 2 clone = 2 phiên) rồi đo hành vi thật.

Chạy:  python3 tests/test-ghi-log-push.py
        python3 tests/test-ghi-log-push.py --tu-kiem
"""
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT_THAT = ROOT / "scripts" / "ghi_log_push.py"
LOG_REL = "logs/scan-2026-08-02.log"


def _git(d, *a, kiem=True):
    r = subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True)
    if kiem and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)}: {(r.stderr or r.stdout)[:300]}")
    return r


def _dung_san(t, ma_script=None):
    """remote bare + 2 clone. Mỗi clone mang NGUYÊN CÂY scripts/ + .github/scripts/."""
    t = pathlib.Path(t)
    bare = t / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)

    goc = t / "goc"
    goc.mkdir()
    _git(goc, "init", "-q")
    _git(goc, "config", "user.email", "t@t")
    _git(goc, "config", "user.name", "t")
    (goc / "logs").mkdir()
    (goc / LOG_REL).write_text("[00:00Z] START\n", encoding="utf-8")
    (goc / "index.html").write_text("GOC", encoding="utf-8")
    _git(goc, "add", "-A")
    _git(goc, "commit", "-q", "-m", "nen")
    _git(goc, "remote", "add", "origin", str(bare))
    _git(goc, "push", "-q", "origin", "HEAD:main")

    clones = []
    for ten in ("A", "B"):
        d = t / ten
        subprocess.run(["git", "clone", "-q", str(bare), str(d)], check=True)
        _git(d, "config", "user.email", f"{ten}@t")
        _git(d, "config", "user.name", ten)
        (d / "scripts").mkdir(parents=True, exist_ok=True)
        (d / ".github" / "scripts").mkdir(parents=True, exist_ok=True)
        noi = ma_script if ma_script is not None else SCRIPT_THAT.read_text(encoding="utf-8")
        (d / "scripts" / "ghi_log_push.py").write_text(noi, encoding="utf-8")
        shutil.copy2(ROOT / ".github" / "scripts" / "ghi_so_push.py",
                     d / ".github" / "scripts" / "ghi_so_push.py")
        clones.append(d)
    return bare, clones[0], clones[1]


def _them_dong(d, dong):
    p = pathlib.Path(d) / LOG_REL
    p.write_text(p.read_text(encoding="utf-8") + dong + "\n", encoding="utf-8")


def _chay(d, nhan="log: thu"):
    r = subprocess.run([sys.executable, str(pathlib.Path(d) / "scripts" / "ghi_log_push.py"),
                        "--file", LOG_REL, "--nhan", nhan],
                       cwd=str(d), capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _log_tren_remote(bare):
    return subprocess.run(["git", "-C", str(bare), "show", f"main:{LOG_REL}"],
                          capture_output=True, text=True).stdout


# ─────────────────────────── các ca ───────────────────────────
def ca_01_giu_du_hai_dong(ma=None):
    """CA CHÍNH · hồi quy 02/08: phiên A push trước, phiên B ghi sau → log PHẢI có CẢ HAI."""
    with tempfile.TemporaryDirectory() as t:
        bare, A, B = _dung_san(t, ma)
        _them_dong(B, "[21:41Z] SKIP local 04:30")      # B viết trước, push sau
        _them_dong(A, "[21:38Z] SKIP lop vet 04:47")
        rc, _ = _chay(A, "log: A")
        if rc != 0:
            return False, "phiên A push hỏng"
        rc, out = _chay(B, "log: B")
        if rc != 0:
            return False, f"phiên B push hỏng (rc={rc})\n{out}"
        noi = _log_tren_remote(bare)
        if "SKIP lop vet 04:47" not in noi:
            return False, f"MẤT dòng của phiên A\n{noi}"
        if "SKIP local 04:30" not in noi:
            return False, f"MẤT dòng của phiên B\n{noi}"
    return True, "giữ đủ dòng của cả hai phiên"


def ca_02_khong_nhan_doi(ma=None):
    """PHẢI CHẶN · chạy lại lần hai KHÔNG được nhân đôi dòng (idempotent)."""
    with tempfile.TemporaryDirectory() as t:
        bare, A, B = _dung_san(t, ma)
        _them_dong(A, "[21:38Z] dong cua A")
        _chay(A, "log: A")
        _chay(A, "log: A lan hai")
        noi = _log_tren_remote(bare)
        if noi.count("dong cua A") != 1:
            return False, f"dòng bị nhân {noi.count('dong cua A')} lần\n{noi}"
    return True, "chạy lại không nhân đôi"


def ca_03_khong_bao_gio_ket_rebase(ma=None):
    """PHẢI CHẶN · sau khi bị chen, repo TUYỆT ĐỐI không được nằm lại ở trạng thái rebase dở.

    Đây là thiệt hại thật của sự cố: repo kẹt thì mọi phiên sau chết ở Bước 1.
    """
    with tempfile.TemporaryDirectory() as t:
        bare, A, B = _dung_san(t, ma)
        _them_dong(B, "[21:41Z] dong cua B")
        _them_dong(A, "[21:38Z] dong cua A")
        _chay(A, "log: A")
        _chay(B, "log: B")
        for d in (A, B):
            for dau in (".git/rebase-merge", ".git/rebase-apply", ".git/MERGE_HEAD"):
                if (pathlib.Path(d) / dau).exists():
                    return False, f"{pathlib.Path(d).name} còn kẹt ở {dau}"
            r = _git(d, "status", "--porcelain", kiem=False)
            if "UU " in r.stdout:
                return False, f"{pathlib.Path(d).name} còn file unmerged:\n{r.stdout}"
    return True, "không phiên nào kẹt rebase"


def ca_04_pha0_doc_truoc_khi_dung_git(ma=None):
    """PHẢI CHẶN · dòng của phiên mình phải được chụp TRƯỚC `checkout FETCH_HEAD`.

    Đọc sau bước đó là đọc log của phiên KHÁC (bản remote vừa ghi đè lên), phần của mình
    mất sạch mà không lỗi nào — đúng kiểu hỏng câm.
    """
    with tempfile.TemporaryDirectory() as t:
        bare, A, B = _dung_san(t, ma)
        _them_dong(A, "[21:38Z] A rieng")
        _chay(A, "log: A")
        _them_dong(B, "[21:41Z] B rieng")
        _chay(B, "log: B")
        noi = _log_tren_remote(bare)
        if "B rieng" not in noi:
            return False, f"dòng của B biến mất — PHA 0 đọc sau khi đã checkout\n{noi}"
    return True, "PHA 0 chụp trước khi đụng git"


def ca_05_khong_ai_chen(ma=None):
    """ĐỐI CHỨNG · không ai chen thì push ngay, không kêu gì."""
    with tempfile.TemporaryDirectory() as t:
        bare, A, _ = _dung_san(t, ma)
        _them_dong(A, "[21:38Z] mot minh")
        rc, out = _chay(A)
        if rc != 0:
            return False, f"rc={rc}\n{out}"
        if "::error::" in out:
            return False, f"kêu oan\n{out}"
        if "mot minh" not in _log_tren_remote(bare):
            return False, "không push được dòng"
    return True, "đường thường chạy trơn"


def ca_06_thieu_file_phai_keu(ma=None):
    """PHẢI KÊU · gọi script khi chưa có file log → mã ≠ 0 + `::error::`, không im."""
    with tempfile.TemporaryDirectory() as t:
        _, A, _ = _dung_san(t, ma)
        (pathlib.Path(A) / LOG_REL).unlink()
        rc, out = _chay(A)
        if rc == 0:
            return False, f"trả 0 cho êm\n{out}"
        if "::error::" not in out:
            return False, f"không in ::error::\n{out}"
    return True, "thiếu file thì kêu"


def ca_07_khong_de_index_html(ma=None):
    """ĐỐI CHỨNG · `--mixed` chứ không `--hard`: index.html đang sửa dở KHÔNG bị đè."""
    with tempfile.TemporaryDirectory() as t:
        bare, A, B = _dung_san(t, ma)
        _them_dong(B, "[21:41Z] cua B")
        _chay(B, "log: B")
        _them_dong(A, "[21:38Z] cua A")
        (pathlib.Path(A) / "index.html").write_text("LO TIN CUA PHIEN A", encoding="utf-8")
        _chay(A, "log: A")
        con = (pathlib.Path(A) / "index.html").read_text(encoding="utf-8")
        if con != "LO TIN CUA PHIEN A":
            return False, f"index.html bị đè: {con!r}"
    return True, "index.html của phiên mình còn nguyên"


CAC_CA = [
    ("[01] CA CHÍNH · hai phiên ghi cùng log → giữ đủ cả hai dòng", ca_01_giu_du_hai_dong),
    ("[02] PHẢI CHẶN · chạy lại không nhân đôi dòng", ca_02_khong_nhan_doi),
    ("[03] PHẢI CHẶN · không phiên nào kẹt rebase", ca_03_khong_bao_gio_ket_rebase),
    ("[04] PHẢI CHẶN · PHA 0 chụp dòng trước khi đụng git", ca_04_pha0_doc_truoc_khi_dung_git),
    ("[05] ĐỐI CHỨNG · không ai chen thì chạy trơn", ca_05_khong_ai_chen),
    ("[06] PHẢI KÊU · thiếu file log → mã ≠ 0 + ::error::", ca_06_thieu_file_phai_keu),
    ("[07] ĐỐI CHỨNG · index.html không bị đè", ca_07_khong_de_index_html),
]


def chay(ma=None, im=False):
    do = []
    for ten, f in CAC_CA:
        try:
            ok, ghi_chu = f(ma)
        except Exception as e:                                  # noqa: BLE001
            ok, ghi_chu = False, f"NGOẠI LỆ: {type(e).__name__}: {e}"
        if not im:
            print(f"  {'✓' if ok else '✗'} {ten}" + (f" — {ghi_chu}" if not ok else ""))
        if not ok:
            do.append(ten)
    return do


BAN_HONG = [
    ("PHA 0 đọc dòng của mình SAU khi đã checkout bản remote",
     "    dong_cua_minh = p.read_text(encoding=\"utf-8\").splitlines()",
     "    dong_cua_minh = []",
     ["[01] CA CHÍNH · hai phiên ghi cùng log → giữ đủ cả hai dòng",
      "[04] PHẢI CHẶN · PHA 0 chụp dòng trước khi đụng git"]),

    ("ghép mà KHÔNG lọc dòng đã có (nhân đôi mỗi vòng)",
     "        them = [d for d in dong_cua_minh if d.strip() and d not in da_co]",
     "        them = [d for d in dong_cua_minh if d.strip()]",
     ["[02] PHẢI CHẶN · chạy lại không nhân đôi dòng"]),

    ("thiếu file log thì trả 0 cho êm",
     '        print(f"::error::khong co file {rel} — phien phai ghi log TRUOC khi goi script nay")\n'
     "        return 2",
     "        return 0",
     ["[06] PHẢI KÊU · thiếu file log → mã ≠ 0 + ::error::"]),
]


def tu_kiem():
    goc = SCRIPT_THAT.read_text(encoding="utf-8")
    print("Bản ĐÚNG:")
    do = chay()
    if do:
        print(f"\n✗ bản đúng đã có {len(do)} ca không đạt — sửa trước khi tự kiểm")
        return 1

    print("\nBản HỎNG (mỗi bản gỡ đúng một lớp vá):")
    hong = 0
    for ten, tim, thay, phai_do in BAN_HONG:
        if goc.count(tim) != 1:
            print(f"  ✗ {ten} — chuỗi neo khớp {goc.count(tim)} chỗ (phải đúng 1)")
            hong += 1
            continue
        ma = goc.replace(tim, thay)
        sha = hashlib.sha1(ma.encode("utf-8")).hexdigest()[:8]
        do = chay(ma, im=True)
        if len(do) == len(CAC_CA):
            print(f"  ✗ {ten} [{sha}] — MỌI ca đều đỏ: phép thay phá hỏng nền")
            hong += 1
            continue
        thieu = [c for c in phai_do if c not in do]
        if thieu:
            print(f"  ✗ {ten} [{sha}] — VẪN XANH: {thieu}\n      (đỏ thực tế: {do})")
            hong += 1
        else:
            print(f"  ✓ {ten} [{sha}] — bắt được ({len(do)} ca đỏ)")
    if hong:
        print(f"\n✗ TỰ KIỂM TRƯỢT: {hong}/{len(BAN_HONG)} bản hỏng không bị bắt")
        return 1
    print(f"\n✅ TỰ KIỂM ĐẠT: {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt")
    return 0


def main(argv):
    if "--tu-kiem" in argv:
        return tu_kiem()
    print(f"Bộ test ghi log push — {len(CAC_CA)} ca")
    do = chay()
    if do:
        print(f"\n✗ {len(do)}/{len(CAC_CA)} ca KHÔNG ĐẠT")
        return 1
    print(f"\n✅ {len(CAC_CA)}/{len(CAC_CA)} ca đạt")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""CỔNG: email/Telegram SÁNG phải so với bản TRƯỚC COMMIT NỘI DUNG, không phải HEAD~1.

VÌ SAO CÓ FILE NÀY — sự cố thật sáng 02/08/2026:
phiên quét sáng sớm nạp 04 bài think-tank + báo cáo tuần Chủ Nhật, commit
`bcf767b Cap nhat su kien 02/08: +4 bai think-tank, bao cao tuan`, RỒI push tiếp commit
log `6fa8cd9 log: hoan tat phien sang som 02/08`, SAU ĐÓ mới `gh workflow run notify-morning`.
Bước "Lấy bản trước" khi đó dùng `git show HEAD~1:...` — mà HEAD~1 chính là commit LOG, tức
bản ĐÃ CÓ SẴN lô vừa nạp. Đo thật: kho ở HEAD~1 có **489** bài, bản đúng phải dùng có **485**.
So hai bản giống nhau ⇒ diff rỗng ⇒ `send-morning-email.js` in
*"Không có sự kiện/tập trận mới, không có báo cáo tuần mới, không có bài think-tank mới —
bỏ qua gửi."* ⇒ **mất 04 bài + báo cáo tuần**. Run `success`, không cảnh báo nào.

Đây là hỏng CÂM đúng nghĩa: mọi thứ xanh, chỉ là bản tin không tới tay.

CÁCH VÁ: neo vào chính commit nội dung —
`git log -1 -E -i --grep='^(Cap nhat su kien|Dang bao cao tuan)' --format=%H` rồi lấy `~1`.
Bao nhiêu commit log chen vào cũng không làm sai được nữa.

Bộ test ĐỌC CHÍNH `.github/workflows/notify-morning.yml`, trích đoạn `run:` của bước đó rồi
chạy thật trong một repo git dựng riêng — nên nó canh được cả việc phiên sau lỡ tay đổi lại
về `HEAD~1` (cổng phải còn nằm trên đường đi, không chỉ đúng trên giấy).

Chạy:  python3 tests/test-base-so-sanh-morning.py
        python3 tests/test-base-so-sanh-morning.py --tu-kiem
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
YML = ROOT / ".github" / "workflows" / "notify-morning.yml"
TEN_BUOC = "Lấy bản TRƯỚC COMMIT NỘI DUNG"


# ─────────────────────────── đọc đoạn script từ chính yml ───────────────────────────
def doc_doan_run(yml_text=None):
    """Trích thân `run:` của bước lấy bản-để-so. Trả chuỗi shell, hoặc '' nếu không thấy."""
    text = yml_text if yml_text is not None else YML.read_text(encoding="utf-8")
    # neo vào tên bước rồi lấy khối `run: |` ngay sau đó
    i = text.find(TEN_BUOC)
    if i < 0:
        # bản cũ (trước 02/08) mang tên khác — vẫn trích để ca hồi quy chạy được
        i = text.find("Lấy bản index.html của commit trước")
        if i < 0:
            return ""
    j = text.find("run: |", i)
    if j < 0:
        return ""
    dong = text[j:].splitlines()[1:]
    than, thut = [], None
    for d in dong:
        if not d.strip():
            than.append("")
            continue
        cur = len(d) - len(d.lstrip())
        if thut is None:
            thut = cur
        if cur < thut:
            break
        than.append(d[thut:])
    return "\n".join(than).rstrip()


# ─────────────────────────── dựng repo giả ───────────────────────────
def _git(d, *a, kiem=True):
    r = subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True)
    if kiem and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)}: {(r.stderr or r.stdout)[:300]}")
    return r


def _kho(n):
    return json.dumps([{"url": f"https://x/{k}", "title": f"bai {k}"} for k in range(n)])


def dung_repo(d, msg_noi_dung="Cap nhat su kien 02/08: +4 bai think-tank, bao cao tuan",
              them_commit_log=True, so_bai_truoc=485, so_bai_sau=489):
    """Dựng đúng hình dạng lịch sử của sự cố: nền → commit NỘI DUNG → (commit LOG)."""
    d = pathlib.Path(d)
    (d / "data").mkdir(parents=True, exist_ok=True)
    (d / "logs").mkdir(parents=True, exist_ok=True)
    _git(d, "init", "-q")
    _git(d, "config", "user.email", "t@t")
    _git(d, "config", "user.name", "t")

    (d / "index.html").write_text("var DATA = {\"exercises\":[]}", encoding="utf-8")
    (d / "data" / "analyses.json").write_text(_kho(so_bai_truoc), encoding="utf-8")
    _git(d, "add", "-A")
    _git(d, "commit", "-q", "-m", "nen: ban truoc phien sang")

    (d / "index.html").write_text("var DATA = {\"exercises\":[1]}", encoding="utf-8")
    (d / "data" / "analyses.json").write_text(_kho(so_bai_sau), encoding="utf-8")
    _git(d, "add", "-A")
    _git(d, "commit", "-q", "-m", msg_noi_dung)

    if them_commit_log:
        (d / "logs" / "scan.log").write_text("DONE\n", encoding="utf-8")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", "log: hoan tat phien sang som 02/08")
    return d


def chay_buoc(d, doan):
    """Chạy đoạn shell của bước trong repo `d`; trả (stdout+stderr, dict biến GITHUB_ENV)."""
    d = pathlib.Path(d)
    env_file = d / "_github_env"
    env_file.write_text("", encoding="utf-8")
    moi = dict(os.environ)
    moi["GITHUB_ENV"] = str(env_file)
    r = subprocess.run(["bash", "-c", doan], cwd=str(d), env=moi,
                       capture_output=True, text=True)
    bien = {}
    for dong in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in dong:
            k, v = dong.split("=", 1)
            bien[k] = v
    return (r.stdout or "") + (r.stderr or ""), bien


def _so_bai(p):
    try:
        return len(json.loads(pathlib.Path(p).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return -1


# ─────────────────────────── các ca ───────────────────────────
def ca_01_hoi_quy_commit_log_chen(doan):
    """PHẢI ĐÚNG · hồi quy sự cố 02/08: có commit LOG chen vào thì base VẪN phải là bản 485 bài."""
    with tempfile.TemporaryDirectory() as t:
        dung_repo(t, them_commit_log=True)
        out, bien = chay_buoc(t, doan)
        p = bien.get("PREV_ANALYSES")
        if not p:
            return False, f"không khai PREV_ANALYSES\n{out}"
        n = _so_bai(p)
        if n != 485:
            return False, (f"base trỏ SAI: kho để so có {n} bài, phải là 485 "
                           f"(489 = đã gồm lô vừa nạp ⇒ diff rỗng ⇒ bỏ qua gửi)\n{out}")
    return True, "base = trước commit nội dung (485 bài)"


def ca_02_khong_co_commit_log(doan):
    """Đối chứng: notify chạy NGAY sau commit nội dung → vẫn phải đúng 485."""
    with tempfile.TemporaryDirectory() as t:
        dung_repo(t, them_commit_log=False)
        _, bien = chay_buoc(t, doan)
        n = _so_bai(bien.get("PREV_ANALYSES", ""))
        if n != 485:
            return False, f"kho để so có {n} bài, phải 485"
    return True, "không có commit log chen → vẫn đúng"


def ca_03_bao_cao_tuan(doan):
    """Đối chứng: tiền tố `Dang bao cao tuan` cũng phải được nhận là commit nội dung."""
    with tempfile.TemporaryDirectory() as t:
        dung_repo(t, msg_noi_dung="Dang bao cao tuan 02/08", them_commit_log=True)
        _, bien = chay_buoc(t, doan)
        n = _so_bai(bien.get("PREV_ANALYSES", ""))
        if n != 485:
            return False, f"kho để so có {n} bài, phải 485"
    return True, "nhận cả tiền tố báo cáo tuần"


def ca_04_prev_html_cung_base(doan):
    """PHẢI ĐÚNG: PREV_HTML cũng phải lấy theo base, không được kẹt lại ở HEAD~1."""
    with tempfile.TemporaryDirectory() as t:
        dung_repo(t, them_commit_log=True)
        out, bien = chay_buoc(t, doan)
        p = bien.get("PREV_HTML")
        if not p:
            return False, f"không khai PREV_HTML\n{out}"
        noi = pathlib.Path(p).read_text(encoding="utf-8")
        if "\"exercises\":[]" not in noi:
            return False, ("PREV_HTML lấy nhầm bản ĐÃ có sự kiện mới ⇒ diffEvents rỗng "
                           f"⇒ mất tin sự kiện/tập trận\nnội dung: {noi[:120]}")
    return True, "PREV_HTML theo đúng base"


def ca_05_khong_co_commit_noi_dung_phai_keu(doan):
    """PHẢI KÊU: lịch sử không có commit nội dung nào → lùi HEAD~1 nhưng phải in ::warning::."""
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t)
        (d / "data").mkdir(parents=True)
        _git(d, "init", "-q")
        _git(d, "config", "user.email", "t@t")
        _git(d, "config", "user.name", "t")
        (d / "index.html").write_text("a", encoding="utf-8")
        (d / "data" / "analyses.json").write_text(_kho(3), encoding="utf-8")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", "nen")
        (d / "index.html").write_text("b", encoding="utf-8")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", "log: gi do")
        out, _ = chay_buoc(d, doan)
        if "::warning::" not in out:
            return False, (f"không in ::warning:: — im lặng lùi về HEAD~1 là dựng lại đúng "
                           f"vùng câm vừa bịt\n{out}")
    return True, "không thấy commit nội dung → kêu rồi mới lùi"


def ca_06_yml_khong_con_head1_cho_analyses(doan):
    """Cổng còn nằm trên đường đi: yml KHÔNG được quay lại `git show HEAD~1:data/analyses.json`."""
    if re.search(r'git show\s+HEAD~1:data/analyses\.json', doan):
        return False, "yml vẫn dùng HEAD~1 cho data/analyses.json — bản vá đã bị gỡ"
    if "--grep" not in doan:
        return False, "yml không còn neo vào commit nội dung bằng --grep"
    return True, "yml neo vào commit nội dung"


CAC_CA = [
    ("[01] PHẢI ĐÚNG · hồi quy 02/08: commit log chen vào, base vẫn phải là bản trước commit nội dung",
     ca_01_hoi_quy_commit_log_chen),
    ("[02] đối chứng · không có commit log chen", ca_02_khong_co_commit_log),
    ("[03] đối chứng · tiền tố 'Dang bao cao tuan'", ca_03_bao_cao_tuan),
    ("[04] PHẢI ĐÚNG · PREV_HTML cũng theo base", ca_04_prev_html_cung_base),
    ("[05] PHẢI KÊU · không có commit nội dung → ::warning::", ca_05_khong_co_commit_noi_dung_phai_keu),
    ("[06] cổng còn trên đường đi · yml không quay lại HEAD~1", ca_06_yml_khong_con_head1_cho_analyses),
]


def chay(doan, im=False):
    do = []
    for ten, f in CAC_CA:
        try:
            ok, ghi_chu = f(doan)
        except Exception as e:                                  # noqa: BLE001
            ok, ghi_chu = False, f"NGOẠI LỆ: {type(e).__name__}: {e}"
        if not im:
            print(f"  {'✓' if ok else '✗'} {ten}" + (f" — {ghi_chu}" if not ok else ""))
        if not ok:
            do.append(ten)
    return do


# ─────────────────────────── tự kiểm ───────────────────────────
# Mỗi bản hỏng gỡ ĐÚNG một lớp vá; ca khai bên phải PHẢI đỏ.
BAN_HONG = [
    ("quay lại HEAD~1 cho cả hai file",
     'base=$(git log -1 -E -i --grep=\'^(Cap nhat su kien|Dang bao cao tuan)\' --format=%H)',
     'base=""',
     ["[01] PHẢI ĐÚNG · hồi quy 02/08: commit log chen vào, base vẫn phải là bản trước commit nội dung",
      "[04] PHẢI ĐÚNG · PREV_HTML cũng theo base"]),
    ("không tìm thấy commit nội dung thì im lặng lùi HEAD~1",
     'echo "::warning::khong tim thay commit',
     'echo "::notice::khong tim thay commit',
     ["[05] PHẢI KÊU · không có commit nội dung → ::warning::"]),
    ("PREV_HTML kẹt lại ở HEAD~1",
     'git show "$base:index.html"',
     'git show "HEAD~1:index.html"',
     ["[04] PHẢI ĐÚNG · PREV_HTML cũng theo base"]),
]


def tu_kiem():
    goc = doc_doan_run()
    if not goc:
        print("✗ không trích được đoạn run từ yml — sửa `doc_doan_run`")
        return 1
    print("Bản ĐÚNG:")
    do = chay(goc)
    if do:
        print(f"\n✗ bản đúng đã có {len(do)} ca không đạt — sửa trước khi tự kiểm")
        return 1

    print("\nBản HỎNG (mỗi bản gỡ đúng một lớp vá):")
    tong_hong = 0
    for ten, tim, thay, phai_do in BAN_HONG:
        if goc.count(tim) != 1:
            print(f"  ✗ {ten} — chuỗi neo khớp {goc.count(tim)} chỗ (phải đúng 1)")
            tong_hong += 1
            continue
        hong = goc.replace(tim, thay)
        sha = hashlib.sha1(hong.encode("utf-8")).hexdigest()[:8]
        do = chay(hong, im=True)
        if len(do) == len(CAC_CA):
            print(f"  ✗ {ten} [{sha}] — MỌI ca đều đỏ: phép thay phá hỏng nền, "
                  f"không chứng minh được ca nào có răng")
            tong_hong += 1
            continue
        thieu = [c for c in phai_do if c not in do]
        if thieu:
            print(f"  ✗ {ten} [{sha}] — các ca sau VẪN XANH: {thieu}\n"
                  f"      (đỏ thực tế: {do})")
            tong_hong += 1
        else:
            print(f"  ✓ {ten} [{sha}] — bắt được ({len(do)} ca đỏ)")
    if tong_hong:
        print(f"\n✗ TỰ KIỂM TRƯỢT: {tong_hong}/{len(BAN_HONG)} bản hỏng không bị bắt")
        return 1
    print(f"\n✅ TỰ KIỂM ĐẠT: {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt")
    return 0


def main(argv):
    if "--tu-kiem" in argv:
        return tu_kiem()
    doan = doc_doan_run()
    if not doan:
        print("✗ không trích được đoạn run từ notify-morning.yml")
        return 2
    print(f"Bộ test base so sánh email sáng — {len(CAC_CA)} ca")
    do = chay(doan)
    if do:
        print(f"\n✗ {len(do)}/{len(CAC_CA)} ca KHÔNG ĐẠT")
        return 1
    print(f"\n✅ {len(CAC_CA)}/{len(CAC_CA)} ca đạt")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bộ test cho `.github/scripts/do_token_phien.py` — đo mức tiêu thụ của phiên quét trên CI.

Hai chiều hỏng của bước đo này KHÁC hẳn nhau, và bộ ca phải canh cả hai:

  (a) NÓI DỐI BẰNG SỐ 0 — không tìm thấy bản ghi phiên mà vẫn in "0 token". Đây là chiều
      nguy hiểm nhất: con số 0 trông y hệt một phép đo thành công, và nó sẽ được cộng vào
      ngân sách routine đêm như thể phiên quét sáng không tiêu gì.

  (b) LỘ NỘI DUNG — repo này CÔNG KHAI. Bản ghi phiên chứa nguyên văn tin tức, đường dẫn,
      và mọi thứ mô hình đọc được trong lúc quét. Bước đo chỉ được in CON SỐ.

Ca [10] đọc chính file workflow: cổng đúng mà workflow không gọi tới thì vô nghĩa.

    python3 tests/test-do-token-phien.py            # chạy bộ ca
    python3 tests/test-do-token-phien.py --tu-kiem  # chứng minh bộ ca BẮT ĐƯỢC lỗi
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
THAT = REPO / ".github" / "scripts" / "do_token_phien.py"
YML_THAT = REPO / ".github" / "workflows" / "claude-web-scan.yml"

# Seam cho --tu-kiem: trỏ sang bản ĐÃ GỠ dòng bảo vệ.
SCRIPT = Path(os.environ.get("DOTOKEN_SCRIPT_MOD") or THAT)
YML = Path(os.environ.get("DOTOKEN_YML_MOD") or YML_THAT)

BAN_HONG_HAN_GIO = 6


def _chay(goc):
    """Gọi script bằng subprocess — đúng cách CI gọi nó. Trả (ma_thoat, stdout)."""
    r = subprocess.run([sys.executable, str(SCRIPT), "--goc", str(goc)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def _dung_kho(thu_muc, so_file=1, so_luot=2, noi_dung_them=None):
    """Dựng thư mục projects giả với bản ghi phiên hợp lệ."""
    for i in range(so_file):
        d = Path(thu_muc) / ("du-an-%d" % i)
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "phien.jsonl", "w", encoding="utf-8") as f:
            for _ in range(so_luot):
                f.write(json.dumps({
                    "timestamp": "2026-08-10T04:10:00.000Z",
                    "message": {"usage": {
                        "input_tokens": 100,
                        "cache_creation_input_tokens": 1000,
                        "cache_read_input_tokens": 10000,
                        "output_tokens": 200}},
                }) + "\n")
            if noi_dung_them:
                f.write(json.dumps({"type": "user", "message": {
                    "role": "user", "content": noi_dung_them}}) + "\n")
    return thu_muc


def _khoi_buoc_do(yml):
    """Trả phần văn bản CỦA RIÊNG bước 'Đo mức tiêu thụ' — từ dòng `- name:` của nó tới
    dòng `- name:` kế tiếp (hoặc hết file). Dùng phép cắt thô thay vì nạp YAML để bộ ca
    chạy được trên máy CI không cài sẵn thư viện YAML."""
    dong = yml.splitlines()
    dau = None
    for i, l in enumerate(dong):
        if l.strip().startswith("- name:") and "Đo mức tiêu thụ" in l:
            dau = i
            break
    if dau is None:
        return ""
    cuoi = len(dong)
    for j in range(dau + 1, len(dong)):
        if dong[j].strip().startswith("- name:"):
            cuoi = j
            break
    return "\n".join(dong[dau:cuoi])


# ─────────────────────────── các ca ───────────────────────────

def cac_ca():
    ca = []

    # [01] ĐỐI CHỨNG — có bản ghi hợp lệ thì phải ra số, và KHÔNG được nói không đo được.
    with tempfile.TemporaryDirectory() as td:
        _dung_kho(td, so_file=1, so_luot=2)
        rc, out = _chay(td)
        ca.append(("[01] co ban ghi -> ra so",
                   rc == 0 and "KHONG DO DUOC" not in out.replace("Ô", "O")
                   and "KHÔNG ĐO ĐƯỢC" not in out and "số lượt   : 2" in out))

    # [02][03][04] PHẢI CHẶN — ba tình huống "không đo được" khác nhau.
    #
    # ⚠ Ba nhánh này bảo vệ CÙNG một hành vi và CHỒNG lên nhau: gỡ nhánh 'không có thư
    # mục' thì os.walk trả rỗng và nhánh 'thư mục rỗng' vẫn kêu; gỡ tiếp thì nhánh
    # 'không dòng nào mang số' vẫn kêu. Nếu ca chỉ kiểm cụm "KHÔNG ĐO ĐƯỢC" thì gỡ một
    # lớp chẳng ca nào đỏ, tức bộ ca không phân biệt nổi ba lớp.
    # Vì thế mỗi ca kiểm ĐÚNG LÝ DO của lớp mình: lớp bị gỡ làm thông điệp đổi sang lý
    # do của lớp kế tiếp, và ca đó đỏ ngay.
    with tempfile.TemporaryDirectory() as td:
        rc, out = _chay(Path(td) / "khong-co")
        ca.append(("[02] thu muc khong co -> KHONG DO DUOC dung ly do",
                   rc == 0 and "KHÔNG ĐO ĐƯỢC" in out and "quy đổi" not in out
                   and "không có thư mục bản ghi phiên" in out))

    with tempfile.TemporaryDirectory() as td:
        rc, out = _chay(td)
        ca.append(("[03] thu muc rong -> KHONG DO DUOC dung ly do",
                   rc == 0 and "KHÔNG ĐO ĐƯỢC" in out and "quy đổi" not in out
                   and "rỗng" in out))

    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "du-an"
        d.mkdir(parents=True)
        with open(d / "phien.jsonl", "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "message": {"content": "chào"}}) + "\n")
        rc, out = _chay(td)
        ca.append(("[04] khong dong nao co so -> KHONG DO DUOC dung ly do",
                   rc == 0 and "KHÔNG ĐO ĐƯỢC" in out and "quy đổi" not in out
                   and "không dòng nào mang số liệu" in out))

    # [05] BẢO MẬT — repo CÔNG KHAI. Đầu ra không được mang một mẩu nội dung nào,
    #      kể cả tên file hay đường dẫn (tên thư mục dự án chính là tên việc của Huy).
    BI_MAT = "NOI-DUNG-RIENG-KHONG-DUOC-IN-RA"
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / BI_MAT
        d.mkdir(parents=True)
        with open(d / "phien.jsonl", "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "message": {"usage": {"input_tokens": 1, "output_tokens": 1}},
            }) + "\n")
            f.write(json.dumps({"type": "user", "message": {
                "role": "user", "content": BI_MAT}}) + "\n")
        rc, out = _chay(td)
        ca.append(("[05] khong lo noi dung/duong dan", BI_MAT not in out))

    # [06] Trọng số quy đổi đúng: 100×1 + 1000×1,25 + 10000×0,1 + 200×5 = 3350 mỗi lượt.
    with tempfile.TemporaryDirectory() as td:
        _dung_kho(td, so_file=1, so_luot=1)
        rc, out = _chay(td)
        dong = [l for l in out.splitlines() if l.startswith("JSON ")]
        ok = False
        if dong:
            try:
                ok = json.loads(dong[0][5:]).get("quy_doi") == 3350
            except Exception:
                ok = False
        ca.append(("[06] trong so quy doi dung", ok))

    # [07] Dòng JSON hỏng không được làm chết phép đo.
    with tempfile.TemporaryDirectory() as td:
        _dung_kho(td, so_file=1, so_luot=1)
        p = next(Path(td).rglob("*.jsonl"))
        with open(p, "a", encoding="utf-8") as f:
            f.write("{hong khong phai json\n")
        rc, out = _chay(td)
        ca.append(("[07] dong hong khong lam chet", rc == 0 and "số lượt   : 1" in out))

    # [08] Mã thoát LUÔN 0 — bước đo chạy sau khi bản tin đã quét xong, không được
    #      làm gãy job dù hỏng kiểu gì.
    with tempfile.TemporaryDirectory() as td:
        rc, _ = _chay(Path(td) / "khong-co")
        ca.append(("[08] ma thoat luon 0", rc == 0))

    # [09] Đếm đúng số phiên: 2 file bản ghi -> 2 phiên.
    with tempfile.TemporaryDirectory() as td:
        _dung_kho(td, so_file=2, so_luot=1)
        rc, out = _chay(td)
        ca.append(("[09] dem dung so phien", "số phiên  : 2" in out))

    # [10] Workflow THẬT phải gọi script này — cổng đúng mà không ai gọi thì vô nghĩa.
    try:
        yml = YML.read_text(encoding="utf-8")
    except OSError:
        yml = ""
    ca.append(("[10] workflow co goi buoc do", "do_token_phien.py" in yml))

    # [11] Bước đo trong workflow phải KHÔNG làm gãy job: có continue-on-error.
    # ⚠ Soi TRONG KHOI cua buoc, KHONG grep ca bai: chinh doan chu thich dat ngay tren
    # buoc do co nhac chu "continue-on-error" de giai thich vi sao can no, nen grep ca
    # file thi ban hong da go rao chan van xanh — cong tu nuot mat rang cua no.
    ca.append(("[11] buoc do khong lam gay job",
               "continue-on-error: true" in _khoi_buoc_do(yml)))

    return ca


def chay_bo_ca():
    ca = cac_ca()
    do = [ten for ten, ok in ca if not ok]
    return ca, do


def _don_rac(thu_muc):
    """Xoá bản hỏng mồ côi. Cắt bằng TUỔI FILE trước khi hỏi pid: mtime khong noi doi,
    pid thi co — he dieu hanh cap lai pid cho tien trinh khac."""
    for f in os.listdir(thu_muc):
        if not f.startswith("_thu-hong-"):
            continue
        p = os.path.join(thu_muc, f)
        try:
            if (time.time() - os.path.getmtime(p)) / 3600 > BAN_HONG_HAN_GIO:
                os.unlink(p)
        except OSError:
            pass


def tu_kiem():
    # Bộ ca phải XANH trên bản đúng trước đã: một ca đỏ sẵn cũng đỏ ở bản hỏng nên không
    # làm lệch phép so nào, và --tu-kiem sẽ trả mã 0 trong khi bộ ca đang hỏng.
    r = subprocess.run([sys.executable, os.path.abspath(__file__)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print("✗ Bo ca DO ngay tren ban dung — sua bo ca truoc khi tu kiem.")
        return 1

    _don_rac(str(THAT.parent))
    _don_rac(str(YML_THAT.parent))
    tong_hong = 0
    print("Dung ban hong, moi ban go dung mot lop va:\n")
    for ten, loai, tim, thay, phai_do in BAN_HONG:
        goc_f = THAT if loai == "py" else YML_THAT
        goc = goc_f.read_text(encoding="utf-8")
        if goc.count(tim) != 1:
            print("  ✗ %s — chuoi neo khop %d cho (phai dung 1)" % (ten, goc.count(tim)))
            tong_hong += 1
            continue
        noi_dung = goc.replace(tim, thay)
        sha = hashlib.sha1(noi_dung.encode()).hexdigest()[:8]
        p = goc_f.parent / ("_thu-hong-%d-%s-%s" % (os.getpid(), sha, goc_f.name))
        env_key = "DOTOKEN_SCRIPT_MOD" if loai == "py" else "DOTOKEN_YML_MOD"
        try:
            p.write_text(noi_dung, encoding="utf-8")
            r = subprocess.run([sys.executable, os.path.abspath(__file__)],
                               capture_output=True, text=True,
                               env=dict(os.environ, **{env_key: str(p)}))
            do = [l.split()[1] for l in r.stdout.splitlines() if l.strip().startswith("✗")]
            if len(do) == len(cac_ca()):
                print("  ✗ %s — ban hong lam DO TOAN BO ca: phep thay hong cu phap, "
                      "khong phai go lop va" % ten)
                tong_hong += 1
                continue
            thieu = [s for s in phai_do if s not in do]
            if thieu:
                print("  ✗ %s — ca %s KHONG do (do: %s)"
                      % (ten, ", ".join(thieu), ", ".join(do) or "khong ca nao"))
                tong_hong += 1
            else:
                print("  ✓ %s — bat duoc, ca do: %s" % (ten, ", ".join(do)))
        finally:
            try:
                p.unlink()
            except OSError:
                pass
    print()
    if tong_hong:
        print("✗ %d/%d ban hong KHONG bi bat." % (tong_hong, len(BAN_HONG)))
        return 1
    print("✓ %d/%d ban hong deu bi bat." % (len(BAN_HONG), len(BAN_HONG)))
    return 0


def main():
    if "--tu-kiem" in sys.argv[1:]:
        return tu_kiem()
    ca, do = chay_bo_ca()
    for ten, ok in ca:
        print("  %s %s" % ("✓" if ok else "✗", ten))
    print()
    if do:
        print("✗ %d/%d ca DO." % (len(do), len(ca)))
        return 1
    print("✓ %d/%d ca dat." % (len(ca), len(ca)))
    return 0


# ⚠ Quy uoc: bang BAN_HONG dat CUOI file, sau ma.
# Moi dong: (ten, loai file, chuoi neo, phan thay, danh sach ma ca PHAI DO).
BAN_HONG = [
    ("go nhanh 'khong co thu muc'", "py",
     "    if not os.path.isdir(goc):",
     "    if False:",
     ["[02]"]),
    ("go nhanh 'thu muc rong'", "py",
     "    if not dd:\n        return ('KHÔNG ĐO ĐƯỢC — thư mục bản ghi phiên rỗng (%s).\\n'",
     "    if False:\n        return ('KHÔNG ĐO ĐƯỢC — thư mục bản ghi phiên rỗng (%s).\\n'",
     ["[03]"]),
    ("go nhanh 'khong dong nao mang so'", "py",
     "    if c['luot'] == 0:",
     "    if False:",
     ["[04]"]),
    ("in ca duong dan ban ghi ra log (lo noi dung, repo CONG KHAI)", "py",
     "        '  số phiên  : %d' % phien,",
     "        '  số phiên  : %d %s' % (phien, dd),",
     ["[05]"]),
    ("doi trong so quy doi", "py",
     "TRONG_SO = {'in': 1.0, 'cc': 1.25, 'cr': 0.1, 'out': 5.0}",
     "TRONG_SO = {'in': 1.0, 'cc': 1.0, 'cr': 1.0, 'out': 1.0}",
     ["[06]"]),
    # Chi khai [10]: go dong lenh chay khong dung toi rao chan `continue-on-error` cua
    # cung buoc do, nen [11] van xanh — khai thua se lam --tu-kiem truot vi ly do SAI.
    ("go buoc do khoi workflow", "yml",
     "python3 .github/scripts/do_token_phien.py",
     "echo 'da go buoc do'",
     ["[10]"]),
    # ⚠ Chuoi thay KHONG duoc chua chinh tu khoa ma ca [11] dang kiem — ban hong dau
    # tien viet "# continue-on-error da bi go" nen ca [11] van thay tu khoa va van xanh.
    ("go continue-on-error cua buoc do", "yml",
     "        continue-on-error: true   # bước đo KHÔNG được làm gãy bản tin",
     "        # rao chan da bi go",
     ["[11]"]),
]

if __name__ == "__main__":
    sys.exit(main())

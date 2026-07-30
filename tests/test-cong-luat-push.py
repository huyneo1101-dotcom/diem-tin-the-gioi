#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CỔNG "WORKFLOW CÓ LỊCH THÌ CẤM REBASE FILE DÙNG CHUNG"
(`.github/scripts/kiem_luat_push.py`).

⚠ VÌ SAO CÓ FILE NÀY
Bản vá 30/07/2026 (`ghi_so_push.py`) chỉ bịt ĐÚNG HAI workflow ghi `logs/da-gui-email.json`.
Lớp lỗi rộng hơn thế: workflow nào vừa chạy theo LỊCH (không ai ngồi canh), vừa commit file
mà NHIỀU nguồn cũng ghi, vừa hợp nhất bằng `pull --rebase`, đều tái diễn được đúng sự cố ấy
— rebase xung đột, 05 vòng retry chết tiếp trên trạng thái đã bẩn, lô tin mất trong im lặng.
`import-news-from-drive.yml` là ca cuối cùng thuộc loại đó; nó đã bỏ cron ngày 30/07/2026.

Cổng là thứ giữ cho việc bỏ cron ấy không bị lặng lẽ đảo ngược. Mà cổng thuộc đúng loại
"hỏng thì nhìn y hệt sạch": không có workflow nào vi phạm thì cổng im, và cổng chết cũng im
y hệt — chạy trăm lần thấy nó không kêu KHÔNG chứng minh được gì. Vì vậy trọng tâm file này
là các **ca PHẢI CHẶN**, kèm ca đối chứng để khoanh đúng nguyên nhân khi có ca đỏ.

Chạy:
    python3 tests/test-cong-luat-push.py
    python3 tests/test-cong-luat-push.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi

Cần PyYAML (`pip install pyyaml`) — chính cổng cũng cần.

⚠ Cố tình KHÔNG gọi cổng bằng `subprocess`: subprocess luôn khởi động lại Python và nạp bản
THẬT trên đĩa, nên `--tu-kiem` không tráo được bản hỏng vào và mọi ca sẽ xanh trên cả bản
đúng lẫn bản hỏng — một bộ test vô dụng mà nhìn bảng kết quả không thấy gì bất thường (luật
mục 17 CLAUDE.md, vấp thật ở `test-cong-vow.py` bên Rèn 66). Ở đây gọi thẳng `main()` trong
tiến trình và bắt stdout bằng `contextlib.redirect_stdout`.
"""
import contextlib
import importlib.util
import io
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
CONG_THAT = REPO / ".github" / "scripts" / "kiem_luat_push.py"

# Seam để --tu-kiem tráo bản hỏng. Mặc định là bản thật.
CONG_PATH = pathlib.Path(os.environ.get("LUATPUSH_MOD") or CONG_THAT)


def _nap_cong(p: pathlib.Path):
    spec = importlib.util.spec_from_file_location(f"cong_luat_push_{p.stem}", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _chay(mod, argv):
    """Gọi main() trong tiến trình, trả (mã thoát, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main(argv)
    return rc, buf.getvalue()


# ───────────────────────────── khuôn workflow để dựng ca ─────────────────────────────
def _wf(on_block: str, run_block: str) -> str:
    dong = "\n".join("          " + d for d in run_block.strip("\n").split("\n"))
    return f"""name: Ca thu
on:
{on_block}
jobs:
  viec:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - name: Commit if changed
        run: |
{dong}
"""


LICH = "  schedule:\n    - cron: '23 0,12 * * *'\n  workflow_dispatch:"
TAY = "  workflow_dispatch:"

# Khối commit THẬT của import-news-from-drive.yml (rút gọn phần không liên quan).
RUN_DRIVE = """
git add index.html logs/
git commit -m "Nhap ban tin tu Google Drive"
for i in 1 2 3 4 5; do
  if git push; then exit 0; fi
  git pull --rebase origin main || { echo "::error::rebase conflict"; exit 1; }
done
"""

RUN_LOGS = """
git add logs/state.json
git commit -m "log"
git pull --rebase origin main && git push
"""

RUN_CA_REPO = """
git add -A
git commit -m "moi thu"
git pull --rebase origin main && git push
"""

# harvest-ci: file RIÊNG (01 nguồn ghi) — rebase ở đây không có gì để xung đột.
RUN_FILE_RIENG = """
git add docs/ung-vien-ci.json
git commit -m "harvest: lo ung vien"
git pull --rebase origin main && git push origin main
"""

# claude-web-scan: pull --rebase để lấy code mới, KHÔNG commit gì.
RUN_KHONG_ADD = """
git pull --rebase origin main || true
gh workflow run notify-email.yml
"""

# Hợp nhất đúng cách: không rebase.
RUN_KHONG_REBASE = """
git add index.html logs/
git commit -m "ban tin"
python3 .github/scripts/ghi_so_push.py --buoi sang
"""


def _dung(tmp: pathlib.Path, ten: str, noi_dung: str) -> pathlib.Path:
    d = tmp / ten
    d.mkdir(parents=True, exist_ok=True)
    (d / "ca.yml").write_text(noi_dung, encoding="utf-8")
    return d


# ───────────────────────────────────── các ca ─────────────────────────────────────
def ca01_bat_lai_lich_drive(mod, tmp):
    """PHẢI CHẶN — bật lại cron cho đúng khối commit của import-news-from-drive."""
    rc, out = _chay(mod, [str(_dung(tmp, "ca01", _wf(LICH, RUN_DRIVE)))])
    assert rc == 1, f"cong KHONG chan (rc={rc}) — bat lai lich ma van rebase index.html"
    assert "index.html" in out, "khong chi ra file dung chung nao bi cham"


def ca02_lich_them_thu_muc_logs(mod, tmp):
    """PHẢI CHẶN — `git add logs/state.json`: logs/ có 03 nguồn ghi."""
    rc, out = _chay(mod, [str(_dung(tmp, "ca02", _wf(LICH, RUN_LOGS)))])
    assert rc == 1, f"cong KHONG chan (rc={rc}) — logs/ la file dung chung"


def ca03_lich_add_ca_repo(mod, tmp):
    """PHẢI CHẶN — `git add -A` đương nhiên ăn luôn file dùng chung."""
    rc, out = _chay(mod, [str(_dung(tmp, "ca03", _wf(LICH, RUN_CA_REPO)))])
    assert rc == 1, f"cong KHONG chan (rc={rc}) — `git add -A` om ca repo"


def ca04_on_quote_van_chan(mod, tmp):
    """PHẢI CHẶN — `"on":` viết dạng chuỗi có nháy.

    Đối chứng của bẫy YAML 1.1: khoá `on:` không nháy bị parse thành boolean True, còn
    `"on":` thì ra chuỗi "on". Cổng phải đọc được CẢ HAI; đọc thiếu một dạng là câm với
    đúng những file viết theo dạng kia.
    """
    wf = _wf(LICH, RUN_DRIVE).replace("\non:\n", '\n"on":\n')
    rc, out = _chay(mod, [str(_dung(tmp, "ca04", wf))])
    assert rc == 1, f"cong KHONG chan (rc={rc}) — dang `\"on\":` co nhay bi bo sot"


def ca05_chay_tay_thi_cho_qua(mod, tmp):
    """ĐỐI CHỨNG — đúng trạng thái sau khi tắt lịch 30/07: chạy tay thì có người canh."""
    rc, out = _chay(mod, [str(_dung(tmp, "ca05", _wf(TAY, RUN_DRIVE)))])
    assert rc == 0, f"CHAN OAN (rc={rc}) — chi con workflow_dispatch thi khong phai vi pham"


def ca06_lich_nhung_khong_rebase(mod, tmp):
    """ĐỐI CHỨNG — có lịch, có file dùng chung, nhưng hợp nhất đúng cách."""
    rc, out = _chay(mod, [str(_dung(tmp, "ca06", _wf(LICH, RUN_KHONG_REBASE)))])
    assert rc == 0, f"CHAN OAN (rc={rc}) — bo rebase roi ma van chan thi khong ai va noi"


def ca07_file_rieng_thi_cho_qua(mod, tmp):
    """ĐỐI CHỨNG — harvest-ci: `docs/ung-vien-ci.json` chỉ 01 nguồn ghi."""
    rc, out = _chay(mod, [str(_dung(tmp, "ca07", _wf(LICH, RUN_FILE_RIENG)))])
    assert rc == 0, f"CHAN OAN (rc={rc}) — file rieng thi rebase khong co gi de xung dot"


def ca08_rebase_ma_khong_commit(mod, tmp):
    """ĐỐI CHỨNG — claude-web-scan: pull để lấy code mới, không commit gì."""
    rc, out = _chay(mod, [str(_dung(tmp, "ca08", _wf(LICH, RUN_KHONG_ADD)))])
    assert rc == 0, f"CHAN OAN (rc={rc}) — khong `git add` gi thi khong co lo nao de mat"


def ca09_yml_hong_phai_keu(mod, tmp):
    """PHẢI CHẶN (fail-closed) — yml hỏng cú pháp phải trả 2, tuyệt đối không 0."""
    d = tmp / "ca09"
    d.mkdir(parents=True, exist_ok=True)
    (d / "hong.yml").write_text("on:\n  schedule:\n   - cron: '* * * * *'\n  jobs: [\n",
                                encoding="utf-8")
    rc, out = _chay(mod, [str(d)])
    assert rc == 2, (f"FAIL-OPEN (rc={rc}) — yml khong doc duoc ma cong bao sach; "
                     f"'khong thay vi pham' khac 'khong nhin duoc'")


def ca10_thu_muc_rong_phai_keu(mod, tmp):
    """PHẢI CHẶN (fail-closed) — không có workflow nào: đường dẫn sai, phải kêu."""
    d = tmp / "ca10"
    d.mkdir(parents=True, exist_ok=True)
    rc, out = _chay(mod, [str(d)])
    assert rc == 2, f"FAIL-OPEN (rc={rc}) — thu muc rong ma bao sach thi cong tu tat luc bi don"


def ca11_repo_that_phai_sach(mod, tmp):
    """Trạng thái THẬT của repo hôm nay phải qua cổng — không thì cổng là cổng chết."""
    rc, out = _chay(mod, [])
    assert rc == 0, (f"repo THAT dang vi pham (rc={rc}):\n{out}\n"
                     f"→ hoac co ai bat lai lich, hoac cong dang chan oan ca luong binh thuong")


CAC_CA = [
    ("01 PHẢI CHẶN · bật lại lịch cho drive-import", ca01_bat_lai_lich_drive),
    ("02 PHẢI CHẶN · lịch + git add logs/", ca02_lich_them_thu_muc_logs),
    ("03 PHẢI CHẶN · lịch + git add -A", ca03_lich_add_ca_repo),
    ('04 PHẢI CHẶN · dạng "on": có nháy', ca04_on_quote_van_chan),
    ("05 đối chứng · chỉ workflow_dispatch", ca05_chay_tay_thi_cho_qua),
    ("06 đối chứng · có lịch nhưng không rebase", ca06_lich_nhung_khong_rebase),
    ("07 đối chứng · file riêng (harvest-ci)", ca07_file_rieng_thi_cho_qua),
    ("08 đối chứng · rebase mà không commit", ca08_rebase_ma_khong_commit),
    ("09 fail-closed · yml hỏng cú pháp", ca09_yml_hong_phai_keu),
    ("10 fail-closed · thư mục không có workflow", ca10_thu_muc_rong_phai_keu),
    ("11 repo THẬT phải sạch", ca11_repo_that_phai_sach),
]


def chay_bo(mod) -> list:
    """Chạy hết các ca, trả danh sách tên ca ĐỎ."""
    do = []
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="test-luat-push-"))
    try:
        for ten, f in CAC_CA:
            try:
                f(mod, tmp)
                print(f"  ✓ {ten}")
            except AssertionError as e:
                do.append(ten)
                print(f"  ✗ {ten}\n      {e}")
            except Exception as e:                    # lỗi lạ cũng là ĐỎ
                do.append(ten)
                print(f"  ✗ {ten}\n      LOI LA: {type(e).__name__}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return do


# ─────────────────────────────────── --tu-kiem ───────────────────────────────────
# Mỗi bản hỏng gỡ ĐÚNG MỘT lớp bảo vệ, kèm ca bắt buộc phải đỏ vì lớp đó.
#
# ⚠ Bản hỏng phải nằm trong CHÍNH thư mục thật của cổng — cổng tự tìm repo root từ
#   `__file__`, để chỗ khác là ca 11 đỏ vì lý do sai.
# ⚠ Đừng khai thừa ca phải đỏ: khai một ca không liên quan thì --tu-kiem báo trượt vì lý do
#   sai, che mất bản hỏng thật sự không bắt được.
BAN_HONG = [
    (
        "lờ điều kiện LỊCH — soi cả workflow chạy tay",
        [("    if not _co_lich(doc):\n        return []\n", "")],
        ["05 đối chứng · chỉ workflow_dispatch"],
    ),
    (
        "quên bẫy YAML 1.1: chỉ đọc doc.get(\"on\"), bỏ nhánh True",
        [('    on = doc.get("on", doc.get(True))', '    on = doc.get("on")')],
        ["01 PHẢI CHẶN · bật lại lịch cho drive-import",
         "02 PHẢI CHẶN · lịch + git add logs/",
         "03 PHẢI CHẶN · lịch + git add -A"],
    ),
    (
        "lờ điều kiện REBASE — chặn mọi workflow commit file dùng chung",
        [("        if not RE_REBASE.search(run):\n            continue\n", "")],
        ["06 đối chứng · có lịch nhưng không rebase"],
    ),
    (
        "lờ điều kiện FILE DÙNG CHUNG — mọi `git add` đều tính",
        [("        if cham:", "        if cham or RE_GIT_ADD.search(run):")],
        ["07 đối chứng · file riêng (harvest-ci)"],
    ),
    (
        "bỏ `logs/` khỏi danh sách file dùng chung",
        # Neo bằng chuỗi NGẮN, không ôm phần chú thích: chú thích là chỗ dễ lệch một dấu
        # cách nhất, mà lệch thì --tu-kiem báo "KHÔNG áp được phép thay" chứ không báo lỗi
        # thật của cổng — đọc bảng sẽ tưởng ca này vô dụng.
        [('    "logs/",\n', ""), ('    "logs",', '    "logs-KHONG-PHAI-TEN-THAT",')],
        ["02 PHẢI CHẶN · lịch + git add logs/"],
    ),
    (
        "bỏ nhận diện `git add -A` (add cả repo)",
        [("        if tok in ADD_CA_REPO:\n            dinh.append(tok + \" (cả repo)\")\n            continue\n", "")],
        ["03 PHẢI CHẶN · lịch + git add -A"],
    ),
    (
        "FAIL-OPEN khi yml hỏng cú pháp — nuốt lỗi rồi bảo sạch",
        [('            print(f"::error::CONG LUAT PUSH: {e}")\n            return 2',
          '            continue')],
        ["09 fail-closed · yml hỏng cú pháp"],
    ),
    (
        "FAIL-OPEN khi thư mục không có workflow nào",
        [("              f\"duong dan sai, hay repo bi don? Khong doc duoc thi phai keu, khong duoc lang im.\")\n        return 2",
          "              f\"duong dan sai, hay repo bi don? Khong doc duoc thi phai keu, khong duoc lang im.\")\n        return 0")],
        ["10 fail-closed · thư mục không có workflow"],
    ),
]


def tu_kiem() -> int:
    goc = CONG_THAT.read_text(encoding="utf-8")
    thu_muc = CONG_THAT.parent
    print("── TỰ KIỂM: dựng bản cổng HỎNG, khẳng định bộ test này BẮT ĐƯỢC ──\n")
    truot = []

    for i, (ten, phep_thay, phai_do) in enumerate(BAN_HONG, 1):
        src = goc
        loi_thay = None
        for cu, moi in phep_thay:
            n = src.count(cu)
            if n != 1:
                loi_thay = f"KHÔNG áp được phép thay: {n} chỗ khớp cho {cu[:60]!r}"
                break
            src = src.replace(cu, moi, 1)
        if loi_thay:
            print(f"[{i}] {ten}\n    ✗ TRƯỢT — {loi_thay}\n")
            truot.append(ten)
            continue

        p = thu_muc / f"_hong-{os.getpid()}-{i}-kiem-luat-push.py"
        p.write_text(src, encoding="utf-8")
        try:
            print(f"[{i}] {ten}")
            try:
                mod = _nap_cong(p)
            except Exception as e:
                print(f"    ✗ TRƯỢT — ban hong khong nap noi ({type(e).__name__}: {e}); "
                      f"sua lai phep thay\n")
                truot.append(ten)
                continue
            do = chay_bo(mod)

            # Bản hỏng làm ĐỎ TOÀN BỘ ca = phép thay hỏng cú pháp/ngữ nghĩa nền, không phải
            # gỡ đúng một lớp vá. Nó chỉ chứng minh Python biết báo lỗi, không chứng minh ca
            # nào có răng. (Luật đúc 30/07/2026 từ ViecBot/test-bao-cao-xong.py.)
            if len(do) == len(CAC_CA):
                print(f"    ✗ TRƯỢT — ban hong lam DO TOAN BO {len(do)} ca; phep thay pha "
                      f"hong nen chu khong go dung mot lop va. Sua lai phep thay.\n")
                truot.append(ten)
                continue

            thieu = [c for c in phai_do if c not in do]
            if thieu:
                print(f"    ✗ TRƯỢT — ca sau ĐÁNG LẼ phải đỏ mà vẫn xanh: {thieu}\n")
                truot.append(ten)
            else:
                print(f"    ✓ bắt được ({len(do)} ca đỏ)\n")
        finally:
            p.unlink(missing_ok=True)
            shutil.rmtree(thu_muc / "__pycache__", ignore_errors=True)

    print("─" * 70)
    if truot:
        print(f"TỰ KIỂM TRƯỢT {len(truot)}/{len(BAN_HONG)}: {truot}")
        return 1
    print(f"TỰ KIỂM ĐẠT — bắt được {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng.")
    return 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    print(f"── TEST CỔNG LUẬT PUSH ({CONG_PATH.name}) ──\n")
    do = chay_bo(_nap_cong(CONG_PATH))
    print("\n" + "─" * 70)
    if do:
        print(f"ĐỎ {len(do)}/{len(CAC_CA)} ca: {do}")
        return 1
    print(f"ĐẠT {len(CAC_CA)}/{len(CAC_CA)} ca.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG: WORKFLOW CHẠY THEO LỊCH THÌ CẤM HỢP NHẤT FILE DÙNG CHUNG BẰNG `pull --rebase`.

VÌ SAO CÓ FILE NÀY
──────────────────
Sáng 30/07/2026, `notify-morning.yml` và `notify-email.yml` ghi `logs/da-gui-email.json`
cách nhau 07 GIÂY. Khối commit cũ (chép y nhau ở hai workflow) `git pull --rebase origin
main` ⇒ rebase phát lại commit của mình lên trên commit của workflow kia, hai bên sửa đúng
cùng chỗ trong JSON nên XUNG ĐỘT; rebase hỏng để repo ở trạng thái rebase dở nên cả 05 vòng
retry chết tiếp. Hậu quả dây chuyền: canary kêu oan + hai phiên CI dự phòng quét lại tốn
token. Luật hợp nhất đúng nay nằm ở `.github/scripts/ghi_so_push.py`.

Nhưng bản vá đó chỉ bịt ĐÚNG HAI workflow ghi sổ. Lớp lỗi thì rộng hơn: bất kỳ workflow nào
(a) chạy theo LỊCH — tức không có người ngồi canh, (b) commit một file mà NHIỀU nguồn khác
cũng ghi, (c) hợp nhất bằng `pull --rebase`, đều tái diễn được đúng sự cố đó. Cổng này canh
tổ hợp ba điều kiện ấy, để phiên sau không chép lại khối lệnh cũ vào một workflow mới.

VÌ SAO PHẢI ĐỦ CẢ BA ĐIỀU KIỆN (đo thật 30/07/2026, `git log --format='%an' -- <file>` từ
01/07/2026 — đây là phép đo để chạy lại khi nghi ngờ, đừng đoán):

    index.html               05 nguồn ghi  ← DÙNG CHUNG
    logs/state.json          03 nguồn ghi  ← DÙNG CHUNG
    logs/da-gui-email.json   02 nguồn ghi  ← DÙNG CHUNG
    docs/ung-vien-ci.json    01 nguồn (harvest-ci)
    baomoi-saved.json        01 nguồn (sync-baomoi)
    docs/probe-ci.json       01 nguồn (probe-sources)

Bỏ bớt bất cứ điều kiện nào là cổng kêu oan, mà theo mục 17 CLAUDE.md thì **cổng nào cũng
phải mở cờ mới qua được là cổng chết** — kêu oan vài lần là bảng hết được đọc:
  · bỏ (a): `import-news-from-drive.yml` chạy tay vẫn dính, trong khi chạy tay có người canh;
  · bỏ (b): `harvest-ci` / `sync-baomoi` / `sync-preferences` / `probe-sources` cùng dính,
    dù mỗi cái chỉ ghi file riêng của nó nên rebase không có gì để xung đột;
  · bỏ (c): mọi workflow commit `index.html` đều dính, kể cả cái hợp nhất đúng cách.

Ở trạng thái ngày 30/07/2026, sau khi `import-news-from-drive.yml` bỏ cron, **KHÔNG workflow
nào vi phạm** — cổng xanh ở luồng bình thường, chỉ đỏ khi có người bật lại lịch mà chưa vá.

GIỚI HẠN ĐÃ BIẾT (khai ra để không ai tưởng cổng này phủ nhiều hơn thực tế): cổng chỉ đọc
được lệnh git viết THẲNG trong `run:` của file yml. Lệnh git do phiên `claude -p` tự gõ bên
trong `claude-web-scan.yml` nằm ngoài tầm — thứ canh chỗ đó là playbook quét, không phải
cổng này.

Chạy:
    python3 .github/scripts/kiem_luat_push.py            # quét .github/workflows của repo
    python3 .github/scripts/kiem_luat_push.py <thư mục>  # quét thư mục khác (bộ test dùng)

Mã thoát: 0 = sạch · 1 = có vi phạm · 2 = không đọc được (fail-CLOSED, xem dưới).

⚠️ FAIL-CLOSED: yml hỏng cú pháp, hay thư mục không có file workflow nào, đều trả 2 chứ
KHÔNG trả 0. Cổng không đọc được thì phải KÊU — "không thấy vi phạm" và "không nhìn được"
là hai chuyện khác nhau, mà lẫn chúng vào nhau chính là kiểu chết câm cổng này sinh ra để
chặn (mục 17 CLAUDE.md).
"""
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WF_MAC_DINH = ROOT / ".github" / "workflows"

# File có ≥02 nguồn ghi — xem phép đo ở docstring. Thêm file vào đây khi một file bắt đầu
# có nguồn ghi thứ hai; đo lại bằng:
#   git log --since=<mốc> --format='%an' -- <file> | sort -u
FILE_DUNG_CHUNG = (
    "index.html",
    "logs/",
    "logs",          # `git add logs` (không dấu /) cũng là cả thư mục
    "data/",
    "data",
)

# `git add` cả repo thì đương nhiên ăn luôn file dùng chung.
ADD_CA_REPO = ("-a", "-A", "--all", "-u", "--update", ".", ":/", "*")

RE_GIT_ADD = re.compile(r"\bgit\s+add\s+([^\n;&|]+)")
RE_REBASE = re.compile(r"\bgit\s+(?:pull\s+[^\n;&|]*--rebase|rebase)\b")


def _co_lich(doc) -> bool:
    """Workflow có chạy theo lịch không.

    ⚠️ Bẫy YAML 1.1: khoá `on:` bị parse thành boolean True, KHÔNG phải chuỗi "on".
    Đọc nhầm khoá là cổng coi mọi workflow đều không có lịch ⇒ câm hoàn toàn.
    """
    if not isinstance(doc, dict):
        return False
    on = doc.get("on", doc.get(True))
    if isinstance(on, dict):
        return bool(on.get("schedule"))
    if isinstance(on, list):
        return "schedule" in on
    return on == "schedule"


def _dung_chung(lenh_add: str) -> list:
    """Trả các đối số của `git add` chạm tới file dùng chung."""
    dinh = []
    for tok in lenh_add.split():
        if tok.startswith("-") and tok not in ADD_CA_REPO:
            continue                      # cờ khác (vd --force) — bỏ qua
        if tok in ADD_CA_REPO:
            dinh.append(tok + " (cả repo)")
            continue
        sach = tok.strip("\"'")
        for f in FILE_DUNG_CHUNG:
            if sach == f or sach.rstrip("/") == f.rstrip("/") or sach.startswith(f.rstrip("/") + "/"):
                dinh.append(sach)
                break
    return dinh


def _cac_buoc_run(doc):
    """Sinh (tên bước, nội dung run) cho mọi bước của mọi job."""
    if not isinstance(doc, dict):
        return
    jobs = doc.get("jobs")
    if not isinstance(jobs, dict):
        return
    for ten_job, job in jobs.items():
        if not isinstance(job, dict):
            continue
        for i, buoc in enumerate(job.get("steps") or []):
            if not isinstance(buoc, dict):
                continue
            run = buoc.get("run")
            if isinstance(run, str) and run.strip():
                yield f"{ten_job} / {buoc.get('name') or f'bước {i + 1}'}", run


def soi_mot_file(p: pathlib.Path) -> list:
    """Trả danh sách vi phạm của một file yml. Ném ValueError nếu không đọc nổi."""
    try:
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as e:                                  # yml hỏng ⇒ fail-CLOSED
        raise ValueError(f"{p.name}: khong doc duoc yml — {e}")

    if not _co_lich(doc):
        return []

    vi_pham = []
    for ten_buoc, run in _cac_buoc_run(doc):
        if not RE_REBASE.search(run):
            continue
        cham = []
        for m in RE_GIT_ADD.finditer(run):
            cham += _dung_chung(m.group(1))
        if cham:
            vi_pham.append((p.name, ten_buoc, sorted(set(cham))))
    return vi_pham


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    thu_muc = pathlib.Path(argv[0]) if argv else WF_MAC_DINH

    files = sorted(
        [f for f in thu_muc.glob("*.yml") if f.is_file()]
        + [f for f in thu_muc.glob("*.yaml") if f.is_file()]
    )
    if not files:
        print(f"::error::CONG LUAT PUSH: khong thay workflow nao trong {thu_muc} — "
              f"duong dan sai, hay repo bi don? Khong doc duoc thi phai keu, khong duoc lang im.")
        return 2

    vi_pham = []
    for f in files:
        try:
            vi_pham += soi_mot_file(f)
        except ValueError as e:
            print(f"::error::CONG LUAT PUSH: {e}")
            return 2

    if not vi_pham:
        print(f"✓ Cong luat push: {len(files)} workflow, khong cai nao vua chay theo LICH "
              f"vua hop nhat file DUNG CHUNG bang `pull --rebase`.")
        return 0

    print("::error::CONG LUAT PUSH CHAN — workflow chay theo LICH ma hop nhat file DUNG "
          "CHUNG bang `git pull --rebase`. Day dung la lop loi gay su co so da gui sang "
          "30/07/2026: hai nguon commit sat nhau thi rebase xung dot, retry KHONG chua duoc "
          "(no thu lai dung phep toan vua hong tren dung trang thai da ban), va lo tin mat "
          "trong im lang.")
    for ten, buoc, cham in vi_pham:
        print(f"  · {ten} → bước “{buoc}” · git add: {', '.join(cham)}")
    print("\nCACH VA — chon MOT trong hai, dung them cach thu ba:")
    print("  01. Bo `schedule` khoi workflow, chi de `workflow_dispatch` (chay tay co nguoi canh).")
    print("  02. Bo `pull --rebase`, hop nhat lai cho dung ban chat cua file:")
    print("      · file APPEND-ONLY (so, log, hang doi): dung `.github/scripts/ghi_so_push.py`")
    print("        — fetch → reset --mixed FETCH_HEAD → checkout FETCH_HEAD -- <file> →")
    print("        append dong cua minh → commit CHI file do → push HEAD:main.")
    print("      · file KHONG append-only (`index.html`): git khong hop nhat duoc, phai CHAY")
    print("        LAI buoc sinh file (`add_news.py`) tren dinh moi — no dedupe theo URL.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

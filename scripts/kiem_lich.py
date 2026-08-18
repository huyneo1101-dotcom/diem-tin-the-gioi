#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG LỊCH — chú thích giờ VN phải khớp cron thật, và bảng lịch phải khớp workflow.

VÌ SAO CÓ FILE NÀY (bắt được 30/07/2026):
`claude-web-scan.yml` dời cả 04 mốc sớm 13 phút (21:00→20:47 · 22:00→21:47 · 04:00→03:47 ·
05:00→04:47) và `harvest-ci.yml` dời theo (20:45→20:32…), nhưng **47 chỗ trong tài liệu vẫn
ghi lịch cũ**: `CLAUDE.md` 25 chỗ · `docs/routine-web-scan.md` 15 · skill `quet-tin` 4 ·
`.github/prompts/web-scan-ci.md` 3. Chú thích của chính `canary.yml` còn ghi *"sau lớp vét TỐI
(CI 21:00 · local 21:15 · vét CI 22:00)"* — cả ba số đều chết.

**Cơ chế gây vấp:** giờ chạy bị chép ra hàng chục chỗ để người đọc tiện, mà **không chỗ nào là
nguồn sự thật** — nguồn thật là dòng `cron:` trong file yml. Sửa cron thì không có gì bắt phải
sửa những chỗ chép lại, nên chúng mục dần trong im lặng. Cái giá không phải sai lệch chữ nghĩa:
phiên sau đọc tài liệu rồi **tính biên thời gian theo mốc đã chết** — đúng loại lỗi đã làm
canary kêu oan (mốc canary `sukien` phải dời hai lần vì tính biên theo lịch cũ).

BA PHÉP ĐO:
  A. Mỗi dòng `- cron:` có chú thích `HH:MM` (giờ VN) thì giờ đó phải khớp cron + 7h. Đây là
     phép đo CHẮC CHẮN nhất — hai vế nằm trên CÙNG một dòng nên không có chỗ cho suy diễn.
  B. Bảng lịch trong `docs/LICH.md` (giữa hai marker) phải khớp cron thật của mọi workflow.
     Sinh lại bằng `--sinh`.
  C. Chú thích cron KHÔNG được nhắc mốc của workflow khác bằng số đã chết (ví dụ `CI 21:00`
     trong `canary.yml`) — đối chiếu với lịch thật của workflow được nhắc tên.

⚠️ **Lịch của scheduled task LOCAL không đo được**: app Claude giữ cron trong DB riêng, không
có file nào trên đĩa (đã kiểm 30/07: `~/.claude/scheduled-tasks/<id>/` chỉ có `SKILL.md`).
Vì vậy bảng lịch khai phần local BẰNG TAY trong `LOCAL_KHAI_TAY` dưới đây — sửa cron task thì
phải sửa ở đây, và đó là giới hạn đã biết, không phải chỗ để tưởng là đã có ai canh.

Chạy:
    python3 scripts/kiem_lich.py --kiem     # mã 0 = khớp · 1 = lệch
    python3 scripts/kiem_lich.py --sinh     # sinh lại bảng trong docs/LICH.md
    python3 scripts/kiem_lich.py --tu-kiem  # chứng minh --kiem bắt được lỗi
"""
import argparse
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WF_DIR = pathlib.Path(os.environ.get("KIEMLICH_WF") or (ROOT / ".github" / "workflows"))
LICH_MD = pathlib.Path(os.environ.get("KIEMLICH_MD") or (ROOT / "docs" / "LICH.md"))
BEGIN = "<!-- LICH:BEGIN — sinh bằng scripts/kiem_lich.py --sinh, ĐỪNG sửa tay -->"
END = "<!-- LICH:END -->"

# Lịch mốc LOCAL — KHAI TAY vì lịch nằm trong plist LaunchAgent, không nằm cạnh workflow.
# ⚠️ SỬA 18/08/2026: phần local KHÔNG CÒN chạy bằng scheduled task của app Claude.
# Từ 06/08/2026 cả hai mốc chuyển sang LaunchAgent gọi `routine-claude-headless.py`
# (`claude -p --model sonnet`), và tới 18/08/2026 `list_scheduled_tasks` trả về RỖNG —
# không còn task nào trong app. Bảng cũ khai `web-scan-diem-tin` cron `30 4,5` (04:30 · 05:30)
# là số đã chết: plist thật khai 04:30 VÀ 04:45, không có mốc 05:30 nào.
# Đo lại bằng: grep -A14 StartCalendarInterval ~/Library/LaunchAgents/com.huy.routine-diemtin-*.plist
LOCAL_KHAI_TAY = [
    ("com.huy.routine-diemtin-sang", "30,45 4 * * *", "04:30 · 04:45", "bật",
     "dự phòng bản tin SÁNG SỚM + event-scan (Bước 4) — LaunchAgent headless sonnet"),
    ("com.huy.routine-diemtin-toi", "15 21 * * *", "21:15", "bật",
     "dự phòng bản tin TỐI — lớp CUỐI còn kịp hạn email 22:00 — LaunchAgent headless sonnet"),
    ("com.huy.diemtin-giu-thuc-som", "41 3 * * *", "03:41", "bật",
     "caffeinate 90' giữ máy thức cho 2 mốc local sáng — CẶP với `pmset repeat` 03:40"),
    ("com.huy.diemtin-giu-thuc", "26 4 * * *", "04:26", "bật (lưới 2)",
     "caffeinate 90' — mốc cũ cặp với pmset 04:25 đã đổi, giữ làm lưới thứ hai"),
    ("com.huy.diemtin-giu-thuc-toi", "40 20 * * *", "20:40", "bật",
     "caffeinate 90' giữ máy thức cho mốc local tối 21:15"),
]
# LaunchAgent KHÔNG có jitter như scheduled task của app — nổ đúng giờ MIỄN LÀ máy đang thức.
# Máy ngủ thì launchd nổ MUỘN lúc máy tình cờ thức (đo 18/08: mốc 04:30 nổ 04:40:12) — đó là
# lý do phải có cặp caffeinate ở trên.
JITTER_GIAY = {}


def _gio_vn(cron: str):
    """('47 13 * * *') -> danh sách 'HH:MM' giờ VN. None nếu không phải mốc giờ cố định."""
    phan = cron.split()
    if len(phan) < 2 or not phan[0].isdigit():
        return None
    phut = int(phan[0])
    gio = []
    for g in phan[1].split(","):
        if not g.isdigit():
            return None
        gio.append(f"{(int(g) + 7) % 24:02d}:{phut:02d}")
    return gio


def doc_cron_workflow():
    """[(tên file, cron, chú thích cùng dòng, số dòng)] của mọi dòng `- cron:`."""
    ra = []
    for p in sorted(WF_DIR.glob("*.yml")):
        for i, dong in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            m = re.match(r"\s*-\s*cron:\s*['\"]([^'\"]+)['\"]\s*(?:#\s*(.*))?$", dong)
            if m:
                ra.append((p.name, m.group(1).strip(), (m.group(2) or "").strip(), i))
    return ra


def do_a_chu_thich_khop_cron():
    """A — giờ VN ghi trong chú thích phải khớp chính cron của dòng đó."""
    loi = []
    for ten, cron, ghi, dong in doc_cron_workflow():
        that = _gio_vn(cron)
        if that is None or not ghi:
            continue
        # chỉ xét giờ ĐỨNG ĐẦU chú thích — đó là giờ của chính mốc này; giờ nhắc mốc khác
        # (kiểu "trước mốc TỐI (CI 20:47)") do phép đo C lo.
        m = re.match(r"(\d{1,2}):(\d{2})", ghi)
        if not m:
            continue
        ghi_gio = f"{int(m.group(1)):02d}:{m.group(2)}"
        if ghi_gio not in that:
            loi.append(f"{ten}:{dong} — chú thích ghi {ghi_gio} nhưng cron '{cron}' "
                       f"là {' · '.join(that)} giờ VN")
    return loi


def _lich_that_theo_file():
    d = {}
    for ten, cron, _ghi, _dong in doc_cron_workflow():
        g = _gio_vn(cron)
        d.setdefault(ten, []).extend(g or [cron])
    return d


def bang_lich() -> str:
    """Bảng lịch sinh TỪ cron thật + phần local khai tay."""
    r = ["| Workflow CI | cron (UTC) | Giờ VN |", "|---|---|---|"]
    for ten, cron, _ghi, _dong in doc_cron_workflow():
        g = _gio_vn(cron)
        r.append(f"| `{ten}` | `{cron}` | {' · '.join(g) if g else '(không cố định)'} |")
    r += ["", "| Task LOCAL (khai tay — xem docstring `kiem_lich.py`) | cron | Giờ VN | Trạng thái | Việc |",
          "|---|---|---|---|---|"]
    for tid, cron, gio, bat, viec in LOCAL_KHAI_TAY:
        j = JITTER_GIAY.get(tid)
        them = f" (jitter ~{j}s ⇒ fire ~{gio.split(' · ')[0][:3]}"\
               f"{int(gio.split(' · ')[0][3:]) + round(j / 60):02d})" if j else ""
        r.append(f"| `{tid}` | `{cron}` | {gio}{them} | {bat} | {viec} |")
    return "\n".join(r)


def do_b_bang_khop():
    """B — bảng trong docs/LICH.md phải khớp bảng sinh từ cron thật."""
    if not LICH_MD.exists():
        return [f"{LICH_MD.name} KHÔNG TỒN TẠI — chạy `--sinh`"]
    t = LICH_MD.read_text(encoding="utf-8")
    if BEGIN not in t or END not in t:
        return [f"{LICH_MD.name} thiếu marker LICH:BEGIN/END — chạy `--sinh`"]
    trong = t.split(BEGIN, 1)[1].split(END, 1)[0].strip()
    if trong != bang_lich().strip():
        return [f"{LICH_MD.name} LỆCH so với cron thật — chạy `--sinh` rồi commit"]
    return []


# C — chú thích nhắc mốc của workflow KHÁC bằng tên viết tắt. Chỉ những cụm ĐO ĐƯỢC:
# "CI <HH:MM>" / "vét CI <HH:MM>" phải là một mốc thật của claude-web-scan.yml.
NHAC_CI = re.compile(r"(?:vét\s+)?CI\s+(\d{1,2}):(\d{2})")


def do_c_nhac_moc_khac():
    loi = []
    that = set(_lich_that_theo_file().get("claude-web-scan.yml", []))
    if not that:
        return ["không đọc được mốc nào của claude-web-scan.yml"]
    for ten, _cron, ghi, dong in doc_cron_workflow():
        for m in NHAC_CI.finditer(ghi):
            g = f"{int(m.group(1)):02d}:{m.group(2)}"
            if g not in that:
                loi.append(f"{ten}:{dong} — nhắc 'CI {g}' nhưng claude-web-scan.yml chạy "
                           f"{' · '.join(sorted(that))}")
    return loi


PHEP_DO = [("A · chú thích giờ VN khớp cron cùng dòng", do_a_chu_thich_khop_cron),
           ("B · bảng docs/LICH.md khớp cron thật", do_b_bang_khop),
           ("C · chú thích nhắc mốc CI bằng số còn sống", do_c_nhac_moc_khac)]


def kiem() -> int:
    print("CỔNG LỊCH — giờ trong tài liệu phải khớp cron thật")
    print("─" * 78)
    tong = 0
    for ten, f in PHEP_DO:
        loi = f()
        print(f"  {'✓' if not loi else '✗'} {ten}")
        for l in loi:
            print(f"        │ {l}")
        tong += len(loi)
    print("─" * 78)
    if tong:
        print(f"✗ {tong} chỗ LỆCH — sửa rồi chạy lại. Lịch chép ra nhiều chỗ mà không ai "
              f"canh thì phiên sau tính biên thời gian theo mốc đã chết.")
        return 1
    print("✓ mọi chỗ khớp cron thật.")
    return 0


def sinh() -> int:
    moi = f"{BEGIN}\n{bang_lich()}\n{END}"
    if LICH_MD.exists() and BEGIN in (t := LICH_MD.read_text(encoding="utf-8")):
        ra = t.split(BEGIN, 1)[0] + moi + t.split(END, 1)[1]
    else:
        ra = (LICH_MD.read_text(encoding="utf-8") + "\n\n" if LICH_MD.exists() else "") + moi + "\n"
    LICH_MD.parent.mkdir(parents=True, exist_ok=True)
    LICH_MD.write_text(ra, encoding="utf-8")
    try:
        ten = LICH_MD.relative_to(ROOT)
    except ValueError:              # --tu-kiem ghim LICH_MD vào thư mục tạm ngoài repo
        ten = LICH_MD
    print(f"đã sinh bảng lịch vào {ten}")
    return 0


# ────────────────────────────── tự kiểm ──────────────────────────────
# Mỗi bản hỏng là một file yml/md HỎNG dựng trong thư mục tạm, KHÔNG sửa file thật.
def tu_kiem() -> int:
    import shutil
    import tempfile
    print("TỰ KIỂM — dựng lịch LỆCH rồi đòi đúng phép đo phải kêu")
    print("─" * 78)
    goc_wf, goc_md = WF_DIR, LICH_MD
    ca = [
        ("chú thích lệch cron (sửa cron mà quên sửa chú thích)",
         "wf", "- cron: '47 13 * * *'   # 21:00 VN — bản tin TỐI", "A"),
        ("chú thích nhắc mốc CI đã chết",
         "wf", "- cron: '45 15 * * *'   # 22:45 VN — sau lớp vét TỐI (CI 21:00)", "C"),
        ("bảng LICH.md không khớp cron",
         "md", "| `claude-web-scan.yml` | `47 13 * * *` | 09:99 |", "B"),
    ]
    hong = 0
    for mo_ta, loai, noi_dung, can_keu in ca:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="kiemlich-"))
        try:
            wf = tmp / "workflows"
            wf.mkdir()
            # nền hợp lệ: một mốc web-scan thật + bảng khớp
            (wf / "claude-web-scan.yml").write_text(
                "on:\n  schedule:\n    - cron: '47 13 * * *'   # 20:47 VN — TOI\n",
                encoding="utf-8")
            globals()["WF_DIR"] = wf
            globals()["LICH_MD"] = tmp / "LICH.md"
            if loai == "wf":
                (wf / "hong.yml").write_text(f"on:\n  schedule:\n    {noi_dung}\n",
                                             encoding="utf-8")
            io_im(sinh)             # dựng bảng LICH.md khớp nền hợp lệ
            if loai == "md":
                t = globals()["LICH_MD"].read_text(encoding="utf-8")
                moi = t.replace("| `claude-web-scan.yml` | `47 13 * * *` | 20:47 |", noi_dung)
                if moi == t:
                    print("        │ KHÔNG áp được phép thay vào bảng — neo lại chuỗi")
                globals()["LICH_MD"].write_text(moi, encoding="utf-8")
            keu = {ten[0]: bool(f()) for ten, f in PHEP_DO}
            thieu = [] if keu.get(can_keu) else [f"phép đo {can_keu} KHÔNG kêu"]
            # đối chứng: các phép đo khác không được kêu oan
            oan = [k for k, v in keu.items() if v and k != can_keu]
            if oan:
                thieu.append(f"phép đo {','.join(oan)} kêu OAN")
            print(f"  {'✓' if not thieu else '✗'} {mo_ta} → chờ {can_keu} kêu")
            for x in thieu:
                print(f"        │ {x}")
            if thieu:
                hong += 1
        finally:
            globals()["WF_DIR"], globals()["LICH_MD"] = goc_wf, goc_md
            shutil.rmtree(tmp, ignore_errors=True)
    print("─" * 78)
    if hong:
        print(f"✗ {hong}/{len(ca)} ca KHÔNG bị bắt — cổng chưa có răng.")
        return 1
    print(f"✓ {len(ca)}/{len(ca)} ca đều bị bắt — cổng có răng thật.")
    return 0


def io_im(f):
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        f()
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kiem", action="store_true")
    ap.add_argument("--sinh", action="store_true")
    ap.add_argument("--tu-kiem", action="store_true")
    a = ap.parse_args()
    if a.tu_kiem:
        return tu_kiem()
    if a.sinh:
        return sinh()
    if a.kiem:
        return kiem()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

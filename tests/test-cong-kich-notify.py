#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cổng "chỉ phiên TỰ NẠP mới được kích notify" — hồi quy sự cố HAI BẢN TIN tối 31/07/2026.

Sự cố: Huy nhận hai file .docx y hệt nhau lúc 21:24 ("9 tin mới") và 21:26 ("không có tin mới
so với bản trước"). Nguyên nhân: bước kích của `claude-web-scan.yml` hỏi
`git log <base.sha>..HEAD | grep '^Cap nhat ban tin'` SAU KHI `git pull --rebase`, nên một run
**đã SKIP, không quét gì** vẫn thấy commit bản tin của phiên khác (kéo về lúc rebase) và kích
`notify-email.yml` lần thứ hai.

Cổng nay là CỜ TƯỜNG MINH: `state.py done <pipeline>` ghi cờ vào thư mục tạm của chính job đó;
`.github/scripts/quyet_dinh_kich.py` đọc cờ. Phiên SKIP không gọi `done` nên không có cờ.

    python3 tests/test-cong-kich-notify.py            # chạy bộ ca
    python3 tests/test-cong-kich-notify.py --tu-kiem  # chứng minh bộ ca BẮT ĐƯỢC lỗi

Ca đọc CHÍNH file yml (ca 06-07) để bảo đảm cổng còn nằm trên đường đi — cùng nếp với
tests/test-cong-phien-test.py: cổng đúng mà workflow không gọi tới thì vô nghĩa.
"""
import contextlib
import hashlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
YML = REPO / ".github" / "workflows" / "claude-web-scan.yml"
STATE_THAT = REPO / "scripts" / "state.py"
KICH_THAT = REPO / ".github" / "scripts" / "quyet_dinh_kich.py"

# Seam cho --tu-kiem: trỏ sang bản state.py / yml ĐÃ GỠ dòng bảo vệ.
STATE_MOD = Path(os.environ.get("KICHNOTIFY_STATE_MOD") or STATE_THAT)
YML_MOD = Path(os.environ.get("KICHNOTIFY_YML_MOD") or YML)


def _nap(duong_dan: Path, ten: str):
    spec = importlib.util.spec_from_file_location(ten, duong_dan)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ten] = mod
    spec.loader.exec_module(mod)
    return mod


def _quyet_dinh(co_dir: Path) -> dict:
    """Chạy quyet_dinh_kich.py bằng subprocess với thư mục cờ riêng.

    Ở ĐÂY subprocess là ĐÚNG: bản hỏng của bộ này là `state.py`, mà `quyet_dinh_kich.py` tự
    `import state` từ repo — nên phải truyền đường dẫn bản hỏng qua PYTHONPATH, không phải
    tráo module trong tiến trình.
    """
    env = dict(os.environ)
    env["DIEMTIN_CO_DIR"] = str(co_dir)
    if STATE_MOD != STATE_THAT:  # ép quyet_dinh_kich import ĐÚNG bản state đang thử
        env["PYTHONPATH"] = str(STATE_MOD.parent) + os.pathsep + env.get("PYTHONPATH", "")
    r = subprocess.run(
        [sys.executable, str(KICH_THAT)], capture_output=True, text=True, env=env
    )
    ra = dict(d.split("=", 1) for d in r.stdout.splitlines() if "=" in d)
    ra["_ma"] = str(r.returncode)
    return ra


def _state_chay(co_dir: Path, logs: Path, *dau_vao) -> int:
    """Gọi state.py (bản đang thử) như routine vẫn gọi."""
    env = dict(os.environ)
    env["DIEMTIN_CO_DIR"] = str(co_dir)
    env["STATE_LOGS_DIR"] = str(logs)
    r = subprocess.run(
        [sys.executable, str(STATE_MOD), *dau_vao], capture_output=True, text=True, env=env
    )
    return r.returncode


def chay():
    ca = []
    yml = YML_MOD.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as td:
        goc = Path(td)
        co_dir = goc / "co"
        co_dir.mkdir()
        logs = goc / "logs"
        logs.mkdir()

        # [01] PHẢI CHẶN — hồi quy 31/07: run vét `claim` trả exit 10 rồi SKIP, không gọi
        #      `done`. Dù cây git của nó đã có commit bản tin của phiên khác, cổng phải im.
        ra = _quyet_dinh(co_dir)
        ca.append(("[01] phien chua `done` -> KHONG kich ban tin", ra.get("ban_tin") == "0"))

        # [02] PHẢI CHẶN — `skip` là lời khai "tôi không nạp gì", tuyệt đối không ghi cờ.
        _state_chay(co_dir, logs, "skip", "web-scan", "lo rong")
        ra = _quyet_dinh(co_dir)
        ca.append(("[02] sau `state.py skip` -> VAN khong kich", ra.get("ban_tin") == "0"))

        # [03] PHẢI CHẶN — `fail` cũng vậy.
        _state_chay(co_dir, logs, "fail", "web-scan", "loi mang")
        ra = _quyet_dinh(co_dir)
        ca.append(("[03] sau `state.py fail` -> VAN khong kich", ra.get("ban_tin") == "0"))

        # [04] chống chặn oan — phiên quét thật `done` thì PHẢI kích, không thì mất bản tin.
        _state_chay(co_dir, logs, "done", "web-scan", "+9 tin")
        ra = _quyet_dinh(co_dir)
        ca.append(("[04] sau `state.py done web-scan` -> KICH ban tin", ra.get("ban_tin") == "1"))

        # [05] hai pipeline độc lập — cờ bản tin không được kéo theo email sự kiện (🎖️ khác 📰).
        ca.append(("[05] `done web-scan` KHONG keo theo su kien", ra.get("su_kien") == "0"))

        # [06] chống chặn oan phía sự kiện.
        _state_chay(co_dir, logs, "done", "event-scan", "+6 bai")
        ra = _quyet_dinh(co_dir)
        ca.append(("[06] sau `done event-scan` -> KICH su kien", ra.get("su_kien") == "1"))

    # ── Cổng có còn nằm trên ĐƯỜNG ĐI không (đọc chính file yml) ──
    # [07] workflow phải GỌI script quyết định.
    ca.append(
        ("[07] yml goi quyet_dinh_kich.py", "quyet_dinh_kich.py" in yml)
    )
    # [08] PHẢI CHẶN chiều lùi — không được quay lại dò `git log … | grep 'Cap nhat ban tin'`,
    #      đó chính là phép đo đã gây gửi hai lần.
    dong_git_log = [
        d for d in yml.splitlines()
        if "git log" in d and "--format=%s" in d and not d.strip().startswith("#")
    ]
    ca.append(("[08] yml KHONG con do bang `git log --format=%s`", not dong_git_log))
    # [09] và không còn nhánh nào quyết định bằng biến new_msgs.
    dung_new_msgs = [
        d for d in yml.splitlines()
        if "new_msgs" in d and not d.strip().startswith("#")
    ]
    ca.append(("[09] yml KHONG con dung bien new_msgs", not dung_new_msgs))

    # [10] script quyết định tự chứng minh được bộ ca của nó.
    r = subprocess.run(
        [sys.executable, str(KICH_THAT), "--tu-kiem"], capture_output=True, text=True
    )
    ca.append(("[10] quyet_dinh_kich.py --tu-kiem dat", r.returncode == 0))

    return ca


BAN_HONG = [
    (
        "go loi goi ghi_co_da_nap trong record() (hanh vi TRUOC ban va)",
        "state",
        "        ghi_co_da_nap(pipeline)\n    state[pipeline] = entry",
        "    state[pipeline] = entry",
        [4, 6],
    ),
    (
        "ghi co cho MOI status, khong rieng DONE",
        "state",
        "    if status == \"RUNNING\":\n        entry[\"heartbeat\"] = now_iso()",
        "    ghi_co_da_nap(pipeline)\n    if status == \"RUNNING\":\n        entry[\"heartbeat\"] = now_iso()",
        [2, 3],
    ),
    (
        "yml quay lai do bang `git log --format=%s` (hanh vi cu)",
        "yml",
        "          python3 .github/scripts/quyet_dinh_kich.py > /tmp/quyet-dinh-kich.env",
        "          new_msgs=$(git log HEAD~1..HEAD --format=%s)\n          python3 .github/scripts/quyet_dinh_kich.py > /tmp/quyet-dinh-kich.env",
        [8, 9],
    ),
]


def tu_kiem() -> int:
    goc_state = STATE_THAT.read_text(encoding="utf-8")
    goc_yml = YML.read_text(encoding="utf-8")
    tong_hong = 0

    for ten, loai, tim, thay, phai_do in BAN_HONG:
        goc = goc_state if loai == "state" else goc_yml
        if goc.count(tim) != 1:
            print(f"  ✗ {ten} — chuoi neo khop {goc.count(tim)} cho (phai dung 1)")
            tong_hong += 1
            continue
        noi_dung = goc.replace(tim, thay)
        # Tên bản hỏng mang PID + sha1 NỘI DUNG: hai bản hỏng liên tiếp cùng tên trong cùng
        # một giây có thể dính lại .pyc cũ khi nạp bằng importlib (luật mục 17 toàn cục).
        vet = f"{os.getpid()}-{hashlib.sha1(noi_dung.encode()).hexdigest()[:8]}"
        if loai == "state":
            # Bản hỏng phải nằm TRONG thư mục thật: state.py không import gì của repo, nhưng
            # quyet_dinh_kich.py `import state` nên bản hỏng phải mang đúng TÊN MODULE `state`.
            thu_muc = REPO / "scripts" / f"_thu-hong-{vet}"
            thu_muc.mkdir(exist_ok=True)
            ban_hong = thu_muc / "state.py"
            env_key = "KICHNOTIFY_STATE_MOD"
        else:
            ban_hong = YML.parent / f"_thu-hong-{vet}-claude-web-scan.yml"
            env_key = "KICHNOTIFY_YML_MOD"
        ban_hong.write_text(noi_dung, encoding="utf-8")
        try:
            env = dict(os.environ)
            env[env_key] = str(ban_hong)
            r = subprocess.run(
                [sys.executable, str(Path(__file__).resolve())],
                capture_output=True, text=True, env=env,
            )
            do = sorted(
                int(d.split("]")[0].split("[")[1])
                for d in r.stdout.splitlines() if d.strip().startswith("✗ [")
            )
            if do == sorted(phai_do):
                print(f"  ✓ {ten} — ca do dung nhu khai: {do}")
            else:
                print(f"  ✗ {ten} — khai {sorted(phai_do)} nhung do thuc te {do}")
                tong_hong += 1
            if len(do) == 10:
                print("    ⚠️ MOI ca deu do -> phep thay pha hong nen, khong chung minh duoc gi")
                tong_hong += 1
        finally:
            ban_hong.unlink(missing_ok=True)
            if loai == "state":
                for rac in ban_hong.parent.glob("__pycache__/*"):
                    rac.unlink(missing_ok=True)
                (ban_hong.parent / "__pycache__").rmdir() if (ban_hong.parent / "__pycache__").exists() else None
                ban_hong.parent.rmdir()

    print(f"\n--tu-kiem: {len(BAN_HONG) - tong_hong}/{len(BAN_HONG)} ban hong bi bat")
    return 1 if tong_hong else 0


def main() -> int:
    if "--tu-kiem" in sys.argv:
        return tu_kiem()
    ca = chay()
    for ten, ok in ca:
        print(("✓ " if ok else "✗ ") + ten)
    do = [t for t, ok in ca if not ok]
    if do:
        print(f"\nTRUOT {len(do)}/{len(ca)} ca")
        return 1
    print(f"\nDAT {len(ca)}/{len(ca)} ca")
    return 0


if __name__ == "__main__":
    sys.exit(main())

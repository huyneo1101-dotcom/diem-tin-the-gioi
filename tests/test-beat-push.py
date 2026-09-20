#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST CỔNG "NHỊP TIM PHẢI ĐẨY NGAY LÊN REMOTE" (`scripts/beat_push.py`).

⚠ VÌ SAO CÓ FILE NÀY — sự cố THẬT sáng 19/09/2026 (xem `logs/scan-2026-09-19.log`
dòng `[21:45Z]` và bàn giao trong `HeThong/SO-VIEC-CHO-NGOAI-GIO.md`):
CI claim khoá `web-scan` lúc 04:00 giờ VN, tự nhịp tim (`state.py beat web-scan`) CỤC BỘ
lúc 04:31 và 04:41 nhưng KHÔNG đẩy lên git — commit đẩy gần nhất chỉ dừng ở checkpoint
baseline 04:04. Máy Mac chạy mốc vét 04:36 chỉ đọc được nhịp tim 04:04 qua git, tính ra
32 phút > `LOCK_STALE_MIN` (30'), kết luận CI đã chết rồi GIÀNH KHOÁ trong khi CI vẫn
sống — hai phiên quét chồng, phí ~12 triệu token quy đổi. May CI push bản tin thật xong
trước (04:45) nên không mất tin, nhưng đúng kiểu lỗi "may mắn mới không mất" mà mục 17
CLAUDE.md coi là CHƯA vá.

`scripts/state.py beat <pipeline>` chỉ ghi *state cục bộ* trong container CI — PUSH lên
remote là một lệnh `git` RIÊNG mà prompt CI tự gọi ở chỗ khác. Bản vá `beat_push.py` gộp
cứng hai việc thành MỘT lệnh (tái dùng `ghi_so_push.day_len_remote`, cùng cơ chế
đọc-sửa-ghi-trên-đỉnh-remote đã dùng cho `logs/da-gui-email.json` và log ngày) — "beat mà
quên push" không còn là lỗi có thể mắc.

Đây đúng loại hỏng CÂM của mục 17 CLAUDE.md: `state.py beat` báo "nhip tim @ ..." y hệt dù
có đẩy lên remote hay không — không lỗi nào, không cảnh báo nào, chỉ có máy khác đọc nhầm
heartbeat cũ. Vì vậy ca chính ở đây là ca PHẢI CHẶN đúng sự cố: gọi `beat_push.py` rồi
khẳng định REMOTE (không phải bản cục bộ) thấy nhịp tim mới.

Bộ test dựng repo git THẬT (remote bare + 2 clone = "CI" và "máy khác") rồi đo hành vi
thật, cùng lối với `tests/test-ghi-log-push.py`.

Chạy:
    python3 tests/test-beat-push.py
    python3 tests/test-beat-push.py --tu-kiem   # chứng minh test này BẮT ĐƯỢC lỗi
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
BEATPUSH_THAT = ROOT / "scripts" / "beat_push.py"
STATE_THAT = ROOT / "scripts" / "state.py"
GSP_THAT = ROOT / ".github" / "scripts" / "ghi_so_push.py"
STATE_REL = "logs/state.json"


def _git(d, *a, kiem=True):
    r = subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True)
    if kiem and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)}: {(r.stderr or r.stdout)[:300]}")
    return r


def _dung_san(t, ma_beat_push=None):
    """remote bare + 2 clone (A = "CI", B = "máy khác"). Mỗi clone mang cây scripts/
    thật (trừ `beat_push.py` — tráo được bằng `ma_beat_push` cho --tu-kiem)."""
    t = pathlib.Path(t)
    bare = t / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)

    goc = t / "goc"
    goc.mkdir()
    _git(goc, "init", "-q")
    _git(goc, "config", "user.email", "t@t")
    _git(goc, "config", "user.name", "t")
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
        shutil.copy2(STATE_THAT, d / "scripts" / "state.py")
        shutil.copy2(GSP_THAT, d / ".github" / "scripts" / "ghi_so_push.py")
        noi = ma_beat_push if ma_beat_push is not None else BEATPUSH_THAT.read_text(encoding="utf-8")
        (d / "scripts" / "beat_push.py").write_text(noi, encoding="utf-8")
        clones.append(d)
    return bare, clones[0], clones[1]


def _claim(d, pipeline, gio="04:00"):
    env = dict(os.environ, STATE_GIO_GIA=gio)
    env.pop("DIEMTIN_PHIEN_TEST", None)
    r = subprocess.run([sys.executable, str(pathlib.Path(d) / "scripts" / "state.py"),
                        "claim", pipeline], cwd=str(d), capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _state_cmd(d, *args, gio="04:00"):
    env = dict(os.environ, STATE_GIO_GIA=gio)
    env.pop("DIEMTIN_PHIEN_TEST", None)
    r = subprocess.run([sys.executable, str(pathlib.Path(d) / "scripts" / "state.py"), *args],
                       cwd=str(d), capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _beat_push(d, pipeline):
    r = subprocess.run([sys.executable, str(pathlib.Path(d) / "scripts" / "beat_push.py"), pipeline],
                       cwd=str(d), capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _beat_tran(d, pipeline):
    """`state.py beat` TRẦN — hành vi CŨ trước bản vá (ghi cục bộ, không đẩy)."""
    return _state_cmd(d, "beat", pipeline)


def _commit_push_state(d, msg="log khoa"):
    _git(d, "add", "logs/")
    if _git(d, "diff", "--cached", "--quiet", kiem=False).returncode == 0:
        return  # không đổi gì, khỏi commit rỗng
    _git(d, "commit", "-q", "-m", msg)
    _git(d, "push", "-q", "origin", "HEAD:main")


def _state_tren_remote(bare, t):
    """Đọc `logs/state.json` mới nhất trên remote qua một clone soi riêng."""
    xem = pathlib.Path(t) / f"xem-{os.urandom(3).hex()}"
    subprocess.run(["git", "clone", "-q", str(bare), str(xem)], check=True)
    p = xem / STATE_REL
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _pull(d):
    _git(d, "fetch", "-q", "origin", "main")
    _git(d, "reset", "-q", "--hard", "FETCH_HEAD")


# ═══════════════════════════════════ các ca ═══════════════════════════════════
def ca_01_chinh_hoi_quy(ma=None):
    """CA CHÍNH · hồi quy 19/09/2026: beat_push phải khiến REMOTE thấy nhịp tim MỚI."""
    with tempfile.TemporaryDirectory() as t:
        bare, A, B = _dung_san(t, ma)
        rc, out = _claim(A, "web-scan")
        if rc != 0:
            return False, f"claim hỏng (rc={rc})\n{out}"
        _commit_push_state(A, "log: claim web-scan")
        truoc = _state_tren_remote(bare, t).get("web-scan", {})
        if truoc.get("lastStatus") != "RUNNING":
            return False, f"remote chưa thấy claim: {truoc}"
        hb_cu = truoc.get("heartbeat")

        time.sleep(1.2)  # đảm bảo now_iso() ra chuỗi khác — độ phân giải là GIÂY
        rc, out = _beat_push(A, "web-scan")
        if rc != 0:
            return False, f"beat_push hỏng (rc={rc})\n{out}"

        sau = _state_tren_remote(bare, t).get("web-scan", {})
        if sau.get("lastStatus") != "RUNNING":
            return False, f"beat_push làm mất trạng thái RUNNING: {sau}"
        if sau.get("heartbeat") == hb_cu:
            return False, (f"REMOTE VẪN THẤY NHỊP TIM CŨ ({hb_cu}) — đúng sự cố 19/09: "
                            f"beat chỉ ghi cục bộ, không tới remote")
        return True, f"remote cập nhật {hb_cu} → {sau.get('heartbeat')}"


def ca_02_doi_chung_beat_tran_khong_toi_remote(ma=None):
    """ĐỐI CHỨNG · `state.py beat` TRẦN (hành vi CŨ) KHÔNG được cập nhật remote —
    chứng minh vì sao phải thay bằng `beat_push.py`, không phải beat_push.py thừa."""
    with tempfile.TemporaryDirectory() as t:
        bare, A, B = _dung_san(t, ma)
        _claim(A, "web-scan")
        _commit_push_state(A, "log: claim web-scan")
        truoc = _state_tren_remote(bare, t).get("web-scan", {})

        time.sleep(1.2)
        rc, _ = _beat_tran(A, "web-scan")
        if rc != 0:
            return False, "state.py beat trần lỗi bất thường"
        sau = _state_tren_remote(bare, t).get("web-scan", {})
        if sau.get("heartbeat") != truoc.get("heartbeat"):
            return False, ("remote lại đổi dù chỉ gọi `beat` trần không push — ca đối "
                            "chứng sai giả định, cần soát lại kịch bản")
        return True, "đúng như dự đoán: beat trần không chạm tới remote"


def ca_03_phai_chan_khong_hoi_sinh_khoa_da_nha(ma=None):
    """PHẢI CHẶN · pipeline đã DONE ở phiên khác rồi thì beat_push KHÔNG được hồi sinh
    heartbeat/RUNNING — tránh một phiên cũ tưởng mình còn giữ khoá."""
    with tempfile.TemporaryDirectory() as t:
        bare, A, B = _dung_san(t, ma)
        _claim(A, "web-scan")
        _commit_push_state(A, "log: claim web-scan")

        _pull(B)
        rc, _ = _state_cmd(B, "done", "web-scan", "xong o phien khac")
        if rc != 0:
            return False, "B không ghi được done"
        _commit_push_state(B, "log: done web-scan (B)")

        # A không biết B đã DONE (A chưa pull) — vẫn gọi beat_push như thường lệ.
        rc, out = _beat_push(A, "web-scan")
        if rc != 0:
            return False, f"beat_push lỗi khi pipeline đã DONE (rc={rc})\n{out}"
        sau = _state_tren_remote(bare, t).get("web-scan", {})
        if sau.get("lastStatus") != "DONE":
            return False, f"beat_push đã HỒI SINH khoá đã nhả: {sau}"
        if "heartbeat" in sau:
            return False, f"beat_push gắn lại heartbeat cho pipeline đã DONE: {sau}"
        return True, "giữ nguyên DONE, không hồi sinh khoá"


def ca_04_doi_chung_giu_pipeline_khac(ma=None):
    """ĐỐI CHỨNG · beat_push của web-scan KHÔNG được xoá mất entry event-scan của
    pipeline khác đang nằm trên cùng file `state.json`."""
    with tempfile.TemporaryDirectory() as t:
        bare, A, B = _dung_san(t, ma)
        _claim(A, "web-scan")
        _commit_push_state(A, "log: claim web-scan")

        _pull(B)
        _claim(B, "event-scan")
        _commit_push_state(B, "log: claim event-scan")

        rc, out = _beat_push(A, "web-scan")
        if rc != 0:
            return False, f"beat_push hỏng (rc={rc})\n{out}"
        sau = _state_tren_remote(bare, t)
        if sau.get("event-scan", {}).get("lastStatus") != "RUNNING":
            return False, f"beat_push của web-scan đã LÀM MẤT entry event-scan: {sau}"
        if sau.get("web-scan", {}).get("lastStatus") != "RUNNING":
            return False, f"web-scan tự nhiên biến mất: {sau}"
        return True, "cả hai pipeline còn nguyên trên remote"


def ca_05_phai_keu_pipeline_sai(ma=None):
    """PHẢI KÊU · tên pipeline không hợp lệ → mã ≠ 0, không im lặng chạy bậy."""
    with tempfile.TemporaryDirectory() as t:
        _, A, _ = _dung_san(t, ma)
        rc, out = _beat_push(A, "khong-ton-tai")
        if rc == 0:
            return False, f"trả 0 cho tên pipeline sai\n{out}"
        return True, f"rc={rc}"


def ca_06_doi_chung_chua_tung_claim(ma=None):
    """ĐỐI CHỨNG · pipeline chưa từng claim (không có entry) → beat_push là NO-OP an
    toàn, không tự bịa ra một khoá RUNNING từ hư không."""
    with tempfile.TemporaryDirectory() as t:
        bare, A, _ = _dung_san(t, ma)
        rc, out = _beat_push(A, "web-scan")
        if rc != 0:
            return False, f"beat_push lỗi khi chưa từng claim (rc={rc})\n{out}"
        sau = _state_tren_remote(bare, t)
        if sau.get("web-scan", {}).get("lastStatus") == "RUNNING":
            return False, f"tự bịa ra khoá RUNNING từ hư không: {sau}"
        return True, "no-op an toàn"


CAC_CA = [
    ("[01] CA CHÍNH · hồi quy 19/09 — beat_push phải tới được remote", ca_01_chinh_hoi_quy),
    ("[02] ĐỐI CHỨNG · beat trần (cũ) không tới remote", ca_02_doi_chung_beat_tran_khong_toi_remote),
    ("[03] PHẢI CHẶN · không hồi sinh khoá đã DONE ở phiên khác", ca_03_phai_chan_khong_hoi_sinh_khoa_da_nha),
    ("[04] ĐỐI CHỨNG · không xoá mất pipeline khác trên cùng file", ca_04_doi_chung_giu_pipeline_khac),
    ("[05] PHẢI KÊU · tên pipeline sai → mã lỗi ≠ 0", ca_05_phai_keu_pipeline_sai),
    ("[06] ĐỐI CHỨNG · chưa từng claim thì no-op, không bịa khoá", ca_06_doi_chung_chua_tung_claim),
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


# ═══════════════════════ tự kiểm: bản hỏng ═══════════════════════
BAN_HONG = [
    ("beat_push: BẺ LẠI đúng sự cố 19/09 — beat ghi cục bộ nhưng KHÔNG push",
     "    return gsp.day_len_remote(STATE_REL, hop_nhat_heartbeat(pipeline),\n"
     "                              f\"beat: {pipeline} {st.now_iso()}\", **kw)",
     "    hop_nhat_heartbeat(pipeline)(ROOT / STATE_REL)\n    return 0",
     ["[01] CA CHÍNH · hồi quy 19/09 — beat_push phải tới được remote"]),

    ("beat_push: gỡ chốt lastStatus=='RUNNING' — hồi sinh khoá đã nhả",
     "        if entry.get(\"lastStatus\") != \"RUNNING\":\n"
     "            # Pipeline đã DONE/SKIP/FAIL (ở phiên khác, hoặc chính mình) — khoá đã nhả,\n"
     "            # đừng hồi sinh nhịp tim cho một phiên không còn giữ khoá.\n"
     "            return",
     "        if False:\n            return",
     ["[03] PHẢI CHẶN · không hồi sinh khoá đã DONE ở phiên khác"]),

    ("beat_push: ghi ĐÈ CẢ FILE thay vì chỉ field của pipeline mình — mất pipeline khác",
     "        data[pipeline] = entry\n"
     "        p.parent.mkdir(parents=True, exist_ok=True)\n"
     "        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + \"\\n\", encoding=\"utf-8\")",
     "        data = {pipeline: entry}\n"
     "        p.parent.mkdir(parents=True, exist_ok=True)\n"
     "        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + \"\\n\", encoding=\"utf-8\")",
     ["[04] ĐỐI CHỨNG · không xoá mất pipeline khác trên cùng file"]),
]


def tu_kiem():
    goc = BEATPUSH_THAT.read_text(encoding="utf-8")
    print("Bản ĐÚNG:")
    do = chay()
    if do:
        print(f"\n✗ bản đúng đã có {len(do)} ca không đạt — sửa trước khi tự kiểm")
        return 1

    print("\nBản HỎNG (mỗi bản gỡ đúng một lớp vá):")
    hong = 0
    for ten, tim, thay, phai_do in BAN_HONG:
        if goc.count(tim) != 1:
            print(f"  ✗ {ten} — chuỗi neo khớp {goc.count(tim)} chỗ (phải đúng 1, mã nguồn "
                  f"đã đổi, sửa lại test)")
            hong += 1
            continue
        ma = goc.replace(tim, thay)
        do_hong = chay(ma, im=True)
        thieu = [c for c in phai_do if c not in do_hong]
        if thieu:
            print(f"  ✗ {ten} — VẪN XANH: {thieu}\n      (đỏ thực tế: {do_hong})")
            hong += 1
        else:
            print(f"  ✓ {ten} — bắt được ({len(do_hong)} ca đỏ)")
    if hong:
        print(f"\n✗ TỰ KIỂM TRƯỢT: {hong}/{len(BAN_HONG)} bản hỏng không bị bắt")
        return 1
    print(f"\n✅ TỰ KIỂM ĐẠT: {len(BAN_HONG)}/{len(BAN_HONG)} bản hỏng đều bị bắt")
    return 0


def main(argv):
    if "--tu-kiem" in argv:
        return tu_kiem()
    print(f"TEST NHỊP TIM PHẢI ĐẨY NGAY LÊN REMOTE — {len(CAC_CA)} ca")
    print("─" * 78)
    do = chay()
    if do:
        print(f"\n✗ {len(do)}/{len(CAC_CA)} ca KHÔNG ĐẠT")
        return 1
    print(f"\n✅ {len(CAC_CA)}/{len(CAC_CA)} ca đạt")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Cờ trạng thái riêng cho từng pipeline — logs/state.json.

VÌ SAO CÓ FILE NÀY: trước đây cả 2 pipeline dùng chung `DATA.generatedAt` làm cờ
idempotent. Action nhập tin từ Drive chạy 08:00 bump generatedAt = hôm nay → routine
quét 6-agent buổi tối thấy "đã xong hôm nay" và SKIP vĩnh viễn (xNews kẹt 3 ngày,
tập trận/sự kiện ngoại giao không ai cập nhật). `generatedAt` là NGÀY BẢN TIN hiển thị
trên web — không phải cờ chạy việc. Tách ra đây, mỗi pipeline một dòng riêng.

Pipeline đang dùng:
  drive-import  — GitHub Action import-news-from-drive.yml (08:00 & 20:00 VN) — THẬT SỰ 2 buổi/ngày
  web-scan      — routine Claude quét bản tin 5 chủ đề — 2 phiên/ngày: TỐI (CI 21:00 · local 21:15 ·
                  vét CI 22:00) và SÁNG SỚM (CI 04:00 · local 04:30 · CI 05:00 · local 05:30)
  event-scan    — sự kiện/tập trận + think-tank + báo cáo tuần CN — 1 phiên/ngày, buổi SÁNG. Từ
                  28/07/2026 KHÔNG còn mốc riêng (cũ: 08:45, dự phòng 09:45): nó chạy NGAY SAU bản
                  tin trong CÙNG session của phiên sáng sớm, chỉ khoá/commit là vẫn tách riêng

CỜ TÁCH THEO BUỔI, không phải theo ngày. Với drive-import (2 buổi/ngày) đây đúng nghĩa "buổi":
nếu chỉ so theo ngày thì lô sáng xong sẽ làm lô tối cùng ngày SKIP oan.

Với web-scan/event-scan (1 phiên/ngày) ô "buổi" còn giá trị KHÁC: nó là lưới chống MẤT PHIÊN khi
máy ngủ. Ví dụ web-scan lẽ ra chạy 22:00 ngày 24 nhưng máy ngủ, mở máy 03:46 ngày 25 mới chạy bù —
lần chạy bù đó rơi vào ô "sang" nên KHÔNG chiếm ô "toi" của ngày 25, và bản tin tối 25 vẫn quét bình
thường. Nếu ép mỗi pipeline một ô cố định thì lần chạy bù sẽ ăn luôn suất của ngày mới → mất 1 bản tin.
Vì vậy giữ nguyên cách suy ô theo giờ VN (trước 14:00 = "sang", từ 14:00 = "toi"), CHỈ đổi NHÃN in ra:
với pipeline 1 phiên/ngày, ô không phải giờ chạy chuẩn của nó được gọi thẳng là "chay bu" (xem
SLOT_LABELS) — trước đây in "web-scan buoi sang" nghe như web có phiên sáng, mà phiên sáng đã bỏ từ 23/07.

PHIÊN TEST KHÔNG ĐƯỢC ĐỤNG CỜ THẬT (thêm 29/07/2026 — vá gốc sự cố tối 29/07). Nhánh
`MODE=test` của `claude-web-scan.yml` (quét nhẹ 1 agent, chứng minh hạ tầng CI) đã gọi
`state.py done web-scan` lúc 17:34 và CHIẾM ô khoá `toi` của cả ngày. Commit của nó rơi
ngoài khung giờ gửi (cổng 2 của notify-email.yml đòi >= 20:30) nên không kích email/Telegram.
Hậu quả: CI 21:00, local 21:15, CI 22:00 đều nhận exit 10 rồi SKIP — bản tin tối suýt mất
trắng mà KHÔNG LỚP NÀO BÁO HỎNG. Cùng bài học đã ghi cho sổ đã gửi: chạy tay/chạy test là
để TEST, không được để dấu vết lên bản thật.

Cơ chế: biến môi trường `DIEMTIN_PHIEN_TEST=1` (workflow đặt ở nhánh test) chuyển TOÀN BỘ
đường ghi sang `logs/state-test.json`. Phiên test vẫn nghiệm thu được trọn pipeline
claim -> beat -> done, chỉ là ghi vào sổ riêng của nó.
  · Ý ĐỊNH PHẢI KHAI BẰNG LỜI, không suy từ kiểu sự kiện — cùng lỗi đã vấp với `tu_dong=1`
    (suy từ `event_name == 'push'`) và `TELEGRAM_BAT_BUOC` (suy từ số secret còn lại).
  · MẶC ĐỊNH LÀ PHIÊN THẬT: quên đặt biến thì hành vi y như cũ, không tạo vùng câm mới.
  · Phiên test KHÔNG xét cờ `lastSuccess` thật -> không bao giờ exit 10 vì bản tin thật đã
    xong (test phải chạy lại được bất kể giờ nào), NHƯNG VẪN đọc `logs/state.json` để nhường
    phiên THẬT đang chạy (exit 11) — bỏ chốt này là mở đường cho hai phiên quét chồng.

KHOÁ CHỐNG CHẠY CHỒNG (thêm 22/07/2026): mốc chính và mốc dự phòng chỉ cách nhau 60 phút
mà một phiên quét mất ~60 phút, nên `check` (chỉ biết ĐÃ XONG hay chưa) sẽ để lần fire dự
phòng khởi động phiên THỨ HAI song song — hai phiên cùng quét, cùng push, tốn token đôi và
đụng nhau lúc rebase. `claim` giành khoá trước khi quét; `done/skip/fail` nhả khoá.
Khoá dùng HEARTBEAT chứ không phải hạn giờ cứng: phiên chết giữa chừng mà khoá không tự
mở thì còn tệ hơn không có khoá (mất luôn bản tin của buổi đó). Không có nhịp nào trong
LOCK_STALE_MIN phút -> coi như phiên đã chết, cho phiên mới giành khoá.

Dùng:
  python3 scripts/state.py claim web-scan       # GIÀNH khoá + kiểm tra; 0 = quét đi, 10 = xong rồi,
                                                #   11 = đang chạy, 12 = SAI GIỜ (ngoài khung ca, xem KHUNG_GIO)
  python3 scripts/state.py beat web-scan        # nhịp tim — gọi ở MỖI checkpoint, nếu không khoá sẽ tự hết hạn
  python3 scripts/state.py check web-scan       # CHỈ hỏi, không giành khoá (dùng để chẩn đoán)
  python3 scripts/state.py show                 # in toàn bộ trạng thái
  python3 scripts/state.py done web-scan "+12 tin"   # xong VÀ có nội dung  -> chặn lần fire sau, nhả khoá
  python3 scripts/state.py skip web-scan "khong co file"  # chạy nhưng không có gì -> nhả khoá, KHÔNG chặn
  python3 scripts/state.py fail web-scan "session limit"  # lỗi -> nhả khoá, KHÔNG chặn, lần sau quét lại
  ... thêm --slot sang|toi để ép buổi (chạy tay ngoài giờ); mặc định tự suy từ giờ VN.
  ... thêm --force cho `claim` để cướp khoá của phiên đang chạy (chỉ khi biết chắc nó đã chết).
  DIEMTIN_PHIEN_TEST=1 python3 scripts/state.py claim web-scan   # phiên TEST: ghi state-test.json

Bộ test canh cổng này: tests/test-cong-phien-test.py (kèm --tu-kiem).
"""
import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

os.environ["TZ"] = "Asia/Ho_Chi_Minh"
try:
    time.tzset()
except AttributeError:  # Windows
    pass

# STATE_LOGS_DIR: seam CHỈ dùng cho bộ test (tests/test-cong-phien-test.py) — ghim thư mục logs
# vào chỗ tạm để ca thử không đụng cờ thật của repo. Vận hành thật KHÔNG đặt biến này.
LOGS_DIR = Path(os.environ.get("STATE_LOGS_DIR") or Path(__file__).resolve().parent.parent / "logs")
STATE_PATH = LOGS_DIR / "state.json"
# Sổ RIÊNG của phiên test — không commit (đã .gitignore), mất cũng không sao.
STATE_TEST_PATH = LOGS_DIR / "state-test.json"
# Khai ý định bằng lời: chỉ biến này mới bật chế độ test. Không suy từ MODE/tên workflow/giờ chạy.
TEST_ENV = "DIEMTIN_PHIEN_TEST"
TEST_ON = ("1", "true", "yes", "on", "co")
PIPELINES = ("drive-import", "web-scan", "event-scan")
SLOTS = ("sang", "toi")
SLOT_SPLIT_HOUR = 14  # < 14:00 VN = ô "sang"; >= 14:00 = ô "toi"

# ── CỔNG KHUNG GIỜ — phiên khởi động sai giờ thì KHÔNG được nhận ô nào ────────────────
# Sự cố thật (Huy kêu sáng 31/08/2026 "sao điểm tin sáng nay vẫn chạy 1h sáng"):
# cron GitHub trễ BẤT ĐỊNH 2-4 tiếng (đo 6 ngày liền: mốc 13:47Z chạy lúc 17:23-18:11Z).
# Mốc CI TỐI 20:47 VN vì thế nổ lúc 00:46 VN hôm sau; `current_slot()` chỉ hỏi đồng hồ
# nên thấy 00:46 < 14:00 và gán ngay ô "sang" -> phiên tối biến thành phiên sáng, quét và
# GỬI bản tin lúc 01:25 sáng, đồng thời chiếm mất ô "sang" khiến mốc sáng thật (local
# 04:30, CI 03:47/04:47) đều SKIP. Ô "toi" hôm đó không còn ai chạy nên bản tin TỐI mất
# hẳn: sổ đã gửi trống dòng [toi] cả 30/08 lẫn 31/08, lần cuối là 29/08 21:30.
# Vá: đồng hồ KHÔNG đủ để nhận ca. Phiên phải rơi vào khung giờ của ca thì mới được claim;
# ngoài khung là SKIP êm (exit 12), nhường lại cho mốc đúng giờ (local `kich_ci.py`).
# Khung nới rộng hơn lịch thật để không chặn oan jitter và mốc vét:
#   sang 03:00-09:00 (mốc CI 03:47/04:47 · local 04:30/04:45, trễ 2h vẫn lọt)
#   toi  19:30-23:30 (mốc CI 20:47/21:47 · local 21:15/22:00)
KHUNG_GIO = {"sang": (3 * 60, 9 * 60), "toi": (19 * 60 + 30, 23 * 60 + 30)}

# ── HẠN CHÓT BẢN TIN TỚI TAY — khác KHUNG_GIO, đừng gộp ─────────────────────────────
# KHUNG_GIO trả lời *phiên này có được nhận ca không* (khung KHỞI ĐỘNG, cố ý rộng để lớp
# chạy bù vẫn làm được việc). HẠN_CHOT trả lời *bản tin phải tới tay chậm nhất lúc mấy
# giờ* — đó là cam kết với người đọc, không phải điều kiện kỹ thuật.
# Ca sáng 04:30: Huy chốt 31/08/2026, nguyên văn *"tin buổi sáng bắt buộc phải có lúc 4h30
# sáng"*. Quét mất 16-21 phút nên lớp cuối còn kịp hạn phải khởi động chậm nhất 04:05;
# lịch mốc local đã dời theo (xem LICH trong scripts/kich_ci.py và docs/LICH.md).
# Ca tối 22:00: hạn cũ đã có từ 26/07/2026, chép về đây làm một bản gốc.
HAN_CHOT = {"sang": 4 * 60 + 30, "toi": 22 * 60}
CONG_GIO_TAT = "--bo-cong-gio"  # đường thoát KHAI BẰNG LỜI, bắt buộc kèm lý do


# STATE_GIO_GIA: seam CHỈ dùng cho bộ test (tests/test-cong-khung-gio.py) — ghim giờ hiện
# tại dạng "HH:MM" để ca thử không phải chờ tới 1h sáng. Vận hành thật KHÔNG đặt biến này.
GIO_GIA_ENV = "STATE_GIO_GIA"


def gio_hien_tai():
    """Giờ dùng để soi khung. Seam test hỏng thì ném lỗi, KHÔNG lặng lẽ rơi về giờ thật."""
    gia = (os.environ.get(GIO_GIA_ENV) or "").strip()
    if not gia:
        return datetime.now()
    gio, phut = gia.split(":")
    return datetime.now().replace(hour=int(gio), minute=int(phut))


def ngoai_khung(slot: str, now=None) -> str:
    """Trả về lý do nếu giờ hiện tại NGOÀI khung của ô; chuỗi rỗng nếu hợp lệ.

    Lỗi đọc bảng khung phải fail về phía KÊU (chặn), không phải phía im.
    """
    now = now or gio_hien_tai()
    phut = now.hour * 60 + now.minute
    dau, cuoi = KHUNG_GIO[slot]  # KeyError = ô lạ -> ném ra, không nuốt
    if dau <= phut <= cuoi:
        return ""
    return (
        f"{now:%H:%M} nam NGOAI khung cua o \"{slot}\" "
        f"({dau // 60:02d}:{dau % 60:02d}-{cuoi // 60:02d}:{cuoi % 60:02d} gio VN)"
    )

# NHÃN in ra cho từng ô của từng pipeline. Chỉ ảnh hưởng chữ hiển thị, KHÔNG ảnh hưởng logic khoá.
# web-scan/event-scan mỗi ngày chỉ 1 phiên nên ô còn lại chính là ô CHẠY BÙ (máy ngủ, chạy trễ sang
# nửa ngày kia) — gọi đúng tên để đọc log không tưởng là pipeline có 2 phiên.
SLOT_LABELS = {
    "drive-import": {"sang": "buoi sang", "toi": "buoi toi"},
    "web-scan": {"toi": "phien toi", "sang": "phien toi CHAY BU (sang som)"},
    "event-scan": {"sang": "phien sang", "toi": "phien sang CHAY BU (chieu/toi)"},
}
# Ô "chuẩn" của pipeline — dùng để xếp thứ tự khi in bảng `show`.
PRIMARY_SLOT = {"web-scan": "toi", "event-scan": "sang"}
# Không có nhịp tim trong ngần này phút -> coi phiên đang chạy là đã chết, cho giành lại khoá.
# Đặt 30': phiên khoẻ ghi checkpoint dày hơn thế nhiều (sau baseline, sau agent, sau script).
LOCK_STALE_MIN = 30

# ── CỜ "PHIÊN NÀY ĐÃ NẠP" — cho bước kích notify của claude-web-scan.yml ─────────────
# Vì sao cần (sự cố thật tối 31/07/2026, Huy nhận HAI bản tin lúc 21:24 và 21:26): bước kích
# cũ hỏi `git log <base.sha>..HEAD` SAU KHI đã `git pull --rebase`, nên khoảng đó nuốt cả
# commit của PHIÊN KHÁC vừa push xen vào. Đo: run vét khởi động 14:11:17Z rồi SKIP (exit 10,
# không quét gì), phiên chính commit `Cap nhat ban tin 31/07` lúc 14:23:49Z, run vét pull về
# lúc 14:25:33Z ⇒ grep khớp commit của người ta ⇒ `gh workflow run notify-email.yml` lần THỨ
# HAI. Không lỗi, không cảnh báo — chỉ có Huy nhận thừa một bản tin rỗng tin mới.
# Phép đo thuần git KHÔNG phân biệt được, vì phiên SKIP cũng phải rebase để push nổi commit
# log của nó, tức commit của phiên kia đã nằm trong cây local từ trước bước kích.
# ⇒ Ý ĐỊNH PHẢI KHAI BẰNG LỜI: chỉ phiên nào TỰ TAY gọi `state.py done` mới ghi cờ này. Phiên
# SKIP không được gọi `done` (luật routine) nên vĩnh viễn không có cờ ⇒ không kích. Cùng bài
# học với `tu_dong=1`, `TELEGRAM_BAT_BUOC`, `DIEMTIN_PHIEN_TEST`.
CO_DIR_ENV = "DIEMTIN_CO_DIR"  # seam CHỈ dùng cho bộ test; vận hành thật không đặt
CO_TIEN_TO = "diemtin-da-nap-"


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def current_slot() -> str:
    return "sang" if datetime.now().hour < SLOT_SPLIT_HOUR else "toi"


def la_phien_test() -> bool:
    """Phiên TEST hạ tầng? Chỉ đọc biến môi trường — ý định phải khai bằng lời."""
    return (os.environ.get(TEST_ENV) or "").strip().lower() in TEST_ON


def state_path() -> Path:
    """Nơi GHI cờ. Phiên test đi sổ riêng nên không bao giờ chiếm được ô khoá thật."""
    return STATE_TEST_PATH if la_phien_test() else STATE_PATH


def load_path(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load() -> dict:
    return load_path(state_path())


def save(state: dict) -> None:
    p = state_path()
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def minutes_since(stamp: str):
    """Số phút kể từ mốc ISO; None nếu không đọc được."""
    try:
        return (datetime.now().astimezone() - datetime.fromisoformat(stamp)).total_seconds() / 60
    except (TypeError, ValueError):
        return None


def is_running(entry: dict) -> bool:
    """Đang có phiên chạy VÀ nhịp tim còn tươi. Nhịp cũ quá = phiên đã chết, khoá tự mở."""
    if entry.get("lastStatus") != "RUNNING":
        return False
    age = minutes_since(entry.get("heartbeat", ""))
    return age is not None and age < LOCK_STALE_MIN


def co_path(pipeline: str) -> Path:
    """Đường dẫn cờ 'phiên NÀY đã nạp'. Nằm ngoài repo (thư mục tạm) — chỉ sống trong một job."""
    thu_muc = Path(os.environ.get(CO_DIR_ENV) or tempfile.gettempdir())
    return thu_muc / f"{CO_TIEN_TO}{pipeline}"


def ghi_co_da_nap(pipeline: str) -> None:
    """Đánh dấu CHÍNH phiên này đã nạp xong pipeline đó. Hỏng thì KÊU, không nuốt."""
    try:
        co_path(pipeline).write_text(now_iso() + "\n", encoding="utf-8")
    except OSError as loi:
        print(f"⚠️ khong ghi duoc co da-nap cho {pipeline}: {loi}", file=sys.stderr)


def record(pipeline: str, status: str, note: str = "", slot: str = None) -> dict:
    """Ghi nhận 1 lần chạy. CHỈ status DONE mới đẩy lastSuccess của buổi (tức mới chặn fire sau).

    Mọi status kết thúc (DONE/SKIP/FAIL) đều NHẢ KHOÁ bằng cách xoá heartbeat.
    """
    slot = slot or current_slot()
    state = load()
    entry = state.get(pipeline, {})
    entry["lastRunAt"] = now_iso()
    entry["lastSlot"] = slot
    entry["lastStatus"] = status
    entry["note"] = note
    if status == "RUNNING":
        entry["heartbeat"] = now_iso()
    else:
        entry.pop("heartbeat", None)  # nhả khoá
    if status == "DONE":
        success = entry.get("lastSuccess") or {}
        success[slot] = today()
        entry["lastSuccess"] = success
        # Cờ cho bước kích notify — xem chú thích ở CO_DIR_ENV. Ghi cả ở phiên test: nhánh
        # test của workflow tự kích với `subject_tag` riêng và KHÔNG truyền `tu_dong`, nên nó
        # không để dấu vết lên sổ đã gửi; chặn cờ ở đây là làm nhánh test hết nghiệm thu được.
        ghi_co_da_nap(pipeline)
    state[pipeline] = entry
    save(state)
    return entry


def beat(pipeline: str) -> str:
    """Nhịp tim: gia hạn khoá. Trả về thông báo để in ra."""
    state = load()
    entry = state.get(pipeline, {})
    if entry.get("lastStatus") != "RUNNING":
        return f"{pipeline}: khong o trang thai RUNNING — bo qua nhip tim"
    entry["heartbeat"] = now_iso()
    state[pipeline] = entry
    save(state)
    return f"{pipeline}: nhip tim @ {entry['heartbeat']}"


def slot_label(pipeline: str, slot: str) -> str:
    """Tên ô để IN RA. Không dùng làm khoá — khoá vẫn là 'sang'/'toi'."""
    return SLOT_LABELS.get(pipeline, {}).get(slot, f"buoi {slot}")


def slots_ordered(pipeline: str) -> tuple:
    """Ô chuẩn của pipeline in trước, ô chạy bù in sau."""
    primary = PRIMARY_SLOT.get(pipeline)
    if primary is None:
        return SLOTS
    return (primary,) + tuple(s for s in SLOTS if s != primary)


def last_success(entry: dict, slot: str) -> str:
    return (entry.get("lastSuccess") or {}).get(slot)


def should_run(pipeline: str, slot: str = None) -> bool:
    slot = slot or current_slot()
    return last_success(load().get(pipeline, {}), slot) != today()


def main() -> None:
    args = sys.argv[1:]
    slot = None
    if "--slot" in args:
        i = args.index("--slot")
        slot = args[i + 1] if i + 1 < len(args) else ""
        if slot not in SLOTS:
            print(f"--slot phai la: {' | '.join(SLOTS)}", file=sys.stderr)
            sys.exit(2)
        del args[i : i + 2]
    force = "--force" in args
    if force:
        args.remove("--force")
    bo_cong_gio = ""
    if CONG_GIO_TAT in args:
        i = args.index(CONG_GIO_TAT)
        bo_cong_gio = args[i + 1] if i + 1 < len(args) else ""
        if not bo_cong_gio.strip():
            print(f"{CONG_GIO_TAT} phai kem LY DO (vd: {CONG_GIO_TAT} \"chay bu tay\")",
                  file=sys.stderr)
            sys.exit(2)
        del args[i : i + 2]
    as_json = "--json" in args
    if as_json:
        args.remove("--json")
    cmd = args[0] if args else "show"

    if la_phien_test():
        # In LOUD ở mọi lệnh: đọc log CI phải thấy ngay phiên này không đụng cờ thật.
        print(f"⚠️  PHIEN TEST ({TEST_ENV}=1) — ghi vao {state_path().name}, KHONG dung "
              f"cham co that ({STATE_PATH.name}).")

    if cmd == "show":
        state = load()
        now_slot = slot or current_slot()
        if as_json:
            # Dữ liệu THÔ, có cấu trúc — nơi khác (vd. bot điện thoại) tự dịch sang câu dễ đọc,
            # thay vì bóc tách lại chuỗi text kỹ thuật ở nhánh in dưới đây.
            out = {"today": today(), "nowSlot": now_slot, "pipelines": {}}
            for name, e in state.items():
                out["pipelines"][name] = {
                    "slots": {slot_label(name, s): last_success(e, s) for s in slots_ordered(name)},
                    "lastStatus": e.get("lastStatus"),
                    "lastRunAt": e.get("lastRunAt"),
                    "note": e.get("note") or "",
                    "doneToday": last_success(e, now_slot) == today(),
                    "running": is_running(e),
                }
            print(json.dumps(out, ensure_ascii=False))
            return
        if not state:
            print(f"(chua co {state_path().name})")
            return
        print(f"Hom nay {today()}, o hien tai: {now_slot}\n")
        for name, e in state.items():
            done = " · ".join(
                f"{slot_label(name, s)}={last_success(e, s) or '-'}" for s in slots_ordered(name)
            )
            flag = (
                ""
                if last_success(e, now_slot) == today()
                else f"  <- {slot_label(name, now_slot)} CHUA xong"
            )
            print(f"{name:<14} {done}  lastStatus={e.get('lastStatus','-')} lastRunAt={e.get('lastRunAt','-')}{flag}")
            if is_running(e):
                age = minutes_since(e.get("heartbeat", "")) or 0
                print(f"{'':<14} 🔒 DANG CHAY — nhip tim {age:.0f}' truoc (khoa het han sau {LOCK_STALE_MIN}')")
            elif e.get("lastStatus") == "RUNNING":
                print(f"{'':<14} ⚠️  danh dau RUNNING nhung nhip tim da cu -> coi nhu CHET, khoa da mo")
            if e.get("note"):
                print(f"{'':<14} note: {e['note']}")
        return

    if len(args) < 2 or args[1] not in PIPELINES:
        print(f"Pipeline phai la mot trong: {', '.join(PIPELINES)}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    pipeline = args[1]
    use_slot = slot or current_slot()

    if cmd in ("check", "claim"):
        entry = load().get(pipeline, {})
        # CỔNG KHUNG GIỜ đứng TRƯỚC mọi phép khác: sai giờ thì không được đụng vào ô nào,
        # kể cả để đọc. Phiên test bỏ qua (phải chạy lại được bất kể giờ nào).
        if pipeline in ("web-scan", "event-scan") and not la_phien_test():
            ly_do = ngoai_khung(use_slot)
            if ly_do and not bo_cong_gio:
                print(
                    f"SKIP — {ly_do}. Cron GitHub tre bat dinh 2-4h nen phien nay khong "
                    f"phai ca that; KHONG claim, KHONG quet. Moc dung gio se lam. "
                    f"Chay bu tay: them {CONG_GIO_TAT} \"<ly do>\"."
                )
                sys.exit(12)
            if ly_do and bo_cong_gio:
                print(f"⚠️  BO CONG GIO ({ly_do}) — ly do: {bo_cong_gio}")
        if la_phien_test():
            # (a) KHÔNG xét lastSuccess thật -> phiên test không bao giờ exit 10 vì bản tin thật
            #     đã xong. Test phải chạy lại được bất kể giờ nào, đó là công dụng của nó.
            # (b) NHƯNG vẫn đọc cờ THẬT để nhường phiên thật đang chạy: bỏ chốt này là mở đường
            #     cho test quét chồng lên bản tin thật (trước đây khoá chung nên không xảy ra).
            that = load_path(STATE_PATH).get(pipeline, {})
            if is_running(that) and not force:
                age = minutes_since(that.get("heartbeat", "")) or 0
                print(
                    f"SKIP — PHIEN TEST khong chay chong len PHIEN THAT dang chay "
                    f"(nhip tim {age:.0f}' truoc, bat dau {that.get('lastRunAt')})."
                )
                sys.exit(11)
        elif not should_run(pipeline, use_slot):
            print(
                f"SKIP — {pipeline} [{slot_label(pipeline, use_slot)}] ngay {today()} DA XONG "
                f"(lan chay cuoi {entry.get('lastRunAt')}). Khong lam lai."
            )
            sys.exit(10)
        if is_running(entry) and not force:
            age = minutes_since(entry.get("heartbeat", "")) or 0
            print(
                f"SKIP — {pipeline} DANG CO PHIEN KHAC CHAY (nhip tim {age:.0f}' truoc, bat dau "
                f"{entry.get('lastRunAt')}). Khong chay chong len. Neu chac chan phien do da chet: "
                f"them --force."
            )
            sys.exit(11)
        if cmd == "claim":
            record(pipeline, "RUNNING", "dang quet", use_slot)
            extra = " (da CUOP khoa bang --force)" if force and is_running(entry) else ""
            print(
                f"RUN — {pipeline} [{slot_label(pipeline, use_slot)}] ngay {today()} chua xong, "
                f"da giu khoa{extra}. Quet di."
            )
        else:
            print(
                f"RUN — {pipeline} [{slot_label(pipeline, use_slot)}] ngay {today()} chua xong "
                f"(check: KHONG giu khoa)."
            )
        sys.exit(0)

    if cmd == "beat":
        print(beat(pipeline))
        return

    if cmd in ("done", "skip", "fail"):
        note = args[2] if len(args) > 2 else ""
        e = record(pipeline, cmd.upper(), note, use_slot)
        print(
            f"{pipeline} [{slot_label(pipeline, use_slot)}]: {e['lastStatus']} @ {e['lastRunAt']}"
            + (f" — {note}" if note else "")
        )
        return

    print(f"Lenh khong hop le: {cmd}", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()

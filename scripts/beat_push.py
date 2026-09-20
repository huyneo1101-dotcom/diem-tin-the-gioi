#!/usr/bin/env python3
"""NHỊP TIM `logs/state.json` RỒI PUSH NGAY — gộp cứng thành MỘT lệnh, không rời ra được.

VÌ SAO CÓ FILE NÀY (sự cố thật 19/09/2026, xem `logs/scan-2026-09-19.log` dòng [21:45Z]):
CI tự nhịp tim (`state.py beat web-scan`) hai lần cục bộ (04:31, 04:41 giờ VN) nhưng
KHÔNG đẩy lên git — commit đẩy gần nhất chỉ dừng ở checkpoint baseline (04:04). Máy Mac
chạy mốc vét 04:36 chỉ đọc được nhịp tim 04:04 qua git, tính ra 32 phút > `LOCK_STALE_MIN`
(30'), kết luận CI đã chết rồi GIÀNH KHOÁ trong khi CI vẫn sống (đang chờ 5 agent song
song trả kết quả). Hai phiên quét chồng, phí ~12 triệu token quy đổi vét lại đúng việc CI
đang làm dở; may CI push xong trước (04:45) nên không mất tin, nhưng đúng kiểu lỗi "may
mắn mới không mất" mà mục 17 CLAUDE.md coi là chưa vá.

NGUYÊN NHÂN GỐC: `state.py beat` chỉ ghi *state cục bộ* trong container CI — PUSH lên
remote là bước RIÊNG mà prompt CI tự gọi bằng lệnh `git` trần ở một chỗ khác trong bài.
Hai việc tách rời cho phép gọi vế đầu (ghi nhịp tim) mà quên vế sau (đẩy lên, chỗ MÁY
KHÁC thật sự nhìn thấy). Bản vá này gộp cứng hai việc thành một lệnh — "beat mà quên
push" không còn là lỗi có thể mắc, đúng nguyên tắc mục 5 CLAUDE.md: chặn bằng CƠ CHẾ,
không chặn bằng nhắc cẩn thận hơn.

CƠ CHẾ MERGE — dùng CHUNG lối "đọc-sửa-ghi trên đỉnh remote, không rebase" với
`logs/da-gui-email.json` (`.github/scripts/ghi_so_push.py`) và log ngày
(`scripts/ghi_log_push.py`): `state.json` cũng là file NHIỀU PHIÊN cùng ghi (web-scan +
event-scan chạy trong cùng session CI, cộng phiên local chạy song song), nên
`git pull --rebase` có thể xung đột đúng kiểu đã vá cho hai file kia. Ở đây chỉ ghi ĐÈ
field `heartbeat` của MỘT pipeline, giữ nguyên mọi thứ khác của bản remote mới nhất —
an toàn để gọi lại bao nhiêu lần cũng được (idempotent), và tự động BỎ QUA (không push
gì) nếu pipeline đó đã DONE/SKIP/FAIL ở nơi khác trong lúc mình đang định beat — không
hồi sinh một khoá đã nhả.

CÁCH DÙNG (THAY HẲN `python3 scripts/state.py beat <pipeline>` bằng đúng lệnh này,
không dùng `state.py beat` trần nữa trong phiên CI/local):
    python3 scripts/beat_push.py web-scan
    python3 scripts/beat_push.py event-scan

Bộ test canh: `tests/test-beat-push.py` (có `--tu-kiem`).
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
for _p in (ROOT / ".github" / "scripts", ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import ghi_so_push as gsp  # noqa: E402  (phải chèn sys.path trước)
import state as st  # noqa: E402

STATE_REL = "logs/state.json"


def hop_nhat_heartbeat(pipeline: str):
    """Trả callback ghi ĐÈ đúng field `heartbeat` của `pipeline` lên bản remote mới nhất.

    Idempotent: gọi lại bao nhiêu vòng retry cũng ra cùng kết quả (heartbeat luôn nhận
    giờ hiện tại — ghi lại giá trị gần-như-giống không sao, ý nghĩa vẫn là "còn sống").
    """
    def _ghep(p: pathlib.Path) -> None:
        data = st.load_path(p) if p.exists() else {}
        entry = data.get(pipeline, {})
        if entry.get("lastStatus") != "RUNNING":
            # Pipeline đã DONE/SKIP/FAIL (ở phiên khác, hoặc chính mình) — khoá đã nhả,
            # đừng hồi sinh nhịp tim cho một phiên không còn giữ khoá.
            return
        entry["heartbeat"] = st.now_iso()
        data[pipeline] = entry
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return _ghep


def _remote_co_state_json() -> bool:
    """Fetch nhanh rồi hỏi remote hiện CÓ file `logs/state.json` hay chưa (bất kể nội dung).

    Vì sao cần bước riêng này: `day_len_remote` giả định `hop_nhat` LUÔN ghi ra file (mọi
    caller khác — sổ đã gửi, log ngày — là dữ liệu append-only, luôn có gì đó để thêm). Ở
    đây `hop_nhat_heartbeat` có thể là NO-OP thật (pipeline chưa từng claim lần nào) —
    lúc đó `logs/state.json` CHƯA TỪNG TỒN TẠI trên remote, và `git add` trên một đường dẫn
    không có trên đĩa lẫn trong index sẽ chết với `pathspec did not match any files`.

    CHỈ chặn đúng ca "file chưa từng tồn tại" — file ĐÃ có (dù pipeline đang DONE/SKIP/FAIL)
    vẫn phải đi tiếp vào `day_len_remote` như thường, để hàm `hop_nhat_heartbeat` bên trong
    là nơi DUY NHẤT quyết định có ghi đè hay không (tránh hai lớp kiểm tra rời nhau lệch ý
    nhau — bài học `tu_dong=1`/`DIEMTIN_PHIEN_TEST` trong docstring của `state.py`).
    """
    gsp._git("fetch", "-q", "origin", "main", kiem=True)
    return gsp._git("show", f"FETCH_HEAD:{STATE_REL}", kiem=False).returncode == 0


def beat_and_push(pipeline: str, vong: int = gsp.VONG_MAC_DINH, ngu=None) -> int:
    """Trả 0 = đã đẩy (hoặc không đổi gì vì pipeline chưa từng claim/đã kết thúc),
    1 = hết vòng chưa đẩy được."""
    gsp._git("config", "user.name", "claude-scan-ci")
    gsp._git("config", "user.email", "noreply@anthropic.com")
    if not _remote_co_state_json():
        print(f"{pipeline}: remote chua tung co logs/state.json — bo qua nhip tim (no-op)")
        return 0
    kw = {"vong": vong,
          "nhan": f"nhip tim {pipeline}",
          "hau_qua": "Nhip tim khong toi duoc remote se lam may khac tuong phien da chet "
                     "roi gianh khoa quet chong — xem tests/test-beat-push.py"}
    if ngu is not None:
        kw["ngu"] = ngu
    return gsp.day_len_remote(STATE_REL, hop_nhat_heartbeat(pipeline),
                              f"beat: {pipeline} {st.now_iso()}", **kw)


def main(argv=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1 or args[0] not in ("web-scan", "event-scan"):
        print("Dung: python3 scripts/beat_push.py <web-scan|event-scan>", file=sys.stderr)
        return 2
    ma = beat_and_push(args[0])
    if ma == 0:
        print(f"{args[0]}: da day nhip tim len remote")
    return ma


if __name__ == "__main__":
    sys.exit(main())

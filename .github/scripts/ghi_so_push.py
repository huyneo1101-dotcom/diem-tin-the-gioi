#!/usr/bin/env python3
"""GHI SỔ ĐÃ GỬI RỒI PUSH — chịu được HAI workflow ghi cùng lúc.

VÌ SAO CÓ FILE NÀY (sự cố thật sáng 30/07/2026):
`notify-morning.yml` ghi `logs/da-gui-email.json` lúc 21:28:01Z, `notify-email.yml` ghi
lúc 21:28:08Z — CÁCH NHAU 07 GIÂY, cùng một file. Khối lệnh cũ (chép y nhau ở hai
workflow) commit local rồi `git pull --rebase origin main`: rebase phải phát lại commit
của mình lên trên commit của workflow kia, mà hai bên sửa đúng cùng chỗ trong JSON nên
XUNG ĐỘT. Rebase hỏng để repo ở trạng thái rebase dở, nên **cả 5 vòng retry đều chết
tiếp** và chỉ còn `::warning::khong push duoc so da gui`.
Hậu quả đo được: bản tin sáng 30/07 ĐÃ tới tay lúc 04:28 mà sổ trống ⇒ (a) canary ca
`sang` kêu oan và nhắn Telegram cho Huy; (b) hai phiên CI dự phòng (05:00 · 05:37) kết
luận "mất bản tin" rồi chạy lại vòng quét bổ sung tốn token. Đây là hệ quả dây chuyền của
việc gộp `event-scan` vào cùng session sáng (28/07) — trước đó hai bên cách nhau ~4 tiếng
nên không ai thấy lỗi này.

CÁCH VÁ — ĐỪNG REBASE, SỔ LÀ DỮ LIỆU APPEND-ONLY:
hai lần gửi khác nhau là hai DÒNG khác nhau trong `lan_gui`, không phải hai phiên bản
tranh nhau của một dòng. Vì vậy cách hợp nhất đúng không phải giải xung đột văn bản mà là
**lấy sổ mới nhất của remote rồi ghi lại dòng của mình lên đó** (read-modify-write, thử
lại trên đỉnh mới nếu bị chen). Không bao giờ gọi `pull --rebase` ⇒ không bao giờ có
xung đột để mà hỏng.

Việc chia làm HAI PHA, và thứ tự đó là phần quan trọng nhất của bản vá:

  PHA 0 — TÍNH DÒNG, đúng MỘT LẦN, trên ngữ cảnh git NGUYÊN BẢN của phiên mình:
  chạy `so_da_gui.py --ghi` rồi giữ lại **dòng vừa được thêm**. Phải làm trước khi
  đụng tới git, vì `so_da_gui.py` chọn URL bằng `make_docx.pick_items` — hàm này diff
  `index.html` với `HEAD~1`. Tính sau khi đã `reset` sang đỉnh remote là diff với lô của
  PHIÊN KHÁC ⇒ sổ ghi thừa URL không phải của mình, mà **URL vào sổ nghĩa là bản tin sau
  BỎ tin đó** — mất tin, không phải trùng tin.

  PHA 1 — ĐẨY DÒNG ĐÓ LÊN, thử lại trên đỉnh mới nếu bị chen. Mỗi vòng bốn việc:
    1. `fetch` + `reset --mixed FETCH_HEAD` — HEAD về đỉnh remote, **giữ nguyên working
       tree** (`--mixed` chứ không `--hard`: `--hard` kéo cả `index.html` của lô khác về,
       và commit của mình khi đó không còn chỉ chứa file sổ).
    2. `checkout FETCH_HEAD -- logs/da-gui-email.json` — chỉ RIÊNG sổ lấy bản remote mới
       nhất. Đây là dòng giữ lại dòng của workflow kia; bỏ nó là ghi đè mất dòng đó.
    3. append dòng của PHA 0 vào sổ đó (bỏ qua nếu đã có sẵn — nên chạy lại bao nhiêu
       lần cũng KHÔNG nhân đôi dòng).
    4. commit CHỈ file sổ rồi `push HEAD:main`.
  Push bị từ chối = có kẻ chen vào giữa bước 1 và 4 → ngủ rồi vòng lại từ bước 1.

⚠️ PHA 1 KHÔNG cắt bản ghi quá `GIU_NGAY` — việc cắt là của `so_da_gui.ghi_lan_gui`, đã
làm ở PHA 0 và cũng đã làm ở lần ghi của workflow kia. Cùng lắm sổ giữ thêm vài dòng cũ
tới lần ghi kế, mà giữ dư URL cũ chỉ khiến bản tin sau bỏ qua tin cũ — hướng lệch an
toàn, đúng nguyên tắc "thà ghi dư còn hơn ghi thiếu" của chính `so_da_gui.py`. Đừng thêm
luật cắt thứ hai vào đây: hai bộ luật song song chắc chắn lệch.
⚠️ Hết vòng mà chưa push được thì **trả mã ≠ 0**, không trả 0 cho êm: sổ trống là thứ
làm canary kêu oan và làm phiên dự phòng quét lại. Bước workflow vẫn để
`continue-on-error: true` nên job không đỏ, nhưng `::error::` phải hiện ra để lần sau lần
được dấu vết.

Bộ test canh: `tests/test-ghi-so-push.py` (có `--tu-kiem` dựng bản hỏng).
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SO_REL = "logs/da-gui-email.json"
VONG_MAC_DINH = 5
NGU_GIAY = 3          # vòng i ngủ i * NGU_GIAY giây — giãn dần để hai workflow lệch nhịp


def _git(*a, kiem=False):
    """Chạy git trong ROOT. Trả CompletedProcess; `kiem=True` thì lỗi là ném."""
    r = subprocess.run(["git", "-C", str(ROOT), *a],
                       capture_output=True, text=True)
    if kiem and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)} rc={r.returncode}: "
                           f"{(r.stderr or r.stdout).strip()[:400]}")
    return r


def _ghi_so_bang_script(buoi, chi):
    """Gọi so_da_gui.py --ghi. Tách thành hàm để bộ test thay bằng bản giả."""
    cmd = [sys.executable, str(ROOT / ".github" / "scripts" / "so_da_gui.py"),
           "--ghi", "--buoi", buoi]
    for k in (chi or ()):
        cmd += ["--chi", k]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        raise RuntimeError(f"so_da_gui.py rc={r.returncode}: "
                           f"{(r.stderr or '').strip()[:400]}")


def _doc_lan_gui():
    p = ROOT / SO_REL
    if not p.exists():
        return []
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d.get("lan_gui") or [] if isinstance(d, dict) else []
    except (ValueError, OSError):
        return []


def _append_dong(dong):
    """Append `dong` vào sổ đang có trên đĩa. Đã có sẵn thì không thêm lại."""
    p = ROOT / SO_REL
    d = {"lan_gui": _doc_lan_gui()}
    if dong not in d["lan_gui"]:
        d["lan_gui"].append(dong)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def ghi_va_push(buoi, chi=None, nhan="", vong=VONG_MAC_DINH,
                ghi_so=None, ngu=time.sleep):
    """Ghi sổ rồi push, chịu được workflow khác ghi cùng lúc.

    Trả 0 = xong (đã push, hoặc sổ không đổi nên không cần push).
    Trả 1 = hết `vong` vòng vẫn chưa push được.
    """
    ghi_so = ghi_so or _ghi_so_bang_script
    _git("config", "user.name", "claude-scan-ci")
    _git("config", "user.email", "noreply@anthropic.com")
    tin_nhan = nhan or f"so: ghi lo tin da gui ({buoi})"

    # ── PHA 0: tính dòng ĐÚNG MỘT LẦN, trên ngữ cảnh git nguyên bản của phiên mình ──
    truoc = _doc_lan_gui()
    ghi_so(buoi, chi)
    them = [x for x in _doc_lan_gui() if x not in truoc]
    if not them:
        print("so khong doi — khong can commit")
        return 0
    dong = them[-1]
    print(f"lan gui nay: buoi {dong.get('buoi')}, {len(dong.get('urls') or [])} URL")

    # ── PHA 1: đẩy dòng đó lên, thử lại trên đỉnh mới nếu bị chen ──
    for i in range(1, vong + 1):
        # (1) HEAD về đỉnh remote, GIỮ working tree (xem docstring: vì sao không --hard)
        _git("fetch", "-q", "origin", "main", kiem=True)
        _git("reset", "-q", "--mixed", "FETCH_HEAD", kiem=True)
        # (2) riêng sổ lấy bản remote mới nhất — đây là chỗ giữ dòng của workflow kia
        if _git("checkout", "-q", "FETCH_HEAD", "--", SO_REL).returncode != 0:
            # sổ chưa từng có trên remote: bỏ bản trong working tree để khỏi nhân dòng
            (ROOT / SO_REL).unlink(missing_ok=True)
        # (3) append dòng của PHA 0 — idempotent, chạy lại không nhân đôi
        _append_dong(dong)
        # (4) commit CHỈ file sổ rồi push
        _git("add", SO_REL, kiem=True)
        if _git("diff", "--cached", "--quiet").returncode == 0:
            print("so khong doi — khong can commit")
            return 0
        _git("commit", "-q", "-m", tin_nhan, kiem=True)
        if _git("push", "-q", "origin", "HEAD:main").returncode == 0:
            print(f"da push so da gui (vong {i}/{vong})")
            return 0
        print(f"push lan {i} bi tu choi (co workflow khac vua push) — "
              f"lay so moi nhat roi ghi lai")
        if i < vong:
            ngu(i * NGU_GIAY)

    print(f"::error::khong push duoc so da gui sau {vong} vong. So TRONG se lam canary "
          f"keu oan va lam phien du phong quet lai — xem tests/test-ghi-so-push.py")
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--buoi", required=True, help="sang | toi | sukien")
    ap.add_argument("--chi", metavar="KIND", action="append",
                    help="chuyển thẳng cho so_da_gui.py (lặp được)")
    ap.add_argument("--nhan", default="", help="commit message")
    ap.add_argument("--vong", type=int, default=VONG_MAC_DINH)
    a = ap.parse_args(argv)
    return ghi_va_push(a.buoi, a.chi, a.nhan, a.vong)


if __name__ == "__main__":
    sys.exit(main())

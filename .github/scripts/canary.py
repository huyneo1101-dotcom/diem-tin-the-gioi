#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CANARY — báo khi bản tin KHÔNG tới nơi, tức là báo cái IM LẶNG.

    python3 .github/scripts/canary.py --ca toi      # sau lớp vét tối
    python3 .github/scripts/canary.py --ca sang     # sau lớp cuối sáng sớm
    python3 .github/scripts/canary.py --ca sukien   # sau lớp cuối event-scan
    DRY_RUN=1 python3 .github/scripts/canary.py --ca toi   # in ra màn hình, không gửi

VÌ SAO CẦN (chỉ thị Huy 27/07/2026): mọi cảnh báo hiện có đều do CHÍNH routine phát ra —
workflow đỏ, job fail, tin nhắn lỗi. Tất cả đòi routine phải CHẠY mới báo được. Nhưng kiểu
hỏng nguy hiểm nhất không phải "chạy rồi lỗi", mà là **không chạy phát nào**:
  · máy Mac đóng nắp, caffeinate không giữ nổi -> lớp local không nổ;
  · GitHub bỏ cron lúc tải cao (đã xảy ra sáng 27/07, chính vì thế mới dời 04:30 -> 04:00);
  · token/quota hết -> phiên quét chết trước khi push -> `notify-email.yml` kích theo PUSH
    nên KHÔNG có push là KHÔNG có gì hết.
Cả ba đều im lặng tuyệt đối: 22h không thấy bản tin, Huy không phân biệt được "hôm nay không
có tin đáng" với "cả hệ thống chết từ chiều". Canary là con chim trong mỏ than — nó chỉ kêu
khi không khí đã hỏng.

HAI NGUYÊN TẮC LÀM NÓ CÓ GIÁ TRỊ — đừng "dọn cho gọn" mất:
 1. **KIỂM ĐẦU RA, KHÔNG KIỂM QUY TRÌNH.** Không hỏi "job có chạy không" (job xanh mà gửi rỗng
    vẫn là hỏng), mà hỏi "bản tin có tới tay không". Bằng chứng là `logs/da-gui-email.json` —
    sổ này chỉ được ghi ở BƯỚC CUỐI sau khi đã gửi xong mọi kênh, nên nó là dấu vết của việc
    đã-gửi-thật, không phải lời tự khai của một job.
 2. **NGƯỜI BÁO PHẢI KHÁC NGƯỜI LÀM.** Canary chạy ở workflow riêng, cron riêng, không import
    và không đụng gì tới đường quét. Nếu nó chết cùng lúc với routine thì nó vô nghĩa.

CHẠY SAU LỚP VÉT, KHÔNG PHẢI SAU HẠN CHÓT. Hạn chót email tối là 22:00, nhưng lớp vét CI 22:00
gửi tới ~22:22 — đó là thiết kế bình thường, không phải sự cố. Canary đặt 22:45 để không kêu
oan trong lúc lớp vét đang làm đúng việc của nó. Đổi lại, cảnh báo tới trễ hơn hạn ~45 phút:
đây là đánh đổi CÓ CHỦ Ý (thà báo muộn mà đúng, còn hơn báo sớm mà nhiễu — cảnh báo kêu oan
vài lần là Huy thôi đọc, lúc đó canary chết thật).

BA CA CHẨN ĐOÁN — canary phải nói được HỎNG Ở KHÂU NÀO, không chỉ "có gì đó sai":
 · sổ CÓ dòng của ca hôm nay          -> im lặng, không nhắn gì (ngày bình thường)
 · sổ TRỐNG mà `state.json` báo DONE  -> phiên quét xong nhưng bản tin không đi: hỏng ở khâu
                                         GỬI (notify-email.yml), hoặc phiên quét 0 tin nên
                                         không có commit nào để kích nó
 · sổ TRỐNG và state KHÔNG done       -> hỏng ở khâu QUÉT: in luôn lastRunAt/lastStatus/note
                                         để biết chết ở đâu mà không phải mở Actions

GIỚI HẠN ĐÃ BIẾT, ghi ra để sau này khỏi tưởng là bug:
 · Gửi TAY (`workflow_dispatch`) KHÔNG ghi sổ (cố ý — xem notify-email.yml). Nên hôm nào phải
   gửi bù bằng tay thì canary vẫn kêu. Đúng hơn là sai: nó nhắc rằng ca tự động đã hỏng.
 · Bước ghi sổ có `continue-on-error` + retry push 5 lần. Push hỏng cả 5 lần thì bản tin đã
   tới tay mà sổ không có dòng nào -> canary kêu oan. Ca này hiếm và đã có `::warning::` riêng.
 · Ca `sukien` KHÔNG kiểm sổ mà kiểm `state.json`, vì `notify-morning.yml` cố ý không gửi khi
   không có sự kiện/tập trận/think-tank mới — "im lặng" ở đó là hành vi ĐÚNG, không phải hỏng.
   Thứ đáng kiểm là phiên event-scan có chạy xong hay không.
"""
import argparse
import datetime
import json
import os
import pathlib
import sys
import zoneinfo

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SO = ROOT / "logs" / "da-gui-email.json"
STATE = ROOT / "logs" / "state.json"
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

# Đi bằng curl chứ không urllib — máy Huy có thiết bị chèn cert nên urllib trượt
# CERTIFICATE_VERIFY_FAILED. Chi tiết trong scripts/tg_api.py.
sys.path.insert(0, str(ROOT / "scripts"))
from tg_api import call, kiem_cau_hinh  # noqa: E402

# Ca -> (nhãn người đọc, pipeline trong state.json, ô sang/toi của pipeline đó)
CA = {
    "toi":    ("bản tin TỐI",       "web-scan",   "toi"),
    "sang":   ("bản tin SÁNG SỚM",  "web-scan",   "sang"),
    "sukien": ("Sự kiện & Tập trận", "event-scan", "sang"),
}


def hom_nay() -> str:
    return datetime.datetime.now(VN).strftime("%Y-%m-%d")


def doc_json(p: pathlib.Path):
    """Đọc file JSON, hỏng/thiếu thì trả None — canary không được chết vì file rác."""
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError) as e:
        print(f"[canary] {p.name} hỏng ({e}) — coi như không có", file=sys.stderr)
        return None


def da_gui(buoi: str, ngay: str) -> dict | None:
    """Lần gửi của ca `buoi` trong ngày `ngay`, hoặc None nếu chưa có.

    So sánh trên phần NGÀY của `luc` (đã là ISO giờ VN do so_da_gui.py ghi), không parse
    datetime — nhanh và không vỡ khi bản ghi thiếu trường.
    """
    so = doc_json(SO)
    if not so or not isinstance(so.get("lan_gui"), list):
        return None
    for lan in so["lan_gui"]:
        if lan.get("buoi") == buoi and str(lan.get("luc", "")).startswith(ngay):
            return lan
    return None


def trang_thai_quet(pipeline: str, o: str, ngay: str) -> tuple[bool, str]:
    """(phiên quét đã DONE cho ô này hôm nay chưa, mô tả để đưa vào tin nhắn)."""
    st = doc_json(STATE)
    if not st or pipeline not in st:
        return False, "không đọc được logs/state.json"
    p = st[pipeline]
    xong = (p.get("lastSuccess") or {}).get(o) == ngay
    mota = (f"lastRun {p.get('lastRunAt', '?')} · {p.get('lastStatus', '?')}"
            f" · {(p.get('note') or '')[:160]}")
    return xong, mota


def gui(text: str) -> int:
    """Gửi cảnh báo tới mọi chat trong danh sách trắng. 0 = xong, 1 = gửi hỏng."""
    if os.environ.get("DRY_RUN") == "1":
        print("--- DRY_RUN, không gửi ---")
        print(text)
        return 0
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chats = [c.strip() for c in os.environ.get("TELEGRAM_CHAT_ID", "").split(",") if c.strip()]
    # Thiếu secret ở ĐÂY là ca tệ nhất trong cả repo: canary chỉ chạy tới dòng này khi bản tin
    # ĐÃ hụt, nên "thoát êm" nghĩa là nuốt luôn tiếng kêu cuối cùng — hỏng chồng hỏng, tuyệt
    # đối im lặng. Vì thế nó đi chung một cổng với send_telegram: mất secret là ĐỎ.
    rc = kiem_cau_hinh(token, chats, "canary")
    if rc is not None:
        # Kênh tắt có chủ ý (rc=0) thì vẫn phải để lại dấu vết: bản tin đang hụt thật.
        if rc == 0:
            print(f"::warning::canary có cảnh báo nhưng kênh Telegram đang tắt:\n{text}")
        return rc
    loi = 0
    for chat in chats:
        r = call(token, "sendMessage",
                 {"chat_id": chat, "text": text, "disable_web_page_preview": True})
        if r.get("ok"):
            print(f"[canary] đã báo tới chat …{chat[-4:]}")
        else:
            # In mô tả lỗi nhưng KHÔNG in token/chat đầy đủ — log Actions của repo public.
            print(f"[canary] gửi tới …{chat[-4:]} HỎNG: {r.get('description')}", file=sys.stderr)
            loi = 1
    return loi


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ca", required=True, choices=list(CA))
    args = ap.parse_args()

    nhan, pipeline, o = CA[args.ca]
    ngay = hom_nay()
    ngay_vn = datetime.datetime.now(VN).strftime("%d/%m")
    gio_vn = datetime.datetime.now(VN).strftime("%H:%M")

    # --- Ca sukien: kiểm PHIÊN QUÉT, không kiểm sổ gửi (xem docstring) ---
    if args.ca == "sukien":
        xong, mota = trang_thai_quet(pipeline, o, ngay)
        if xong:
            print(f"[canary] {nhan} {ngay}: phiên event-scan DONE — im lặng.")
            return 0
        text = (f"⚠️ {gio_vn} {ngay_vn} — phiên SỰ KIỆN & TẬP TRẬN chưa chạy xong.\n\n"
                f"Cả 4 mốc (CI 08:45 · local 09:15 · CI 09:45 · local 10:15) đều không "
                f"hoàn tất.\n{mota}\n\n"
                f"Chạy tay: gh workflow run claude-event-scan.yml")
        print(f"::warning::canary {args.ca}: {mota}")
        return gui(text)

    # --- Ca sang/toi: bằng chứng là SỔ ĐÃ GỬI ---
    lan = da_gui(o, ngay)
    if lan:
        print(f"[canary] {nhan} {ngay}: đã gửi lúc {lan.get('luc')} "
              f"({len(lan.get('urls') or [])} tin) — im lặng.")
        return 0

    xong, mota = trang_thai_quet(pipeline, o, ngay)
    if xong:
        khau = ("Phiên quét XONG nhưng bản tin không đi — hỏng ở khâu GỬI "
                "(notify-email.yml), hoặc phiên quét 0 tin nên không có commit nào kích nó.")
    else:
        khau = "Phiên quét CHƯA xong — hỏng ở khâu QUÉT."

    moc = ("CI 21:00 · local 21:15 · vét CI 22:00" if args.ca == "toi"
           else "CI 04:00 · local 04:30 · CI 05:00 · local 05:30")
    text = (f"⚠️ {gio_vn} {ngay_vn} — CHƯA có {nhan}.\n\n"
            f"{khau}\nMọi mốc đã qua: {moc}\n\n"
            f"{mota}\n\n"
            f"Chạy tay: gh workflow run claude-web-scan.yml")
    print(f"::warning::canary {args.ca}: {khau} | {mota}")
    return gui(text)


if __name__ == "__main__":
    sys.exit(main())

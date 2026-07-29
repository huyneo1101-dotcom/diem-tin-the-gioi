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
 · Gửi TAY (bấm nút, không kèm `tu_dong=1`) KHÔNG ghi sổ (cố ý — xem notify-email.yml). Nên hôm
   nào phải gửi bù bằng tay thì canary vẫn kêu. Đúng hơn là sai: nó nhắc rằng ca tự động đã hỏng.
   Phiên quét CI kích notify thì CÓ ghi sổ (nó truyền `-f tu_dong=1`) — trước 28/07/2026 điều
   kiện chỉ là `event_name == 'push'` nên mọi bản tin do CI ra đều lọt sổ và canary kêu oan.
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


def ngay_cua_ca(ca: str, luc: datetime.datetime) -> str:
    """Ngày mà một lần chạy/lần gửi THUỘC VỀ — không phải ngày trên đồng hồ.

    VẤP THẬT 28/07/2026: canary ca `toi` đặt cron 22:45 VN nhưng GitHub chạy lúc **00:23**
    (trễ 1h38 — hồ sơ repo vốn đã ghi cron trễ 5–20', hôm đó ăn hết biên 1h15 từ 22:45 tới
    nửa đêm). Qua nửa đêm thì `hom_nay()` nhảy sang ngày mới, nên canary đi hỏi "bản tin tối
    NGÀY MAI đâu" — bản đó còn 21 tiếng nữa mới tới, tất nhiên chưa có. Nó nhắn báo động
    trong khi bản tin tối 27/07 đã gửi lúc 21:37 và nằm trong sổ đàng hoàng. Tin nhắn tự mâu
    thuẫn ngay trên mặt chữ: tiêu đề "CHƯA có" mà dòng dưới in `lastRun … DONE`.

    Quy ước: **ca `toi` fire 21:00–22:30, nên mốc trước 12:00 thuộc về NGÀY HÔM TRƯỚC.**
    Ca `sang` và `sukien` cùng theo phiên sáng sớm (fire 04:00–05:30; từ 28/07/2026 event-scan
    chạy gộp trong chính phiên đó nên hai ca soi cùng một dải giờ) — cách nửa đêm hơn 13 tiếng
    nên không cần quy đổi; trễ tới mức đó thì hệ thống đã hỏng theo kiểu khác rồi.

    Dời cron sớm hơn KHÔNG chữa được gốc: độ trễ cron GitHub là thứ không ép được, chỉ mua
    thêm biên. Phải sửa cách tính ngày.
    """
    if ca == "toi" and luc.hour < 12:
        return (luc - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    return luc.strftime("%Y-%m-%d")


def ngay_ca_tu_iso(ca: str, luc: str) -> str:
    """`ngay_cua_ca` cho một mốc ISO đọc từ sổ. Hỏng/thiếu giờ thì lùi về so ngày thô."""
    try:
        return ngay_cua_ca(ca, datetime.datetime.fromisoformat(luc))
    except (TypeError, ValueError):
        return luc[:10]


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

    So bằng NGÀY CỦA CA (`ngay_ca_tu_iso`) chứ không phải ngày trên đồng hồ của `luc` — nhờ
    vậy một bản tin tối trôi qua nửa đêm (gửi 00:30 ngày 28) vẫn được tính cho ca tối ngày
    27, đúng như canary đang hỏi. Hai bên dùng CHUNG một hàm quy đổi; đừng để mỗi bên tự
    tính, lệch nhau là canary kêu oan mà không ai hiểu vì sao.
    """
    so = doc_json(SO)
    if not so or not isinstance(so.get("lan_gui"), list):
        return None
    for lan in so["lan_gui"]:
        if lan.get("buoi") == buoi and ngay_ca_tu_iso(buoi, str(lan.get("luc", ""))) == ngay:
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
    """Gửi cảnh báo — CHỈ tới chat của Huy. 0 = xong, 1 = gửi hỏng.

    ⚠️ TRƯỚC 28/07/2026 GỬI TỚI MỌI CHAT TRONG DANH SÁCH TRẮNG — sai đối tượng. Nội dung
    cảnh báo là *"hỏng ở khâu QUÉT · lastRun … · Chạy tay: gh workflow run claude-web-scan.yml"*:
    người đọc bản tin không làm gì được với nó, không kiểm chứng được, và cũng không xoá đi
    được. Với họ đó thuần tuý là rác — mà rác gửi cho người khác thì chính Huy cũng không dọn
    hộ được, vì bot chỉ xoá được tin trong 48h và Huy không có mặt trong đoạn chat đó.
    Cảnh báo hạ tầng là việc của người vận hành. Bản tin hụt thì người đọc tự thấy bằng việc
    không có bản tin — không cần thông báo kỹ thuật.
    """
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
    # Chỉ chat CHỦ. Quy ước giống telegram_bot.py: phần tử ĐẦU trong TELEGRAM_CHAT_ID, ghi đè
    # bằng TELEGRAM_OWNER_CHAT. Kiểm cấu hình vẫn soi cả danh sách (ở trên) để mất secret là đỏ.
    chu = os.environ.get("TELEGRAM_OWNER_CHAT", "").strip() or chats[0]
    loi = 0
    for chat in [chu]:
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
    bay_gio = datetime.datetime.now(VN)
    # NGÀY CỦA CA, không phải ngày đồng hồ — xem `ngay_cua_ca`. Tin nhắn cũng hiện ngày này
    # chứ không hiện ngày hôm nay: canary chạy 00:23 mà báo "28/07 chưa có bản tin tối" thì
    # đọc vào tưởng đang nói về tối nay, trong khi nó đang nói về tối HÔM QUA.
    ngay = ngay_cua_ca(args.ca, bay_gio)
    ngay_vn = datetime.datetime.strptime(ngay, "%Y-%m-%d").strftime("%d/%m")
    gio_vn = bay_gio.strftime("%H:%M")

    # --- Ca sukien: kiểm PHIÊN QUÉT, không kiểm sổ gửi (xem docstring) ---
    if args.ca == "sukien":
        xong, mota = trang_thai_quet(pipeline, o, ngay)
        if xong:
            print(f"[canary] {nhan} {ngay}: phiên event-scan DONE — im lặng.")
            return 0
        text = (f"⚠️ {gio_vn} {ngay_vn} — phiên SỰ KIỆN & TẬP TRẬN chưa chạy xong.\n\n"
                f"Pipeline này gộp vào phiên sáng sớm từ 28/07/2026 — cả 4 mốc của phiên đó "
                f"(CI 04:00 · local 04:30 · CI 05:00 · local 05:30) đều không hoàn tất.\n"
                f"{mota}\n\n"
                f"Chạy tay: gh workflow run claude-web-scan.yml")
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

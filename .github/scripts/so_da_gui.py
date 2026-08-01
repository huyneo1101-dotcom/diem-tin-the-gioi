#!/usr/bin/env python3
"""SỔ ĐÃ GỬI — chống bản tin TỐI gửi lại tin đã có trong bản tin SÁNG.

VÌ SAO (chỉ thị Huy 27/07/2026: *"gộp tất cả những tin đã tiếp tục quét được tính từ sau
email phiên buổi sáng"* → *"loại cả những tin đã quét lúc 4h 5h sáng"*):
`notify-email.yml` chạy theo PUSH chứ không theo cron — cứ có commit "Cap nhat ban tin" là
gửi. Phiên sáng (04:00/05:00) push -> gửi email "BUỔI SÁNG"; phiên tối (21:00) push -> gửi
email "BUỔI TỐI". Nhưng CẢ BA kênh đều chọn tin bằng luật "cùng ngày"
(`_addedDate == generatedAt`): send-email.js, make_docx.py, và send_telegram.py (dùng chung
make_docx). Nên bản tối liệt kê lại nguyên si tin đã gửi lúc sáng.

VÌ SAO KHÔNG DÙNG MỐC GIỜ (kiểu "tối chỉ lấy tin nạp sau 12:00"): `_addedDate` chỉ có độ
phân giải NGÀY, và mốc giờ vỡ ngay khi bản tin gửi trễ qua nửa đêm, khi phải gửi lại tay,
hoặc khi một mốc dự phòng chạy bù. Sổ URL thì đúng trong mọi trường hợp đó: đã gửi rồi là
không gửi lại, bất kể lúc nào.

Dùng:
    python3 .github/scripts/so_da_gui.py --ghi --buoi toi   # sau khi đã gửi xong MỌI kênh
    python3 .github/scripts/so_da_gui.py --xem              # xem sổ hiện tại
"""
import argparse
import datetime
import json
import pathlib
import sys
import zoneinfo

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SO = ROOT / "logs" / "da-gui-email.json"
VN = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")

# Giữ bao nhiêu ngày trong sổ. 7 là dư: tin cũ hơn thế thì luật "cùng ngày" đã tự loại rồi,
# giữ thêm chỉ làm file phình. Nhưng đừng hạ xuống 1 — lô tin neo ngày cũ (xem "HAI BẪY khi
# lô tin trải QUÁ 2 NGÀY" trong CLAUDE.md) có `_addedDate` lệch `generatedAt` tới 2 ngày.
GIU_NGAY = 7


def doc_so() -> dict:
    if not SO.exists():
        return {"lan_gui": []}
    try:
        d = json.loads(SO.read_text(encoding="utf-8"))
        if isinstance(d, dict) and isinstance(d.get("lan_gui"), list):
            return d
    except (ValueError, OSError) as e:
        print(f"[so] {SO.name} hỏng ({e}) — coi như sổ rỗng", file=sys.stderr)
    return {"lan_gui": []}


def url_da_gui() -> set:
    """Tập URL đã nằm trong BẤT KỲ lần gửi nào còn trong sổ."""
    out = set()
    for lan in doc_so()["lan_gui"]:
        out.update(u for u in (lan.get("urls") or []) if u)
    return out


def url_da_gui_buoi(buoi: str, ngay: str) -> set:
    """Tập URL đã gửi ở ĐÚNG một buổi, trong ĐÚNG một ngày VN (`ngay` dạng YYYY-MM-DD).

    Khác `url_da_gui()` (gộp cả sổ, dùng cho kênh THÔNG BÁO — lặp lại tin cũ là thừa).
    Hàm này hẹp hơn vì `.docx` bản tối chỉ được loại tin của **ca SÁNG cùng ngày**:
      • dòng `toi` KHÔNG được dùng để lọc — nếu không, bản dựng lại trong ngày (`-bo-sung`,
        gửi bù bằng tay) sẽ ra file rỗng vì lô của chính nó đã nằm trong sổ;
      • tin quét TAY giữa ngày vốn không ghi sổ (chỉ ca chính thức mới ghi) nên tự nhiên
        không bị đụng — đúng chỉ thị Huy 27/07: *"quét tay xong có gửi email thì email tối
        vẫn phải có các tin đó"*.

    Bản tin trôi qua nửa đêm thì `ngay` là ngày mới, không khớp dòng `sang` hôm trước ⇒ không
    lọc gì. Cố ý để hướng lệch là LẶP một bản tin chứ không phải MẤT tin.
    """
    out = set()
    for lan in doc_so()["lan_gui"]:
        if lan.get("buoi") != buoi:
            continue
        try:
            luc = datetime.datetime.fromisoformat(lan["luc"])
        except (ValueError, KeyError, TypeError):
            continue          # bản ghi hỏng thì bỏ qua, đừng để nó lọc oan
        if luc.astimezone(VN).strftime("%Y-%m-%d") != ngay:
            continue
        out.update(u for u in (lan.get("urls") or []) if u)
    return out


def ghi_lan_gui(urls, buoi: str) -> int:
    urls = sorted({u for u in urls if u})
    d = doc_so()
    now = datetime.datetime.now(VN)
    d["lan_gui"].append({
        "luc": now.isoformat(timespec="seconds"),
        "buoi": buoi,
        "urls": urls,
    })
    # cắt bản ghi cũ
    han = now - datetime.timedelta(days=GIU_NGAY)
    giu = []
    for lan in d["lan_gui"]:
        try:
            if datetime.datetime.fromisoformat(lan["luc"]) >= han:
                giu.append(lan)
        except (ValueError, KeyError):
            pass          # bản ghi hỏng thì bỏ luôn, đừng để nó chặn việc cắt
    d["lan_gui"] = giu
    SO.parent.mkdir(parents=True, exist_ok=True)
    SO.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(urls)


KIND_MAC_DINH = ("usNews", "worldNews", "events")


def _tin_cua_ban_tin_nay(kinds=KIND_MAC_DINH):
    """URL của mọi tin mà các kênh CÓ THỂ đã gửi lần này.

    Lấy HỢP của `pick_items` (luật của .docx + Telegram) và `today_items` (luật của
    send-email.js) — cố tình rộng hơn từng luật riêng. Thà ghi dư một URL (lần sau bỏ qua)
    còn hơn ghi thiếu rồi gửi lại tin cũ, đúng thứ Huy vừa bắt lỗi.

    ⚠️ `kinds` phải khớp ĐÚNG thứ vừa gửi. Email sáng "Sự kiện & Tập trận"
    (`notify-morning.yml`) chỉ gửi `events` — ghi cả `usNews`/`worldNews` vào sổ ở đó sẽ
    XOÁ SỔ tin thường trước khi chúng kịp lên bản tin tối. Đó là mất tin, không phải trùng tin.
    """
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import make_docx as M          # cần python-docx; bước này chỉ chạy trên CI (đã cài)

    cur = M.extract_data((ROOT / "index.html").read_text(encoding="utf-8"))
    try:
        prev = M.prev_data()
    except Exception:                       # noqa: BLE001 - không có commit cha là chuyện thường
        prev = None
    urls = set()
    for kind in kinds:
        for it in M.pick_items(cur, prev, kind) + M.today_items(cur, kind):
            if it.get("sourceUrl"):
                urls.add(it["sourceUrl"])
    return urls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ghi", action="store_true", help="ghi lần gửi vừa rồi vào sổ")
    ap.add_argument("--buoi", default="?", help="sang | toi | sukien")
    ap.add_argument("--chi", metavar="KIND", action="append",
                    choices=list(KIND_MAC_DINH),
                    help="chỉ ghi loại này (lặp được). Mặc định: cả 3. "
                         "Email sự kiện buổi sáng phải dùng `--chi events`.")
    ap.add_argument("--xem", action="store_true", help="in sổ hiện tại")
    args = ap.parse_args()

    if args.xem:
        d = doc_so()
        for lan in d["lan_gui"]:
            print(f"{lan.get('luc')}  [{lan.get('buoi')}]  {len(lan.get('urls') or [])} tin")
        print(f"TỔNG {len(url_da_gui())} URL đã gửi trong {GIU_NGAY} ngày gần nhất")
        return

    if args.ghi:
        kinds = tuple(args.chi) if args.chi else KIND_MAC_DINH
        n = ghi_lan_gui(_tin_cua_ban_tin_nay(kinds), args.buoi)
        print(f"Đã ghi {n} URL vào {SO.relative_to(ROOT)} "
              f"(buổi {args.buoi}, loại: {', '.join(kinds)})")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
